"""
Job Descriptions API Routes
CRUD operations for job descriptions
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from app.schemas.common import Response, PaginatedResponse
from app.models.job_description import JobDescription, JobDescriptionCreate, JobDescriptionUpdate
from app.services.job_description_service import JobDescriptionService
from app.utils.auth import get_current_user_id
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/job-descriptions", tags=["job-descriptions"])


@router.post("", response_model=Response[JobDescription], status_code=status.HTTP_201_CREATED)
async def create_job_description(
    job_data: JobDescriptionCreate,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Create a new job description
    
    Args:
        job_data: Job description data
        recruiter_id: Current user ID (from auth)
    
    Returns:
        Created job description
    """
    try:
        job = await JobDescriptionService.create_job_description(recruiter_id, job_data)
        return Response(
            success=True,
            message="Job description created successfully",
            data=job
        )
    except Exception as e:
        logger.error("Error creating job description", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=Response[List[JobDescription]])
async def list_job_descriptions(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    List job descriptions for the current recruiter
    
    Args:
        is_active: Optional filter by active status
        limit: Maximum number of results
        offset: Offset for pagination
        recruiter_id: Current user ID
    
    Returns:
        List of job descriptions
    """
    try:
        jobs = await JobDescriptionService.list_job_descriptions(
            recruiter_id=recruiter_id,
            is_active=is_active,
            limit=limit,
            offset=offset
        )
        return Response(
            success=True,
            message="Job descriptions retrieved successfully",
            data=jobs
        )
    except Exception as e:
        logger.error("Error listing job descriptions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{job_id}", response_model=Response[JobDescription])
async def get_job_description(
    job_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Get a job description by ID
    
    Args:
        job_id: Job description ID
        recruiter_id: Current user ID (for authorization)
    
    Returns:
        Job description data
    """
    try:
        job = await JobDescriptionService.get_job_description(job_id, recruiter_id)
        return Response(
            success=True,
            message="Job description retrieved successfully",
            data=job
        )
    except Exception as e:
        logger.error("Error fetching job description", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/{job_id}", response_model=Response[JobDescription])
async def update_job_description(
    job_id: UUID,
    job_data: JobDescriptionUpdate,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Update a job description
    
    Args:
        job_id: Job description ID
        job_data: Updated job description data
        recruiter_id: Current user ID (for authorization)
    
    Returns:
        Updated job description
    """
    try:
        job = await JobDescriptionService.update_job_description(job_id, recruiter_id, job_data)
        return Response(
            success=True,
            message="Job description updated successfully",
            data=job
        )
    except Exception as e:
        logger.error("Error updating job description", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{job_id}", response_model=Response[dict])
async def delete_job_description(
    job_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Delete a job description
    
    Args:
        job_id: Job description ID
        recruiter_id: Current user ID (for authorization)
    
    Returns:
        Deletion confirmation
    """
    try:
        await JobDescriptionService.delete_job_description(job_id, recruiter_id)
        return Response(
            success=True,
            message="Job description deleted successfully"
        )
    except Exception as e:
        logger.error("Error deleting job description", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

