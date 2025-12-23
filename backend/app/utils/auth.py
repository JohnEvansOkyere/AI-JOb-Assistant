"""
Authentication Utilities
JWT token handling and user authentication
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.database import db
import structlog
import sentry_sdk

logger = structlog.get_logger()

# Security scheme
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: Data to encode in token
        expires_delta: Optional expiration time delta
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer token credentials
    
    Returns:
        User data dictionary
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Verify user exists in Supabase
    try:
        response = db.client.table("users").select("*").eq("id", user_id).execute()
        if not response.data:
            raise credentials_exception
        user = response.data[0]
        
        # Add user context to Sentry (non-sensitive info only)
        sentry_sdk.set_user({
            "id": str(user_id),
            "email": user.get("email"),  # Email is generally safe to log
        })
        
        return user
    except Exception as e:
        logger.error("Error fetching user", error=str(e))
        raise credentials_exception


async def get_current_user_id(
    current_user: dict = Depends(get_current_user)
) -> UUID:
    """
    Get current user ID as UUID
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User ID as UUID
    """
    return UUID(current_user["id"])


def verify_supabase_token(token: str) -> Optional[dict]:
    """
    Verify Supabase JWT token
    
    Args:
        token: Supabase JWT token
    
    Returns:
        User data if valid, None otherwise
    """
    try:
        # Supabase tokens are already verified by Supabase client
        # This is a placeholder for additional verification if needed
        # In production, you might want to verify the token signature
        return None
    except Exception as e:
        logger.error("Error verifying Supabase token", error=str(e))
        return None

