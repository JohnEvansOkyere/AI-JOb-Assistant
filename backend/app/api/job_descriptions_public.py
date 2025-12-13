"""
Public Job Descriptions API Routes
Public endpoints for viewing job descriptions (no auth required)
"""

from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from app.schemas.common import Response
from app.models.job_description import JobDescription
from app.database import db
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/public/job-descriptions", tags=["public"])


@router.get("/{job_id}", response_model=Response[JobDescription])
async def get_public_job_description(job_id: UUID):
    """
    Get a job description by ID (public, no auth required)
    Only returns active jobs
    
    Args:
        job_id: Job description ID
    
    Returns:
        Job description data
    """
    try:
        response = db.service_client.table("job_descriptions").select("*").eq("id", str(job_id)).eq("is_active", True).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found or not active"
            )
        
        return Response(
            success=True,
            message="Job description retrieved successfully",
            data=response.data[0]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching public job description", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

