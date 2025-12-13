"""
Interview Tickets API Routes
Ticket generation and validation endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from uuid import UUID
from app.schemas.common import Response
from app.models.interview_ticket import InterviewTicket
from app.services.ticket_service import TicketService
from app.utils.auth import get_current_user_id
from app.database import db
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=Response[InterviewTicket], status_code=status.HTTP_201_CREATED)
async def create_ticket(
    candidate_id: UUID,
    job_description_id: UUID,
    expires_in_hours: Optional[int] = Query(None, description="Expiration time in hours"),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Create a new interview ticket
    
    Args:
        candidate_id: Candidate ID
        job_description_id: Job description ID
        expires_in_hours: Optional expiration time in hours
        recruiter_id: Current user ID (for authorization)
    
    Returns:
        Created ticket with ticket code
    """
    try:
        # Verify recruiter owns the job (use service client to bypass RLS)
        job = db.service_client.table("job_descriptions").select("id").eq("id", str(job_description_id)).eq("recruiter_id", str(recruiter_id)).execute()
        if not job.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job description not found"
            )
        
        ticket = await TicketService.create_ticket(
            candidate_id=candidate_id,
            job_description_id=job_description_id,
            created_by=recruiter_id,
            expires_in_hours=expires_in_hours
        )
        
        return Response(
            success=True,
            message="Ticket created successfully",
            data=ticket
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating ticket", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/validate", response_model=Response[dict])
async def validate_ticket(ticket_code: str):
    """
    Validate an interview ticket (public endpoint, no auth required)
    
    Args:
        ticket_code: Ticket code to validate
    
    Returns:
        Ticket validation result
    """
    try:
        ticket = await TicketService.validate_ticket(ticket_code)
        
        return Response(
            success=True,
            message="Ticket is valid",
            data={
                "valid": True,
                "ticket_id": ticket["id"],
                "candidate_id": ticket["candidate_id"],
                "job_description_id": ticket["job_description_id"]
            }
        )
    except Exception as e:
        logger.error("Error validating ticket", error=str(e))
        return Response(
            success=False,
            message=str(e),
            data={"valid": False}
        )


@router.get("/job/{job_description_id}", response_model=Response[list])
async def list_tickets_for_job(
    job_description_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    List all tickets for a job description
    
    Args:
        job_description_id: Job description ID
        recruiter_id: Current user ID (for authorization)
    
    Returns:
        List of tickets
    """
    try:
        tickets = await TicketService.get_tickets_for_job(job_description_id, recruiter_id)
        return Response(
            success=True,
            message="Tickets retrieved successfully",
            data=tickets
        )
    except Exception as e:
        logger.error("Error listing tickets", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

