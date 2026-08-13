from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.agents.graph import run_agent, generate_executive_summary
from app.agents.debate import run_clinical_debate
from app.models.schemas import (
    QueryRequest,
    QueryResponse,
    ReportRequest,
    ReportResponse,
    DebateResponse,
)

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post("/query", response_model=QueryResponse)
async def agent_query(request: QueryRequest):
    """
    Send a natural language query to the Hospital Resource Optimizer Agent.
    Pass a stable session_id per conversation to get real multi-turn memory
    (e.g. so "what about her labs?" resolves to the last patient discussed).
    """
    session_id = request.session_id or "default"
    try:
        response = run_agent(request.query, session_id=session_id)
        return QueryResponse(query=request.query, response=response, session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.post("/report", response_model=ReportResponse)
async def agent_report(request: ReportRequest):
    """
    Generate a full Executive Operational Summary: bed occupancy + pending
    discharges (SQL) -> shortage forecasting (optimization) -> comparable
    past cases (RAG) -> memo (LLM writer).
    """
    try:
        summary = generate_executive_summary(focus=request.focus)
        return ReportResponse(summary=summary, generated_at=datetime.utcnow().isoformat())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation error: {str(e)}")


@router.get("/debate/{patient_id}", response_model=DebateResponse)
async def agent_debate(patient_id: str):
    """
    Clinician vs discharge coordinator debate for a single patient
    (by patient_id, e.g. 'P-20260020'), resolved to one final recommendation.
    """
    try:
        result = run_clinical_debate(patient_id)
        return DebateResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debate error: {str(e)}")
