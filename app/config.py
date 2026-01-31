"""
Configuration management for Assura backend.
Loads environment variables and provides typed configuration.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_role_key: str
    supabase_db_url: str
    
    # Encryption
    encryption_key: str  # Base64-encoded Fernet key
    
    # Anthropic Claude
    anthropic_api_key: str
    
    # Celery/Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Application
    environment: str = "development"
    log_level: str = "INFO"
    
    # Confidence thresholds
    min_confidence_threshold: float = 0.6
    critical_fields: list[str] = ["incident_type", "date", "location"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
