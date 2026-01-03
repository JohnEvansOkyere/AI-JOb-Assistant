"""
Email Verification Utilities
Helper functions for checking email verification status
"""

from fastapi import Depends, HTTPException, status
from app.utils.auth import get_current_user
import structlog

logger = structlog.get_logger()


async def require_email_verified(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency that ensures user's email is verified before accessing protected routes
    
    Args:
        current_user: Current authenticated user (from get_current_user)
    
    Returns:
        User data dictionary (guaranteed to have verified email)
    
    Raises:
        HTTPException: If email is not verified
    """
    email_verified = current_user.get("email_verified", False)
    
    if not email_verified:
        logger.warning("Unverified user attempted to access protected route", user_id=current_user.get("id"))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address before accessing this feature. Check your email for a verification code."
        )
    
    return current_user

