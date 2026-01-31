"""
Configuration management for Assura backend.
Loads environment variables and provides typed configuration.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Supabase (optional for MVP)
    supabase_url: str = "https://your-project.supabase.co"
    supabase_key: str = "dummy-key"
    supabase_service_role_key: str = "dummy-service-key"
    supabase_db_url: str = "postgresql://dummy"
    
    # Encryption (optional for MVP - no-op encryption used when use_memory_db=True)
    encryption_key: str = "dummy-encryption-key-32-bytes-long!!"  # Not used in MVP mode
    
    # Anthropic Claude (uses Replit AI Integrations)
    anthropic_api_key: str = os.getenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY", "dummy-key")
    anthropic_base_url: Optional[str] = os.getenv("AI_INTEGRATIONS_ANTHROPIC_BASE_URL", None)
    
    # Celery/Redis (optional for MVP)
    redis_url: str = "redis://localhost:6379/0"
    
    # Application
    environment: str = "development"
    log_level: str = "INFO"
    
    # MVP mode: use in-memory database
    # Set to False to use real Supabase when configured
    use_memory_db: bool = os.getenv("USE_MEMORY_DB", "true").lower() == "true"
    
    # Confidence thresholds
    min_confidence_threshold: float = 0.6
    critical_fields: list[str] = ["incident_type", "date", "location"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        # Allow missing environment variables (use defaults)
        extra = "ignore"


# Global settings instance
# For MVP, use defaults if .env doesn't exist
try:
    settings = Settings()
except Exception as e:
    # If loading fails, use defaults
    print(f"Warning: Could not load settings from .env, using defaults: {e}")
    settings = Settings(
        _env_file=None,  # Don't try to load .env
        use_memory_db=True
    )
