"""
Interview API Routes
Handles interview management and operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Optional
from uuid import UUID
from app.schemas.common import Response
from app.models.interview import Interview, InterviewUpdate
from app.services.interview_service import InterviewService
from app.utils.auth import get_current_user_id, get_current_user
from app.database import db
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.get("", response_model=Response[list])
async def list_interviews(
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    List all interviews for the current recruiter across all their jobs
    
    Args:
        recruiter_id: Current user ID (for authorization)
    
    Returns:
        List of interviews with candidate and report data
    """
    try:
        interviews = await InterviewService.list_interviews_with_reports_for_recruiter(recruiter_id)
        return Response(
            success=True,
            message=f"Found {len(interviews)} interviews",
            data=interviews
        )
    except Exception as e:
        logger.error("Error listing interviews", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{interview_id}/job-status", response_model=Response[dict])
async def update_interview_job_status(
    interview_id: UUID,
    job_status: str = Body(..., embed=True),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Update the job status for an interview (e.g., 'accepted', 'rejected', 'on_hold')
    
    Args:
        interview_id: Interview ID
        job_status: New job status
        recruiter_id: Current user ID (for authorization)
    
    Returns:
        Updated interview data
    """
    try:
        # Verify recruiter owns the job for this interview
        interview = await InterviewService.get_interview(interview_id)
        job_id = interview.get("job_description_id")
        
        # Check if recruiter owns this job
        job_response = db.service_client.table("job_descriptions").select("recruiter_id").eq("id", str(job_id)).execute()
        if not job_response.data or str(job_response.data[0]["recruiter_id"]) != str(recruiter_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this interview"
            )
        
        # Update interview job_status
        update_data = InterviewUpdate(job_status=job_status)
        updated_interview = await InterviewService.update_interview(interview_id, update_data)
        
        logger.info(
            "Interview job status updated",
            interview_id=str(interview_id),
            job_status=job_status,
            recruiter_id=str(recruiter_id)
        )
        
        return Response(
            success=True,
            message="Interview job status updated successfully",
            data=updated_interview
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating interview job status", error=str(e))
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
    List all interviews for a specific job
    
    Args:
        job_description_id: Job description ID
        recruiter_id: Current user ID (for authorization)
    
    Returns:
        List of interviews with candidate and report data
    """
    try:
        interviews = await InterviewService.list_interviews_for_job(job_description_id, recruiter_id)
        return Response(
            success=True,
            message=f"Found {len(interviews)} interviews",
            data=interviews
        )
    except Exception as e:
        logger.error("Error listing interviews", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{interview_id}/replay", response_model=Response[dict])
async def get_interview_replay(
    interview_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Get interview replay data with ordered questions and responses
    
    Returns interview data with:
    - Interview metadata (candidate, job, date, etc.)
    - Questions ordered by order_index with audio paths
    - Responses with transcripts and audio paths
    
    Args:
        interview_id: Interview ID
        recruiter_id: Current user ID (for authorization)
    
    Returns:
        Interview replay data with ordered Q&A
    """
    try:
        # Get interview and verify recruiter owns the job
        interview = await InterviewService.get_interview(interview_id)
        job_id = interview.get("job_description_id")
        
        # Check if recruiter owns this job
        job_response = db.service_client.table("job_descriptions").select("recruiter_id, title").eq("id", str(job_id)).execute()
        if not job_response.data or str(job_response.data[0]["recruiter_id"]) != str(recruiter_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this interview"
            )
        job_title = job_response.data[0].get("title", "")
        
        # Get candidate info
        candidate_response = db.service_client.table("candidates").select("id, full_name, email").eq("id", str(interview["candidate_id"])).execute()
        candidate = candidate_response.data[0] if candidate_response.data else {}
        
        # Get responses first to identify which questions were actually asked
        responses_response = (
            db.service_client.table("interview_responses")
            .select("id, question_id, response_text, response_audio_path, created_at")
            .eq("interview_id", str(interview_id))
            .execute()
        )
        responses = {r["question_id"]: r for r in (responses_response.data or [])}
        
        # Only fetch questions that have responses (were actually asked)
        question_ids_with_responses = list(responses.keys())
        if not question_ids_with_responses:
            # If no responses, return empty list (interview not started)
            qa_items = []
        else:
            # Get only questions that have responses
            questions_response = (
                db.service_client.table("interview_questions")
                .select("id, question_text, order_index, question_type")
                .eq("interview_id", str(interview_id))
                .in_("id", question_ids_with_responses)
                .order("order_index")
                .execute()
            )
            questions = questions_response.data or []
            
            # Combine questions with responses (only questions that were asked)
            qa_items = []
            for q in questions:
                q_id = q["id"]
                response = responses.get(q_id, {})
            
            # Get audio URL if audio path exists (use signed URL for private buckets)
            audio_url = None
            if response.get("response_audio_path"):
                from app.services.storage_service import StorageService
                # Generate signed URL (valid for 1 hour) - works with both public and private buckets
                audio_url = StorageService.get_audio_signed_url(response["response_audio_path"], expires_in=3600)
            
            qa_items.append({
                "question_id": q_id,
                "question_text": q.get("question_text", ""),
                "question_order": q.get("order_index", 0) + 1,  # 1-based for display
                "question_type": q.get("question_type"),
                "response_text": response.get("response_text", ""),
                "response_audio_path": response.get("response_audio_path"),
                "response_audio_url": audio_url,
                "response_created_at": response.get("created_at"),
            })
        
        replay_data = {
            "interview_id": str(interview_id),
            "interview_status": interview.get("status"),
            "interview_mode": interview.get("interview_mode", "text"),
            "started_at": interview.get("started_at"),
            "completed_at": interview.get("completed_at"),
            "duration_seconds": interview.get("duration_seconds"),
            "candidate": {
                "id": candidate.get("id"),
                "full_name": candidate.get("full_name", "Unknown"),
                "email": candidate.get("email", ""),
            },
            "job": {
                "id": str(job_id),
                "title": job_title,
            },
            "questions_and_responses": qa_items,
        }
        
        return Response(
            success=True,
            message="Interview replay data retrieved successfully",
            data=replay_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching interview replay", error=str(e), interview_id=str(interview_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch interview replay: {str(e)}"
        )
