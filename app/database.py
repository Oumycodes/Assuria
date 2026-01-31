"""
Database client and connection management.
Uses Supabase if configured, otherwise falls back to in-memory database for MVP.
"""

from app.config import settings
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

# Try to import Supabase, but make it optional
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase not available, using in-memory database")

# Import in-memory database
from app.database_memory import get_memory_client, get_memory_db

# Global Supabase client (service role for backend operations)
_supabase_client: Optional[Union['Client', object]] = None


def get_supabase_client():
    """
    Get or create Supabase client with service role key, or in-memory client.
    Falls back to in-memory database if Supabase is not configured.
    """
    global _supabase_client
    
    # Check if we should use in-memory database
    use_memory = (
        not SUPABASE_AVAILABLE or
        not hasattr(settings, 'supabase_url') or
        not settings.supabase_url or
        settings.supabase_url == "https://your-project.supabase.co" or
        getattr(settings, 'use_memory_db', False)
    )
    
    if use_memory:
        logger.info("Using in-memory database (MVP mode)")
        return get_memory_client()
    
    # Use real Supabase
    if _supabase_client is None:
        try:
            _supabase_client = create_client(
                settings.supabase_url,
                settings.supabase_service_role_key
            )
            logger.info("Supabase client initialized with service role")
        except Exception as e:
            logger.warning(f"Failed to initialize Supabase, using in-memory: {e}")
            return get_memory_client()
    
    return _supabase_client


def get_supabase_client_anon():
    """
    Get Supabase client with anon key, or in-memory client.
    Falls back to in-memory database if Supabase is not configured.
    """
    # Check if we should use in-memory database
    use_memory = (
        not SUPABASE_AVAILABLE or
        not hasattr(settings, 'supabase_url') or
        not settings.supabase_url or
        settings.supabase_url == "https://your-project.supabase.co" or
        getattr(settings, 'use_memory_db', False)
    )
    
    if use_memory:
        return get_memory_client()
    
    try:
        return create_client(
            settings.supabase_url,
            settings.supabase_key
        )
    except Exception as e:
        logger.warning(f"Failed to initialize Supabase anon client, using in-memory: {e}")
        return get_memory_client()
