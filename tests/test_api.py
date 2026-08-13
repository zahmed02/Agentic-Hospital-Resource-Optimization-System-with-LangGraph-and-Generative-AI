"""
API-level smoke tests using FastAPI's TestClient (no running server needed —
imports your `main.app` directly).

Run:  pytest tests/test_api.py -v
Requires: `httpx` installed (pip install httpx), DB reachable so main.py
imports cleanly. Agent-related tests skip automatically without GROQ_API_KEY.
"""
import os
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200


def test_dashboard_stats():
    res = client.get("/api/dashboard/stats")
    assert res.status_code == 200
    assert "total_patients" in res.json()


@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY not set")
def test_agent_query_returns_session_id():
    res = client.post(
        "/agent/query",
        json={"query": "How many beds are free?", "session_id": "api-test-1"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["session_id"] == "api-test-1"
    assert "response" in data


@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY not set")
def test_agent_report():
    res = client.post("/agent/report", json={})
    assert res.status_code == 200
    assert "summary" in res.json()


@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY not set")
def test_agent_debate_unknown_patient():
    res = client.get("/agent/debate/P-NOT-REAL")
    assert res.status_code == 200
    assert "No patient found" in res.json()["resolution"]
