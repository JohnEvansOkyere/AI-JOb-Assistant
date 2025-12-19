"""
Health Check API Routes
System health and status endpoints
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.common import Response
from app.database import db
from app.config import settings
import structlog
from typing import Dict, Any
import time

logger = structlog.get_logger()

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    Enhanced health check endpoint with system status
    
    Returns:
        Health status with database and service checks
    """
    health_data: Dict[str, Any] = {
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.app_env,
        "checks": {}
    }
    
    overall_status = "healthy"
    
    # Database check
    try:
        start_time = time.time()
        response = db.client.table("users").select("id").limit(1).execute()
        db_latency = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        health_data["checks"]["database"] = {
            "status": "healthy",
            "latency_ms": round(db_latency, 2),
            "connected": True
        }
    except Exception as e:
        overall_status = "degraded"
        health_data["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "connected": False
        }
        logger.error("Database health check failed", error=str(e))
    
    # Storage check (Supabase Storage)
    try:
        start_time = time.time()
        # Try to list buckets (lightweight operation)
        buckets = db.service_client.storage.list_buckets()
        storage_latency = (time.time() - start_time) * 1000
        
        health_data["checks"]["storage"] = {
            "status": "healthy",
            "latency_ms": round(storage_latency, 2),
            "connected": True
        }
    except Exception as e:
        overall_status = "degraded"
        health_data["checks"]["storage"] = {
            "status": "unhealthy",
            "error": str(e),
            "connected": False
        }
        logger.warning("Storage health check failed", error=str(e))
    
    # Email service check (check if configured)
    email_status = "not_configured"
    if settings.email_provider == "resend" and settings.resend_api_key:
        email_status = "configured"
    elif settings.email_provider == "smtp" and settings.smtp_enabled and settings.smtp_host:
        email_status = "configured"
    
    health_data["checks"]["email"] = {
        "status": email_status,
        "provider": settings.email_provider
    }
    
    # AI provider check (check if at least one is configured)
    ai_providers = []
    if settings.openai_api_key:
        ai_providers.append("openai")
    if settings.groq_api_key:
        ai_providers.append("groq")
    if settings.gemini_api_key:
        ai_providers.append("gemini")
    
    health_data["checks"]["ai"] = {
        "status": "configured" if ai_providers else "not_configured",
        "providers": ai_providers,
        "primary": settings.primary_ai_provider
    }
    
    health_data["status"] = overall_status
    
    # Return appropriate status code
    status_code = status.HTTP_200_OK if overall_status == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(
        success=overall_status == "healthy",
        message=f"System status: {overall_status}",
        data=health_data
    )


@router.get("/health/db")
async def database_health_check():
    """
    Database health check
    
    Returns:
        Database connection status
    """
    try:
        start_time = time.time()
        # Try a simple query
        response = db.client.table("users").select("id").limit(1).execute()
        latency = (time.time() - start_time) * 1000
        
        return Response(
            success=True,
            message="Database connection healthy",
            data={
                "status": "connected",
                "latency_ms": round(latency, 2)
            }
        )
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return Response(
            success=False,
            message="Database connection failed",
            data={"status": "disconnected", "error": str(e)}
        )

