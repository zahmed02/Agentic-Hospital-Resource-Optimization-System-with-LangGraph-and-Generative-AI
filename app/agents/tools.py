"""
Tool definitions for the LangGraph agent.
Includes SQL query, RAG retrieval, and calculation tools.
All tools have docstrings that serve as descriptions for the LLM.
"""

import json
import re
import math
import statistics
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import text
from langchain_core.tools import tool
from app.core.database import SessionLocal
from app.models.database import Patient, Admission, Bed, DischargePrediction


# ========== SQL Query Tool ==========
@tool
def sql_query_tool(query: str) -> str:
    """
    Execute a SQL query on the hospital database and return results as JSON.
    Only SELECT statements are allowed for safety.
    Results are limited to 20 rows automatically.
    Use this to fetch patient data, bed occupancy, admissions, discharge info, etc.
    """
    # If the query asks about schema or tables, return the schema
    if "schema" in query.lower() or "tables" in query.lower():
        return """
        Database Schema:
        - patients: id, patient_id, name, age, gender, condition, admission_date, expected_discharge_date, actual_discharge_date, is_active
        - admissions: id, patient_id, admission_type, department, bed_number, doctor_in_charge, admission_date, discharge_date, notes, is_discharged
        - beds: id, ward, bed_number, is_occupied, patient_id
        - discharge_predictions: id, patient_id, prediction_date, predicted_discharge_date, confidence_score, factors, actual_discharge_date, accuracy
        
        Example queries:
        - "SELECT ward, COUNT(*) as occupied_beds FROM beds WHERE is_occupied = true GROUP BY ward"
        - "SELECT COUNT(*) FROM patients WHERE is_active = true"
        - "SELECT * FROM patients WHERE condition ILIKE '%pneumonia%' LIMIT 10"
        """

    if not query.strip().upper().startswith("SELECT"):
        return "Error: Only SELECT queries are allowed."

    # Auto-add LIMIT to avoid huge outputs
    if "LIMIT" not in query.upper():
        query = query.rstrip(";") + " LIMIT 20"

    try:
        with SessionLocal() as db:
            result = db.execute(text(query))
            rows = result.fetchall()
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in rows]
            summary = f"Returned {len(data)} rows (limited to 20)."
            return json.dumps({"summary": summary, "rows": data}, default=str, indent=2)
    except Exception as e:
        return f"SQL Error: {str(e)}"


# ========== RAG Retrieval Tool ==========
@tool
def rag_retrieval_tool(query: str) -> str:
    """
    Retrieve similar past discharge cases based on a description (e.g., condition, age, symptoms).
    Uses FAISS index built from discharge notes.
    Returns top 5 similar cases with patient details and truncated notes.
    """
    from app.services.retriever import get_similar_cases
    try:
        results = get_similar_cases(query, top_k=5)
        # Truncate long notes for token saving
        for res in results:
            if "notes" in res and res["notes"] and len(res["notes"]) > 100:
                res["notes"] = res["notes"][:100] + "..."
        return json.dumps(results, default=str, indent=2)
    except Exception as e:
        return f"RAG Error: {str(e)}"


# ========== Calculation Tool ==========
@tool
def calculate_tool(expression: str) -> str:
    """
    Perform mathematical calculations safely.
    Input should be a valid arithmetic expression using numbers, operators, and basic functions.
    Examples: '35 + 12', 'avg([5,10,15])', 'sum([1,2,3])', 'max([4,8,2])'
    """
    # Allowed names for safe evaluation
    allowed_names = {
        "abs": abs, "round": round, "sum": sum, "avg": statistics.mean,
        "min": min, "max": max, "len": len, "math": math
    }
    # Sanitize input: only allow letters, numbers, operators, brackets, commas, dots, and underscores
    if not re.match(r'^[\d\s+\-*/().,a-zA-Z_]+$', expression):
        return "Error: Invalid characters in expression."
    try:
        result = eval(expression, {"__builtins__": None}, allowed_names)
        return str(result)
    except Exception as e:
        return f"Calculation Error: {str(e)}"