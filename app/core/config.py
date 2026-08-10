from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Hospital-Resource-Optimizer-Agent"
    DEBUG: bool = True
    
    # Groq API
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_FAST_MODEL: str = "llama-3.1-8b-instant"
    
    # Database
    DATABASE_URL: str
    
    # Vector Store
    VECTOR_STORE_PATH: str = "./data/processed/faiss_index"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Redis / Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 86400
    SEMANTIC_SIMILARITY_THRESHOLD: float = 0.92
    
    # Security
    SECRET_KEY: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()