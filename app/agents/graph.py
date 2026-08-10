"""
LangGraph agent with caching (exact + semantic), token trimming, and limited tool outputs.
"""

import tiktoken
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from app.core.config import settings
from app.agents.tools import sql_query_tool, rag_retrieval_tool, calculate_tool
from app.core.cache import get_cached_response, set_cache

# ---------- Token counting (for reference) ----------
encoding = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    """Count tokens in a string."""
    return len(encoding.encode(text))

# ---------- (Optional) message trimming ----------
# Note: create_react_agent does not accept a message_modifier, so this function
# is kept for documentation / future use. Actual token reduction is achieved by:
#   - truncating tool outputs (already in tools.py)
#   - limiting LLM max_tokens to 500
#   - limiting recursion to 10 steps
def trim_messages(messages: List[Dict[str, Any]], max_tokens: int = 10000) -> List[Dict[str, Any]]:
    """
    Trim messages to stay under max_tokens.
    Keeps system message, most recent user message, and last few assistant/tool messages.
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

    # Keep last 6 non‑system messages
    trimmed = non_system[-6:] if len(non_system) > 6 else non_system
    if system_msg:
        trimmed = [system_msg] + trimmed

    # Truncate tool content if still too large
    total_tokens = sum(count_tokens(str(msg)) for msg in trimmed)
    if total_tokens > max_tokens:
        for msg in trimmed:
            if msg.get("role") == "tool" and "content" in msg:
                content = msg["content"]
                if len(content) > 500:
                    msg["content"] = content[:500] + "... (truncated)"
        # Drop oldest non‑system messages if still over limit
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
    model=settings.GROQ_MODEL,         # llama-3.3-70b-versatile
    temperature=0.1,
    max_tokens=500,                    # limit response length
)

tools = [sql_query_tool, rag_retrieval_tool, calculate_tool]
agent_executor = create_react_agent(llm, tools)

# ---------- Main entry point with caching ----------
SYSTEM_PROMPT = """You are a hospital resource optimization assistant. Your job is to answer questions using the tools provided.

IMPORTANT: You MUST use the tools to get real data. Never guess or use your own knowledge.

Available tools:
- sql_query_tool: Execute SQL SELECT queries on the hospital database.
- rag_retrieval_tool: Find similar past cases.
- calculate_tool: Do math.

When asked about patient counts, bed occupancy, or any number, ALWAYS use sql_query_tool.

For example:
- To get ICU patient count: sql_query_tool("SELECT COUNT(*) FROM beds WHERE ward = 'ICU' AND is_occupied = true")
- To get bed occupancy by ward: sql_query_tool("SELECT ward, COUNT(*) FROM beds WHERE is_occupied = true GROUP BY ward")

If you don't know the exact SQL, ask for the schema first: sql_query_tool("schema")

Always base your answer on the tool's output. If a tool returns no rows, say so.
"""

# Then in the agent creation, we need to pass this as a system message.
# Since create_react_agent doesn't directly support system prompt, we'll wrap it:

def run_agent(query: str) -> str:
    # 1. Check cache
    cached_response, from_semantic = get_cached_response(query)
    if cached_response:
        print(f"Cache hit (semantic={from_semantic}) for: {query[:50]}...")
        return cached_response

    # 2. Cache miss – invoke agent with system prompt
    try:
        # Create messages with system prompt
        messages = [
            ("system", SYSTEM_PROMPT),
            ("user", query)
        ]
        result = agent_executor.invoke(
            {"messages": messages},
            config={"recursion_limit": 20}
        )
        messages = result["messages"]
        last_msg = messages[-1]
        response = last_msg.content
    except Exception as e:
        return f"Agent error: {str(e)}"

    # 3. Only cache if response is not a generic error/fallback
    if response and not response.startswith(("Sorry", "Agent error", "I couldn't", "Error")):
        set_cache(query, response)
    else:
        print(f"Not caching error/fallback response: {response}")

    return response