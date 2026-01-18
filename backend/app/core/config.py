"""
Cortex - Centralized Configuration
Environment variables with Pydantic Settings validation.
"""

from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    # ==========================================================================
    # Application
    # ==========================================================================
    APP_NAME: str = "Cortex"
    DEBUG: bool = False
    
    # ==========================================================================
    # CORS
    # ==========================================================================
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS_ORIGINS from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    # ==========================================================================
    # Neo4j (Graph + Vector)
    # ==========================================================================
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "cortex123"
    
    # ==========================================================================
    # Redis (Working Memory)
    # ==========================================================================
    REDIS_URL: str = "redis://localhost:6379/0"
    WORKING_MEMORY_TTL: int = 3600  # 1 hour
    
    # ==========================================================================
    # LLM Configuration
    # ==========================================================================
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:latest"
    
    # Cloud LLMs (optional)
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    
    # ==========================================================================
    # Langfuse Observability
    # ==========================================================================
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "http://localhost:3001"


@lru_cache
def get_settings() -> Settings:
    """Cache settings instance."""
    return Settings()


# Singleton instance
settings = get_settings()

