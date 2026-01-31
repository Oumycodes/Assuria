"""
Authentication middleware for Supabase JWT validation.
Extracts user_id from JWT token in Authorization header.
"""

from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from app.database import get_supabase_client_anon
import jwt
from typing import Optional
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    Extract and validate user_id from JWT token.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        
    Returns:
        User ID (UUID string)
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    token = credentials.credentials
    
    try:
        # Verify token with Supabase
        supabase = get_supabase_client_anon()
        user = supabase.auth.get_user(token)
        
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = user.user.id
        logger.info(f"Authenticated user: {user_id}")
        return user_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


# Dependency for routes
def require_auth() -> str:
    """Dependency that requires authentication and returns user_id."""
    return Depends(get_current_user_id)
