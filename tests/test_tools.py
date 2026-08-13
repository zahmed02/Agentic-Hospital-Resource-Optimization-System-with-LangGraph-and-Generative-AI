"""
Unit tests for app/agents/tools.py.
These hit the real DB (via SessionLocal) but never call the LLM, so they run
fast and don't need GROQ_API_KEY.

Run:  pytest tests/test_tools.py -v
Requires: DATABASE_URL configured in .env, and seed_data.py already run.
"""
import json
from app.agents.tools import (
    calculate_tool,
    sql_query_tool,
    optimize_bed_allocation,
    get_patient_details,
)


def test_calculate_tool_basic():
    result = calculate_tool.invoke({"expression": "12 + 30"})
    assert result == "42"


def test_calculate_tool_rejects_bad_input():
    result = calculate_tool.invoke({"expression": "__import__('os').system('echo hi')"})
    assert "Error" in result


def test_sql_query_tool_rejects_non_select():
    result = sql_query_tool.invoke({"query": "DELETE FROM patients"})
    assert result == "Error: Only SELECT queries are allowed."


def test_sql_query_tool_returns_json():
    result = sql_query_tool.invoke({"query": "SELECT COUNT(*) as n FROM patients"})
    data = json.loads(result)
    assert "rows" in data
    assert data["rows"][0]["n"] >= 0


def test_optimize_bed_allocation_shape():
    """
    This is the new optimization tool — check the JSON contract the agent
    (and the /agent/report pipeline) depends on.
    """
    result = optimize_bed_allocation.invoke({"target_free_beds": 5})
    data = json.loads(result)
    assert "results" in data
    assert "wards_at_risk" in data
    for ward in data["results"]:
        assert {"ward", "total_beds", "occupied_beds", "free_beds", "shortage"} <= ward.keys()
        assert ward["free_beds"] == ward["total_beds"] - ward["occupied_beds"]
        if ward["shortage"] > 0:
            assert len(ward["discharge_priority_candidates"]) <= ward["shortage"]


def test_get_patient_details_not_found():
    result = get_patient_details.invoke({"patient_id": "P-DOES-NOT-EXIST"})
    assert "No patient found" in result
