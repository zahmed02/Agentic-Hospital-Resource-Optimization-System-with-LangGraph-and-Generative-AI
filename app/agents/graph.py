"""
LangGraph agent with:
  - Real multi-turn memory (LangGraph MemorySaver checkpointer, keyed by session_id)
  - Exact + semantic response caching (Redis + FAISS)
  - A dedicated Executive Operational Summary pipeline (SQL -> optimization
    -> RAG -> writer), separate from ad-hoc chat queries.

CHANGE from the previous version:
  - run_agent() now takes a session_id and threads it through to the
    checkpointer, so "she"/"he" follow-up references actually work.
  - Added generate_executive_summary(), which forces the agent through the
    SQL, optimization, and RAG tools before writing the memo, instead of
    relying on the model to decide to call them.
"""

import tiktoken
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import settings
from app.agents.tools import (
    sql_query_tool,
    rag_retrieval_tool,
    calculate_tool,
    get_patient_details,
    optimize_bed_allocation,
)
from app.agents.prompts import SYSTEM_PROMPT, EXEC_SUMMARY_FORMAT
from app.core.cache import get_cached_response, set_cache

# ---------- Token counting (for reference / manual trimming if ever needed) ----------
encoding = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Count tokens in a string."""
    return len(encoding.encode(text))


def trim_messages(messages: List[Dict[str, Any]], max_tokens: int = 10000) -> List[Dict[str, Any]]:
    """
    Trim messages to stay under max_tokens.
    Kept as a utility for callers that manage their own message lists outside
    the checkpointer (the checkpointer handles trimming-by-recency itself via
    recursion_limit + per-thread history, but this remains useful for any
    manual/one-off message list you build).
    """
    if not messages:
        return messages

    system_msg = None
    non_system = []
    for msg in messages:
        if msg.get("role") == "system":
            system_msg = msg
        else:
            non_system.append(msg)

    trimmed = non_system[-6:] if len(non_system) > 6 else non_system
    if system_msg:
        trimmed = [system_msg] + trimmed

    total_tokens = sum(count_tokens(str(msg)) for msg in trimmed)
    if total_tokens > max_tokens:
        for msg in trimmed:
            if msg.get("role") == "tool" and "content" in msg:
                content = msg["content"]
                if len(content) > 500:
                    msg["content"] = content[:500] + "... (truncated)"
        while len(trimmed) > 1:
            total_tokens = sum(count_tokens(str(msg)) for msg in trimmed)
            if total_tokens <= max_tokens:
                break
            for i in range(1, len(trimmed)):
                if trimmed[i].get("role") != "system":
                    trimmed.pop(i)
                    break
    return trimmed


# ---------- Agent setup ----------
llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    temperature=0.1,
    max_tokens=700,
)

tools = [
    sql_query_tool,
    rag_retrieval_tool,
    calculate_tool,
    get_patient_details,
    optimize_bed_allocation,
]

# One in-process checkpointer for the whole app. Each conversation's history
# is keyed by thread_id (== our session_id). NOTE: in-memory only, so history
# resets on process restart — for production, swap MemorySaver() for a
# persistent checkpointer (e.g. langgraph-checkpoint-postgres / -redis).
_checkpointer = MemorySaver()
agent_executor = create_react_agent(llm, tools, checkpointer=_checkpointer)


def run_agent(query: str, session_id: str = "default") -> str:
    """
    Execute the agent for one turn of a conversation.

      - Exact/semantic cache is keyed per-session so cache hits don't leak
        answers meant for a different patient context across sessions.
      - Conversation memory is handled by the LangGraph checkpointer via
        thread_id = session_id, so follow-ups like "what about her labs?"
        resolve correctly within the same session.
    """
    cache_key = f"{session_id}:{query}"
    cached_response, from_semantic = get_cached_response(cache_key)
    if cached_response:
        print(f"Cache hit (semantic={from_semantic}) for: {query[:50]}...")
        return cached_response

    result = agent_executor.invoke(
        {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ]
        },
        config={
            "configurable": {"thread_id": session_id},
            "recursion_limit": 10,
        },
    )
    messages = result["messages"]
    response = messages[-1].content

    set_cache(cache_key, response)
    return response


def generate_executive_summary(focus: Optional[str] = None) -> str:
    """
    Runs the fixed operational-report pipeline:
      Node 1 (SQL)          -> current bed occupancy + pending discharges
      Node 2 (Optimization) -> optimize_bed_allocation for shortage forecasting
      Node 3 (RAG)          -> similar past cases to sanity-check recovery times
                                for any ward flagged at risk
      Node 4 (Writer)       -> LLM composes the final memo in EXEC_SUMMARY_FORMAT

    Unlike run_agent(), this does not rely on the model choosing to call the
    right tools — the directive below explicitly walks it through all three
    before writing, and each report run gets its own throwaway thread so it
    never mixes context with an admin's ongoing chat session.
    """
    focus_line = f"Focus area: {focus}. " if focus else ""
    directive = (
        f"{focus_line}Generate a full Executive Operational Summary. Follow these "
        "steps in order, using tools for every factual claim:\n"
        "1. Use sql_query_tool to get current bed occupancy per ward "
        "(join beds).\n"
        "2. Use sql_query_tool to get active patients whose "
        "expected_discharge_date is within the next 3 days.\n"
        "3. Use optimize_bed_allocation (target_free_beds=5) to identify "
        "which wards are at risk of a shortage and which patients to "
        "prioritize for discharge.\n"
        "4. For any ward at risk, use rag_retrieval_tool with that ward's "
        "most common condition to pull comparable past cases and sanity-check "
        "the recovery/discharge estimate.\n"
        "5. Write the final memo.\n\n"
        f"{EXEC_SUMMARY_FORMAT}"
    )

    thread_id = f"report-{datetime.utcnow().strftime('%Y%m%dT%H%M%S%f')}"
    result = agent_executor.invoke(
        {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": directive},
            ]
        },
        config={
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 15,
        },
    )
    return result["messages"][-1].content
