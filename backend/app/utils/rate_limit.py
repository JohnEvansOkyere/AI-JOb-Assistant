"""
Rate Limiting Utilities
Provides rate limiting functionality using slowapi
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from app.config import settings
import structlog

logger = structlog.get_logger()

# Initialize rate limiter
# Uses in-memory storage by default, or Redis if configured
if settings.rate_limit_storage_uri:
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=settings.rate_limit_storage_uri,
        default_limits=[settings.rate_limit_default] if settings.rate_limit_enabled else []
    )
    if settings.rate_limit_enabled:
        logger.info("Rate limiting enabled with Redis storage", uri=settings.rate_limit_storage_uri)
    else:
        logger.info("Rate limiting DISABLED - no limits applied")
else:
    # In-memory storage (works for single server, not distributed)
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[settings.rate_limit_default] if settings.rate_limit_enabled else []
    )
    if settings.rate_limit_enabled:
        logger.info("Rate limiting enabled with in-memory storage")
    else:
        logger.info("Rate limiting DISABLED - no limits applied")


def get_user_id(request: Request) -> str:
    """
    Get user ID from JWT token for user-based rate limiting
    Falls back to IP address if no user is authenticated
    """
    try:
        # Try to get user from request state (set by auth middleware)
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"
    except Exception:
        pass
    
    # Fall back to IP address
    return get_remote_address(request)


# No-op decorator when rate limiting is disabled
def _noop_decorator(func):
    """No-op decorator that does nothing - used when rate limiting is disabled"""
    return func


# Predefined rate limit decorators for common use cases
# These use slowapi's limiter.limit() which requires 'request: Request' parameter
# When rate_limit_enabled is False, returns a no-op decorator

def rate_limit_auth():
    """Rate limit for authentication endpoints (login, register) - 3/minute per IP (4th request blocked)"""
    if not settings.rate_limit_enabled:
        return _noop_decorator
    return limiter.limit(settings.rate_limit_auth, key_func=get_remote_address)


def rate_limit_ai():
    """Rate limit for AI analysis endpoints (expensive operations) - 10/hour per user"""
    if not settings.rate_limit_enabled:
        return _noop_decorator
    return limiter.limit(settings.rate_limit_ai, key_func=get_user_id)


def rate_limit_public():
    """Rate limit for public endpoints (application forms) - 20/hour per IP"""
    if not settings.rate_limit_enabled:
        return _noop_decorator
    return limiter.limit(settings.rate_limit_public, key_func=get_remote_address)


def rate_limit_default():
    """Default rate limit for general endpoints - 100/minute per user"""
    if not settings.rate_limit_enabled:
        return _noop_decorator
    return limiter.limit(settings.rate_limit_default, key_func=get_user_id)


def rate_limit_custom(limit: str, key_func=None):
    """
    Custom rate limit decorator
    
    Args:
        limit: Rate limit string (e.g., "10/minute", "100/hour")
        key_func: Optional key function (defaults to get_user_id)
    
    Example:
        @rate_limit_custom("5/minute")
        async def my_endpoint(request: Request, ...):
            ...
    """
    if not settings.rate_limit_enabled:
        return _noop_decorator
    return limiter.limit(limit, key_func=key_func or get_user_id)


# Rate limit exceeded handler
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors"""
    logger.warning(
        "Rate limit exceeded",
        path=request.url.path,
        method=request.method,
        remote_address=get_remote_address(request),
        limit=exc.detail
    )
    from fastapi.responses import JSONResponse
    
    # Determine retry time based on endpoint
    retry_after_seconds = 60  # Default: 1 minute
    if "/auth/" in request.url.path:
        # Auth endpoints: 5 hours retry period
        retry_after_seconds = settings.rate_limit_auth_retry_hours * 3600  # Convert hours to seconds
    
    # Calculate retry time in hours for user-friendly message
    retry_after_hours = retry_after_seconds / 3600
    
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "message": f"Rate limit exceeded: {exc.detail}. Please try again in {retry_after_hours:.0f} hour(s).",
            "error_code": "RateLimitExceeded",
            "retry_after_seconds": retry_after_seconds,
            "retry_after_hours": retry_after_hours
        },
        headers={"Retry-After": str(retry_after_seconds)}
    )

