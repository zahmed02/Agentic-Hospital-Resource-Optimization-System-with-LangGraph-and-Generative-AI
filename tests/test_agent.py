"""
Integration tests for the agent's memory, executive-summary, and debate
pipelines. These call the real LLM (Groq), so keep this suite small and
expect it to take longer / cost tokens. Auto-skips if GROQ_API_KEY isn't set.

Run:  pytest tests/test_agent.py -v -s
"""
import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY not set"
)

from app.agents.graph import run_agent, generate_executive_summary
from app.agents.debate import run_clinical_debate


def test_run_agent_basic():
    response = run_agent("How many active patients are there?", session_id="test-basic")
    assert isinstance(response, str) and len(response) > 0


def test_run_agent_memory_followup():
    """
    Core thing this patch fixes: memory across turns within one session_id.
    Turn 2 uses a pronoun with no patient_id — should resolve via memory,
    not ask for clarification.
    """
    session_id = "test-memory-001"

    first = run_agent(
        "Look up patient P-20260001 and tell me their condition.",
        session_id=session_id,
    )
    assert isinstance(first, str)
    print("\nTurn 1:", first)

    second = run_agent("What ward is she in?", session_id=session_id)
    print("Turn 2:", second)
    assert isinstance(second, str)
    assert "which patient" not in second.lower()


def test_different_sessions_dont_leak_context():
    """
    A pronoun follow-up in a BRAND NEW session (no prior turn) should NOT
    silently resolve to a patient from a different session's history.
    """
    run_agent("Look up patient P-20260001.", session_id="test-session-A")
    response = run_agent("What ward is she in?", session_id="test-session-B-fresh")
    print("\nFresh-session response:", response)
    assert isinstance(response, str)
    assert ("which patient" in response.lower()) or ("clarif" in response.lower())


def test_generate_executive_summary():
    summary = generate_executive_summary()
    print("\nExecutive summary:\n", summary)
    assert isinstance(summary, str) and len(summary) > 50


def test_clinical_debate():
    result = run_clinical_debate("P-20260001")
    print("\nDebate result:", result)
    assert {"clinician_view", "admin_view", "resolution"} <= result.keys()
