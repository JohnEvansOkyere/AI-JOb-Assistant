"""
Job Descriptions API Routes
CRUD operations for job descriptions
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Body
from typing import List, Optional
from uuid import UUID
from app.schemas.common import Response, PaginatedResponse
from app.models.job_description import JobDescription, JobDescriptionCreate, JobDescriptionUpdate
from app.services.job_description_service import JobDescriptionService
from app.utils.auth import get_current_user_id
from app.api.applications import send_cv_rejection_email, send_interview_rejection_email
from app.database import db
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
        error_msg = str(e)
        logger.error("Error creating job description", error=error_msg, recruiter_id=str(recruiter_id))
        # Return more detailed error information
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Failed to create job description",
                "error": error_msg
            }
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


@router.post("/{job_id}/complete-hiring", response_model=Response[JobDescription])
async def complete_hiring(
    job_id: UUID,
    hiring_status: str = Body(..., embed=True, description="hiring_status to set: 'filled' or 'closed'"),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Mark job as hiring completed (filled or closed)
    Sets hiring_status to 'filled' or 'closed' to indicate recruitment is complete
    
    Args:
        job_id: Job description ID
        hiring_status: 'filled' (position filled) or 'closed' (no longer hiring)
        recruiter_id: Current user ID (for authorization)
    
    Returns:
        Updated job description
    """
    try:
        # Validate hiring_status
        valid_statuses = ['filled', 'closed']
        if hiring_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid hiring_status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Update hiring_status
        job_data = JobDescriptionUpdate(hiring_status=hiring_status)
        job = await JobDescriptionService.update_job_description(job_id, recruiter_id, job_data)
        
        logger.info(
            "Job hiring marked as complete",
            job_id=str(job_id),
            hiring_status=hiring_status,
            recruiter_id=str(recruiter_id)
        )
        
        return Response(
            success=True,
            message=f"Job marked as {hiring_status}. You can now send rejection emails to candidates.",
            data=job
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error completing hiring", error=str(e), job_id=str(job_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{job_id}/send-rejections", response_model=Response[dict])
async def send_rejection_emails(
    job_id: UUID,
    background_tasks: BackgroundTasks,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Send rejection emails to all candidates who need them for a completed job
    
    Sends two types of rejection emails:
    1. CV Rejection: To candidates who applied but were never interviewed
    2. Interview Rejection: To candidates who completed interviews but weren't accepted
    
    Args:
        job_id: Job description ID
        background_tasks: FastAPI background tasks for email sending
        recruiter_id: Current user ID (for authorization)
    
    Returns:
        Summary of emails sent
    """
    try:
        # Verify recruiter owns the job
        job_response = db.service_client.table("job_descriptions").select(
            "id, title, recruiter_id, hiring_status"
        ).eq("id", str(job_id)).eq("recruiter_id", str(recruiter_id)).execute()
        
        if not job_response.data:
            raise HTTPException(status_code=404, detail="Job not found or not authorized")
        
        job = job_response.data[0]
        job_title = job.get("title", "Position")
        hiring_status = job.get("hiring_status", "active")
        
        # Warn if hiring is not marked as complete
        if hiring_status not in ['filled', 'closed']:
            logger.warning(
                "Sending rejections for job that is not marked as complete",
                job_id=str(job_id),
                hiring_status=hiring_status
            )
        
        # Get all applications for this job
        applications_response = db.service_client.table("job_applications").select(
            "id, candidate_id, candidates!inner(email, full_name)"
        ).eq("job_description_id", str(job_id)).execute()
        
        if not applications_response.data:
            return Response(
                success=True,
                message="No applications found for this job",
                data={
                    "cv_rejections_sent": 0,
                    "interview_rejections_sent": 0,
                    "total_candidates": 0
                }
            )
        
        applications = applications_response.data
        application_ids = [app["id"] for app in applications]
        
        # Get all interviews for this job to identify who was interviewed
        interviews_response = db.service_client.table("interviews").select(
            "id, candidate_id, job_status, completed_at"
        ).eq("job_description_id", str(job_id)).execute()
        
        interviewed_candidate_ids = set()
        accepted_candidate_ids = set()
        interview_data = {}
        
        if interviews_response.data:
            for interview in interviews_response.data:
                candidate_id = interview.get("candidate_id")
                if candidate_id:
                    interviewed_candidate_ids.add(candidate_id)
                    interview_data[candidate_id] = interview
                    if interview.get("job_status") == "accepted":
                        accepted_candidate_ids.add(candidate_id)
        
        # Separate candidates into two groups:
        # 1. CV rejections: Applied but never interviewed
        # 2. Interview rejections: Interviewed but not accepted
        
        cv_rejection_count = 0
        interview_rejection_count = 0
        
        for application in applications:
            candidate_id = application.get("candidate_id")
            candidate = application.get("candidates", {})
            candidate_email = candidate.get("email")
            candidate_name = candidate.get("full_name", "Candidate")
            
            if not candidate_email:
                continue
            
            # Check if candidate was interviewed
            if candidate_id not in interviewed_candidate_ids:
                # CV Rejection: Applied but never interviewed
                background_tasks.add_task(
                    send_cv_rejection_email,
                    candidate_email=candidate_email,
                    candidate_name=candidate_name,
                    job_title=job_title,
                    job_id=job_id,
                    recruiter_id=recruiter_id,
                    application_id=application["id"]
                )
                cv_rejection_count += 1
            elif candidate_id not in accepted_candidate_ids:
                # Interview Rejection: Interviewed but not accepted
                interview = interview_data.get(candidate_id, {})
                interview_date = interview.get("completed_at")
                
                background_tasks.add_task(
                    send_interview_rejection_email,
                    candidate_email=candidate_email,
                    candidate_name=candidate_name,
                    job_title=job_title,
                    job_id=job_id,
                    recruiter_id=recruiter_id,
                    interview_id=interview.get("id", job_id),  # Fallback to job_id if interview ID missing
                    interview_date=interview_date
                )
                interview_rejection_count += 1
        
        logger.info(
            "Rejection emails scheduled",
            job_id=str(job_id),
            cv_rejections=cv_rejection_count,
            interview_rejections=interview_rejection_count,
            total_candidates=len(applications)
        )
        
        return Response(
            success=True,
            message=f"Scheduled {cv_rejection_count + interview_rejection_count} rejection emails to be sent",
            data={
                "cv_rejections_sent": cv_rejection_count,
                "interview_rejections_sent": interview_rejection_count,
                "total_candidates": len(applications),
                "total_emails_scheduled": cv_rejection_count + interview_rejection_count
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error sending rejection emails", error=str(e), job_id=str(job_id), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send rejection emails: {str(e)}"
        )

