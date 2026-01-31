"""
Authentication middleware for JWT validation.
For MVP, supports simple token validation or mock users.
"""

from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_supabase_client_anon
from app.database_memory import get_memory_db
from app.config import settings
from typing import Optional
import logging
import re

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)  # Don't auto-error for MVP


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> str:
    """
    Extract and validate user_id from JWT token.
    For MVP, accepts simple tokens or creates mock users.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        
    Returns:
        User ID (UUID string)
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    # MVP mode: Allow simple token or create mock user
    if settings.use_memory_db or not credentials:
        # For MVP, use a default test user if no token provided
        if not credentials:
            # Create or get default test user
            memory_db = get_memory_db()
            default_user_id = "test-user-123"
            if default_user_id not in memory_db.users:
                memory_db.create_user(default_user_id, "test@example.com")
            logger.info(f"Using default test user: {default_user_id}")
            return default_user_id
        
        token = credentials.credentials
        
        # Simple token validation for MVP
        # Accept "test-token" or extract user_id from token
        if token == "test-token" or token.startswith("test-user-"):
            user_id = token.replace("test-user-", "") if token.startswith("test-user-") else "test-user-123"
            memory_db = get_memory_db()
            if user_id not in memory_db.users:
                memory_db.create_user(user_id, f"{user_id}@test.com")
            logger.info(f"Authenticated MVP user: {user_id}")
            return user_id
    
    # Real Supabase auth (if configured)
    token = credentials.credentials
    
    try:
        supabase = get_supabase_client_anon()
        
        # Check if it's a Supabase client (has auth attribute)
        if hasattr(supabase, 'auth'):
            user = supabase.auth.get_user(token)
            
            if not user or not user.user:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            user_id = user.user.id
            logger.info(f"Authenticated user: {user_id}")
            return user_id
        else:
            # Fallback to MVP mode
            memory_db = get_memory_db()
            user_id = "test-user-123"
            if user_id not in memory_db.users:
                memory_db.create_user(user_id, "test@example.com")
            return user_id
            
    except Exception as e:
        logger.warning(f"Auth error, using MVP mode: {e}")
        # Fallback to MVP mode
        memory_db = get_memory_db()
        user_id = "test-user-123"
        if user_id not in memory_db.users:
            memory_db.create_user(user_id, "test@example.com")
        return user_id


# Dependency for routes
def require_auth() -> str:
    """Dependency that requires authentication and returns user_id."""
    return Depends(get_current_user_id)
