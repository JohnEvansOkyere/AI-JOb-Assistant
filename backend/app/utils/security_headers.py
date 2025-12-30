"""
Security Headers Middleware
Adds security headers to all HTTP responses
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog

logger = structlog.get_logger()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        
        # Handle OPTIONS preflight for Vercel preview URLs BEFORE other middleware
        if request.method == "OPTIONS" and origin and "vercel.app" in origin:
            from fastapi import Response
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            # Must explicitly list Authorization - browsers don't allow * for this header
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept, X-Requested-With"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Max-Age"] = "600"
            return response
        
        response = await call_next(request)
        
        # Add CORS headers for Vercel preview URLs on regular requests
        if origin and "vercel.app" in origin:
            if "Access-Control-Allow-Origin" not in response.headers:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy (adjust based on your needs)
        # This is a basic CSP - you may need to adjust for your frontend
        # Note: CSP is primarily for frontend pages, not API responses
        # We set it here for completeness, but it won't affect API calls
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # unsafe-eval needed for some libraries
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https: http://localhost:* ws://localhost:* ws://* wss://*; "  # Allow localhost and WebSocket connections
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # HSTS (only for HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Remove server header (optional - hides server technology)
        # Use del instead of pop since MutableHeaders doesn't support pop()
        if "server" in response.headers:
            del response.headers["server"]
        
        return response

