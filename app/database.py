"""
Supabase database client and connection management.
Uses service role key for backend operations (bypasses RLS).
"""

from supabase import create_client, Client
from app.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Global Supabase client (service role for backend operations)
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create Supabase client with service role key.
    Service role bypasses RLS - backend handles authorization.
    """
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
        logger.info("Supabase client initialized with service role")
    
    return _supabase_client


def get_supabase_client_anon() -> Client:
    """
    Get Supabase client with anon key (for user-facing operations).
    This respects RLS policies.
    """
    return create_client(
        settings.supabase_url,
        settings.supabase_key
    )
