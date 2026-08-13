"""
Tool definitions for the LangGraph agent.
Includes SQL query, RAG retrieval, calculation, patient details lookup,
and bed-allocation optimization.
All tools have docstrings that serve as descriptions for the LLM.
"""

import json
import re
import math
import statistics
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from langchain_core.tools import tool
from app.core.database import SessionLocal
from app.models.database import Patient, Admission, Bed


# ========== SQL Query Tool ==========
@tool
def sql_query_tool(query: str) -> str:
    """
    Execute a SQL query on the hospital database and return results as JSON.
    Only SELECT statements are allowed for safety.
    Results are limited to 20 rows automatically.
    Use this to fetch patient data, bed occupancy, admissions, discharge info, etc.
    """
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
        - "SELECT patient_id, name, expected_discharge_date FROM patients WHERE is_active = true ORDER BY expected_discharge_date LIMIT 5"
        """

    if not query.strip().upper().startswith("SELECT"):
        return "Error: Only SELECT queries are allowed."

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
        error_msg = str(e)
        if "relation" in error_msg.lower():
            return f"SQL Error: {e}\nHint: available tables are patients, admissions, beds, discharge_predictions. Use patient_id as text (with quotes)."
        elif "does not exist" in error_msg.lower() and "column" in error_msg.lower():
            return f"SQL Error: {e}\nHint: check column names. Use patient_id (text), id (integer), etc."
        return f"SQL Error: {e}"


# ========== RAG Retrieval Tool ==========
@tool
def rag_retrieval_tool(
    query: str,
    condition: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
) -> str:
    """
    Retrieve similar past discharge cases. Uses a ChromaDB vector index built
    from discharge notes, ranked by semantic similarity to `query`.

    IMPORTANT — for accurate results, always pass `condition` and/or
    min_age/max_age as SEPARATE structured arguments whenever the user's
    question specifies them, instead of relying on the free-text `query`
    alone to enforce them:
      - "COPD patient in their 50s" -> condition="COPD", min_age=50, max_age=59
      - "elderly cardiac patient" -> condition="Cardiac Arrhythmia" (or similar), min_age=65
    min_age/max_age are applied as a hard filter (results outside the range
    are excluded entirely, not just ranked lower). `condition` filters by
    substring match on the stored diagnosis. Use `query` itself for softer,
    unstructured criteria (symptoms, notes phrasing) that don't map to a
    single field.

    Returns top 5 similar cases with patient details and truncated notes.
    """
    from app.services.retriever import get_similar_cases
    try:
        results = get_similar_cases(
            query, top_k=5, condition=condition, min_age=min_age, max_age=max_age
        )
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
    allowed_names = {
        "abs": abs, "round": round, "sum": sum, "avg": statistics.mean,
        "min": min, "max": max, "len": len, "math": math
    }
    if not re.match(r'^[\d\s+\-*/().,a-zA-Z_]+$', expression):
        return "Error: Invalid characters in expression."
    try:
        result = eval(expression, {"__builtins__": None}, allowed_names)
        return str(result)
    except Exception as e:
        return f"Calculation Error: {str(e)}"


# ========== Patient Details Tool ==========
@tool
def get_patient_details(patient_id: str) -> str:
    """
    Get full details for a patient by their patient_id (e.g., 'P-20260020').
    Returns name, age, gender, condition, admission date, active status, bed number, ward, and doctor.
    """
    with SessionLocal() as db:
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            return f"No patient found with ID {patient_id}."

        admission = db.query(Admission).filter(Admission.patient_id == patient.id).first()
        bed = None
        if admission and admission.bed_number:
            bed = db.query(Bed).filter(Bed.bed_number == admission.bed_number).first()

        result = {
            "patient_id": patient.patient_id,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "condition": patient.condition,
            "admission_date": str(patient.admission_date),
            "is_active": patient.is_active,
            "bed_number": bed.bed_number if bed else None,
            "ward": bed.ward if bed else None,
            "doctor": admission.doctor_in_charge if admission else None,
            "admission_type": admission.admission_type if admission else None,
            "department": admission.department if admission else None,
        }
        return json.dumps(result, default=str, indent=2)


# ========== Bed Allocation Optimization Tool ==========
@tool
def optimize_bed_allocation(target_free_beds: int = 5) -> str:
    """
    Runs a resource-optimization pass over current bed occupancy to identify
    which wards are below a target safety buffer of free beds, and
    recommends which active patients in that ward to prioritize for discharge
    (soonest expected_discharge_date first).

    Input: target_free_beds - the desired safety buffer of free beds per
    ward (default 5). This is a buffer target, NOT "beds until zero" — a
    ward with `at_risk: true` still has free_beds > 0 in most cases, it just
    means free_beds is below the requested buffer, so discuss it as "below
    target buffer" / "at risk", not as "about to run out of beds" unless
    free_beds is actually 0 or negative-trending.

    Returns JSON: for each ward — total_beds, occupied_beds, free_beds,
    target_free_beds, buffer_shortfall (how many additional discharges
    would close the gap to the target buffer; 0 if already at/above it),
    at_risk (bool, true if buffer_shortfall > 0), and a list of recommended
    discharge-priority patients sized to close the shortfall.
    """
    try:
        with SessionLocal() as db:
            ward_rows = db.execute(text("""
                SELECT ward,
                       COUNT(*) AS total,
                       SUM(CASE WHEN is_occupied THEN 1 ELSE 0 END) AS occupied
                FROM beds
                GROUP BY ward
                ORDER BY ward
            """)).fetchall()

            results = []
            for ward, total, occupied in ward_rows:
                occupied = occupied or 0
                free = total - occupied
                buffer_shortfall = max(0, target_free_beds - free)
                at_risk = buffer_shortfall > 0

                candidates = []
                if at_risk:
                    cand_rows = db.execute(text("""
                        SELECT p.patient_id, p.name, p.expected_discharge_date
                        FROM patients p
                        JOIN admissions a ON a.patient_id = p.id
                        WHERE p.is_active = true AND a.department = :ward
                        ORDER BY p.expected_discharge_date ASC NULLS LAST
                        LIMIT :n
                    """), {"ward": ward, "n": buffer_shortfall}).fetchall()
                    candidates = [
                        {
                            "patient_id": r.patient_id,
                            "name": r.name,
                            "expected_discharge_date": str(r.expected_discharge_date) if r.expected_discharge_date else None,
                        }
                        for r in cand_rows
                    ]

                results.append({
                    "ward": ward,
                    "total_beds": total,
                    "occupied_beds": occupied,
                    "free_beds": free,
                    "target_free_beds": target_free_beds,
                    "buffer_shortfall": buffer_shortfall,
                    "at_risk": at_risk,
                    "discharge_priority_candidates": candidates,
                })

            summary = {
                "target_free_beds_per_ward": target_free_beds,
                "note": "at_risk means free_beds is below the target buffer, not that the ward has 0 free beds. Check free_beds directly to see actual availability.",
                "wards_at_risk": len([r for r in results if r["at_risk"]]),
                "results": results,
            }
            return json.dumps(summary, default=str, indent=2)
    except Exception as e:
        return f"Optimization Error: {str(e)}"
