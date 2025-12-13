"""
Health Check API Routes
System health and status endpoints
"""

from fastapi import APIRouter
from app.schemas.common import Response
from app.database import db
import structlog

logger = structlog.get_logger()

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "version": "0.1.0"
    }


@router.get("/health/db")
async def database_health_check():
    """
    Database health check
    
    Returns:
        Database connection status
    """
    try:
        # Try a simple query
        response = db.client.table("users").select("id").limit(1).execute()
        
        return Response(
            success=True,
            message="Database connection healthy",
            data={"status": "connected"}
        )
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return Response(
            success=False,
            message="Database connection failed",
            data={"status": "disconnected", "error": str(e)}
        )

