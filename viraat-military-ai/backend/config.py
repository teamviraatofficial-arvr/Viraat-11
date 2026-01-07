from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Environment
    environment: str = "development"
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database (SQLite by default, PostgreSQL for production)
    database_url: str = "sqlite:///./viraat_military_ai.db"
    
    # LLM Settings
    llm_model_path: str = "./models/llm/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    llm_context_size: int = 4096
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.7
    llm_n_gpu_layers: int = 0  # -1 for GPU, 0 for CPU
    mock_llm: bool = False
    
    # ChromaDB Settings
    chromadb_path: str = "../knowledge-base/embeddings"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # RAG Settings
    rag_top_k: int = 5
    rag_min_similarity: float = 0.05 # Lowered to catch short terms like "M4A1"3
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # Analytics
    enable_analytics: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
