from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db, engine
from app.core.config import settings
from app.models import database as models
from app.api.routes import router as agent_router
from app.api.explain_routes import router as explain_router
from app.api.data_routes import router as data_router

# Create tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Hospital Resource Optimizer Agent - LangGraph + Groq + Neon PostgreSQL",
    version="1.0.0"
)

# CORS middleware – allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agent_router)
app.include_router(explain_router)
app.include_router(data_router)

@app.get("/")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "healthy",
        "database": "Neon PostgreSQL",
        "llm": settings.GROQ_MODEL
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "database": db_status,
        "groq_model": settings.GROQ_MODEL
    }

@app.get("/cache/status")
def cache_status():
    from app.core.cache import _get_redis_client
    try:
        r = _get_redis_client()
        r.ping()
        return {"redis": "connected", "semantic_cache": "active"}
    except Exception as e:
        return {"redis": "error", "detail": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )