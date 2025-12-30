"""
Admin Authentication Utilities
Checks if user has admin privileges
"""

from fastapi import Depends, HTTPException, status
from app.utils.auth import get_current_user
from app.database import db
import structlog

logger = structlog.get_logger()


async def get_current_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Get current user and verify they are an admin
    
    Args:
        current_user: Current authenticated user (from get_current_user)
    
    Returns:
        User data dictionary (guaranteed to be admin)
    
    Raises:
        HTTPException: If user is not an admin
    """
    user_id = current_user.get("id")
    
    # Check if user is admin
    if not current_user.get("is_admin", False):
        logger.warning("Non-admin user attempted to access admin endpoint", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


async def require_admin(current_user: dict = Depends(get_current_user)) -> None:
    """
    Verify current user is an admin (throws exception if not)
    This is a convenience function for endpoints that just need to check admin status
    
    Args:
        current_user: Current authenticated user
    
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.get("is_admin", False):
        user_id = current_user.get("id")
        logger.warning("Non-admin user attempted to access admin endpoint", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

