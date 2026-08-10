from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.agents.graph import run_agent

router = APIRouter(prefix="/agent", tags=["Agent"])

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query: str
    response: str

@router.post("/query", response_model=QueryResponse)
async def agent_query(request: QueryRequest):
    """Send a natural language query to the Hospital Resource Optimizer Agent."""
    try:
        response = run_agent(request.query)
        return QueryResponse(query=request.query, response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")