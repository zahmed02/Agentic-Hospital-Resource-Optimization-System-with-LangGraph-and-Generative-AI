"""
Lightweight two-role clinical debate: Clinician vs Discharge Coordinator,
resolved by an arbiter — a minimal stand-in for a full CrewAI/AutoGen
multi-agent setup that doesn't require adding a new heavy dependency.

Matches the spec's:
  Agent 1 (The Clinician): "Patient X is clinically fit to go home."
  Agent 2 (The Admin): "But Patient X has no family support until tomorrow."
  -> resolved final actionable recommendation.
"""

from langchain_groq import ChatGroq
from app.core.config import settings
from app.agents.tools import get_patient_details

_llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    temperature=0.3,
    max_tokens=400,
)

CLINICIAN_SYSTEM = (
    "You are Dr. Reyes, an attending clinician. You argue purely on clinical "
    "readiness for discharge: vitals trend, labs, days since admission relative "
    "to the condition's typical recovery window. Base every claim only on the "
    "patient record you're given. Be concise (3-4 sentences)."
)

ADMIN_SYSTEM = (
    "You are Morgan, the discharge planning coordinator. You argue based on "
    "non-clinical discharge barriers: family/social support, transport, home "
    "care setup, insurance and paperwork. If the record doesn't mention a "
    "barrier, say so rather than inventing one. Be concise (3-4 sentences)."
)

ARBITER_SYSTEM = (
    "You are the Chief Resident. Given a clinician's view and a discharge "
    "coordinator's view on the same patient, issue exactly one final "
    "recommendation: DISCHARGE NOW, DISCHARGE WITH CONDITIONS (state the "
    "condition), or HOLD (state what needs to resolve first). Max 3 sentences."
)


def run_clinical_debate(patient_id: str) -> dict:
    """
    Runs the Clinician -> Coordinator -> Arbiter sequence for one patient
    and returns all three viewpoints plus the final resolution.
    """
    patient_json = get_patient_details.invoke({"patient_id": patient_id})

    if patient_json.startswith("No patient found"):
        return {
            "patient_id": patient_id,
            "clinician_view": patient_json,
            "admin_view": patient_json,
            "resolution": patient_json,
        }

    clinician_view = _llm.invoke([
        {"role": "system", "content": CLINICIAN_SYSTEM},
        {"role": "user", "content": f"Patient record:\n{patient_json}\n\nIs this patient clinically ready for discharge?"},
    ]).content

    admin_view = _llm.invoke([
        {"role": "system", "content": ADMIN_SYSTEM},
        {"role": "user", "content": f"Patient record:\n{patient_json}\n\nAre there any non-clinical barriers to discharging this patient?"},
    ]).content

    resolution = _llm.invoke([
        {"role": "system", "content": ARBITER_SYSTEM},
        {"role": "user", "content": f"Clinician says: {clinician_view}\n\nCoordinator says: {admin_view}\n\nFinal recommendation?"},
    ]).content

    return {
        "patient_id": patient_id,
        "clinician_view": clinician_view,
        "admin_view": admin_view,
        "resolution": resolution,
    }
