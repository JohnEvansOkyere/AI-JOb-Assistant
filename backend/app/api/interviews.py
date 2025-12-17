"""
Interviews API Routes
Interview session management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Optional
from uuid import UUID
from app.schemas.common import Response
from app.models.interview import Interview
from app.services.interview_service import InterviewService
from app.utils.auth import get_current_user, get_current_user_id
from typing import Optional
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("/start", response_model=Response[Interview], status_code=status.HTTP_201_CREATED)
async def start_interview_from_ticket(
    ticket_code: str = Body(..., embed=True)
):
    """
    Start an interview session from a ticket code (public endpoint)
    
    Args:
        ticket_code: Valid ticket code
    
    Returns:
        Created and started interview session
    """
    try:
        interview = await InterviewService.create_interview_from_ticket(ticket_code)
        interview = await InterviewService.start_interview(UUID(interview["id"]))
        
        return Response(
            success=True,
            message="Interview started successfully",
            data=interview
        )
    except Exception as e:
        logger.error("Error starting interview", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{interview_id}/job-status", response_model=Response[dict])
async def update_interview_job_status(
    interview_id: UUID,
    job_status: str = Body(..., embed=True),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Update interview job status (accepted/rejected/under_review/pending)
    
    Args:
        interview_id: Interview ID
        job_status: New job status (accepted, rejected, under_review, pending)
        recruiter_id: Current recruiter ID
    
    Returns:
        Updated interview data
    """
    try:
        from app.database import db
        
        # Validate job_status
        valid_statuses = ['accepted', 'rejected', 'under_review', 'pending']
        if job_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid job_status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Get interview and verify recruiter owns the job
        interview_response = db.service_client.table("interviews").select(
            "id, job_description_id"
        ).eq("id", str(interview_id)).execute()
        
        if not interview_response.data:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        interview = interview_response.data[0]
        job_id = interview.get("job_description_id")
        
        # Verify recruiter owns the job
        job_response = db.service_client.table("job_descriptions").select(
            "id, recruiter_id"
        ).eq("id", str(job_id)).eq("recruiter_id", str(recruiter_id)).execute()
        
        if not job_response.data:
            raise HTTPException(status_code=403, detail="Not authorized to update this interview")
        
        # Update job_status
        update_response = db.service_client.table("interviews").update({
            "job_status": job_status
        }).eq("id", str(interview_id)).execute()
        
        if not update_response.data:
            raise HTTPException(status_code=500, detail="Failed to update interview status")
        
        return Response(
            success=True,
            message=f"Interview status updated to {job_status}",
            data=update_response.data[0]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating interview job status", error=str(e), interview_id=str(interview_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update interview status: {str(e)}"
        )


@router.get("/{interview_id}", response_model=Response[Interview])
async def get_interview(
    interview_id: UUID,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Get an interview by ID
    Can be accessed by recruiter (with auth) or candidate (via interview_id)
    
    Args:
        interview_id: Interview ID
        recruiter_id: Optional current user ID (if recruiter)
    
    Returns:
        Interview data
    """
    try:
        interview = await InterviewService.get_interview(interview_id)
        return Response(
            success=True,
            message="Interview retrieved successfully",
            data=interview
        )
    except Exception as e:
        logger.error("Error fetching interview", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{interview_id}/complete", response_model=Response[Interview])
async def complete_interview(
    interview_id: UUID,
    transcript: Optional[str] = Body(None),
    audio_file_path: Optional[str] = Body(None)
):
    """
    Complete an interview session
    
    Args:
        interview_id: Interview ID
        transcript: Interview transcript
        audio_file_path: Path to interview audio file
    
    Returns:
        Updated interview data
    """
    try:
        interview = await InterviewService.complete_interview(
            interview_id=interview_id,
            transcript=transcript,
            audio_file_path=audio_file_path
        )
        
        return Response(
            success=True,
            message="Interview completed successfully",
            data=interview
        )
    except Exception as e:
        logger.error("Error completing interview", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/job/{job_description_id}", response_model=Response[list])
async def list_interviews_for_job(
    job_description_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    List interviews for a job description
    
    Args:
        job_description_id: Job description ID
        recruiter_id: Current user ID (for authorization)
    
    Returns:
        List of interviews
    """
    try:
        interviews = await InterviewService.list_interviews_for_job(job_description_id, recruiter_id)
        return Response(
            success=True,
            message="Interviews retrieved successfully",
            data=interviews
        )
    except Exception as e:
        logger.error("Error listing interviews", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("", response_model=Response[list])
async def list_interviews_with_reports(
    recruiter_id: UUID = Depends(get_current_user_id),
):
    """
    List interviews for all jobs owned by the current recruiter, including AI report data.
    """
    try:
        interviews = await InterviewService.list_interviews_with_reports_for_recruiter(recruiter_id)
        return Response(
            success=True,
            message="Interviews with reports retrieved successfully",
            data=interviews,
        )
    except Exception as e:
        logger.error("Error listing interviews with reports", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

