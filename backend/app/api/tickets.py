"""
Interview Tickets API Routes
Ticket generation and validation endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, BackgroundTasks
from typing import Optional
from uuid import UUID
from app.schemas.common import Response
from app.models.interview_ticket import InterviewTicket
from app.services.ticket_service import TicketService
from app.services.email_service import EmailService
from app.utils.auth import get_current_user_id
from app.database import db
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=Response[InterviewTicket], status_code=status.HTTP_201_CREATED)
async def create_ticket(
    candidate_id: UUID = Body(..., description="Candidate ID"),
    job_description_id: UUID = Body(..., description="Job description ID"),
    interview_mode: str = Body("text", description="Interview mode: 'text' or 'voice'"),
    expires_in_hours: Optional[int] = Query(None, description="Expiration time in hours"),
    send_email: bool = Query(True, description="Automatically send interview invitation email"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Create a new interview ticket and optionally send invitation email
    
    Args:
        candidate_id: Candidate ID (request body)
        job_description_id: Job description ID (request body)
        interview_mode: Interview mode - 'text' or 'voice' (default: 'text')
        expires_in_hours: Optional expiration time in hours (query param)
        send_email: Whether to automatically send interview invitation email (default: true)
        background_tasks: Background tasks for email sending
        recruiter_id: Current user ID (for authorization)
    
    Returns:
        Created ticket with ticket code
    """
    try:
        # Verify recruiter owns the job (use service client to bypass RLS)
        job = db.service_client.table("job_descriptions").select("id, title").eq("id", str(job_description_id)).eq("recruiter_id", str(recruiter_id)).execute()
        if not job.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job description not found"
            )
        
        # Validate interview_mode
        if interview_mode not in ("text", "voice"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="interview_mode must be 'text' or 'voice'"
            )
        
        ticket = await TicketService.create_ticket(
            candidate_id=candidate_id,
            job_description_id=job_description_id,
            created_by=recruiter_id,
            expires_in_hours=expires_in_hours,
            interview_mode=interview_mode
        )
        
        # Automatically send interview invitation email if requested
        if send_email:
            background_tasks.add_task(
                send_interview_invitation_email,
                recruiter_id=recruiter_id,
                ticket_id=UUID(ticket["id"]),
                candidate_id=candidate_id,
                job_description_id=job_description_id
            )
        
        return Response(
            success=True,
            message="Ticket created successfully" + (" and email sent" if send_email else ""),
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


async def send_interview_invitation_email(
    recruiter_id: UUID,
    ticket_id: UUID,
    candidate_id: UUID,
    job_description_id: UUID
):
    """Background task to send interview invitation email"""
    try:
        # Fetch ticket details
        ticket_response = db.service_client.table("interview_tickets").select(
            "ticket_code, expires_at, candidate_id, job_description_id, interview_mode"
        ).eq("id", str(ticket_id)).execute()
        
        if not ticket_response.data:
            logger.error("Ticket not found for email", ticket_id=str(ticket_id))
            return
        
        ticket = ticket_response.data[0]
        ticket_code = ticket.get("ticket_code")
        
        # Fetch job details
        job_response = db.service_client.table("job_descriptions").select(
            "id, title"
        ).eq("id", str(job_description_id)).execute()
        
        if not job_response.data:
            logger.error("Job not found for email", job_id=str(job_description_id))
            return
        
        job = job_response.data[0]
        
        # Fetch candidate details
        candidate_response = db.service_client.table("candidates").select(
            "id, email, full_name"
        ).eq("id", str(candidate_id)).execute()
        
        if not candidate_response.data:
            logger.error("Candidate not found for email", candidate_id=str(candidate_id))
            return
        
        candidate = candidate_response.data[0]
        
        if not candidate.get("email"):
            logger.error("Candidate email not found", candidate_id=str(candidate_id))
            return
        
        # Calculate expires_in_hours if expires_at is set
        expires_in_hours = None
        if ticket.get("expires_at"):
            from datetime import datetime, timezone
            expires_at = datetime.fromisoformat(ticket["expires_at"].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            if expires_at > now:
                delta = expires_at - now
                expires_in_hours = int(delta.total_seconds() / 3600)
        
        # Generate interview link
        from app.config import settings
        base_url = settings.allowed_origins[0] if settings.allowed_origins else "http://localhost:3000"
        interview_link = f"{base_url}/interview/job/{job.get('id')}"
        
        await EmailService.send_ticket_email(
            recruiter_id=recruiter_id,
            candidate_id=UUID(candidate["id"]),
            ticket_code=ticket_code,
            interview_link=interview_link,
            job_title=job.get("title", "Interview"),
            candidate_name=candidate.get("full_name", "Candidate"),
            candidate_email=candidate["email"],
            ticket_id=ticket_id,
            job_description_id=job_description_id,
            expires_in_hours=expires_in_hours,
            interview_mode=ticket.get("interview_mode", "text")
        )
        logger.info("Interview invitation email sent", ticket_id=str(ticket_id), candidate_email=candidate["email"])
    except Exception as e:
        logger.error("Error sending interview invitation email", error=str(e), ticket_id=str(ticket_id))


@router.post("/validate", response_model=Response[dict])
async def validate_ticket(ticket_code: str):
    """
    Validate an interview ticket (public endpoint, no auth required)
    
    Args:
        ticket_code: Ticket code to validate
    
    Returns:
        Ticket validation result including basic candidate and job info
    """
    try:
        ticket = await TicketService.validate_ticket(ticket_code)

        # Enrich with candidate and job information for nicer candidate UX
        candidate_name = None
        job_title = None
        company_name = None

        try:
            candidate_resp = db.service_client.table("candidates").select("full_name").eq(
                "id", str(ticket["candidate_id"])
            ).execute()
            if candidate_resp.data:
                candidate_name = candidate_resp.data[0].get("full_name")
        except Exception as e:
            logger.warning(
                "Failed to load candidate for ticket validation",
                error=str(e),
                candidate_id=str(ticket.get("candidate_id")),
            )

        try:
            job_resp = db.service_client.table("job_descriptions").select(
                "id, title, recruiter_id"
            ).eq(
                "id", str(ticket["job_description_id"])
            ).execute()
            if job_resp.data:
                job_row = job_resp.data[0]
                job_title = job_row.get("title")

                # Look up recruiter/company for branding and candidate awareness
                recruiter_id = job_row.get("recruiter_id")
                if recruiter_id:
                    try:
                        # First try to load default branding (most authoritative source)
                        branding_resp = db.service_client.table("company_branding").select(
                            "company_name"
                        ).eq("recruiter_id", str(recruiter_id)).eq("is_default", True).limit(1).execute()
                        
                        if branding_resp.data and branding_resp.data[0].get("company_name"):
                            company_name = branding_resp.data[0].get("company_name")
                        else:
                            # If no default branding, try any branding for this recruiter
                            branding_resp = db.service_client.table("company_branding").select(
                                "company_name"
                            ).eq("recruiter_id", str(recruiter_id)).limit(1).execute()
                            
                            if branding_resp.data and branding_resp.data[0].get("company_name"):
                                company_name = branding_resp.data[0].get("company_name")
                        
                        # Fallback to user profile company_name only if branding doesn't have it
                        if not company_name:
                            user_resp = db.service_client.table("users").select("company_name").eq(
                                "id", str(recruiter_id)
                            ).limit(1).execute()
                            if user_resp.data and user_resp.data[0].get("company_name"):
                                company_name = user_resp.data[0].get("company_name")
                    except Exception as e:
                        logger.warning(
                            "Failed to load company for ticket validation",
                            error=str(e),
                            recruiter_id=str(recruiter_id),
                        )
        except Exception as e:
            logger.warning(
                "Failed to load job for ticket validation",
                error=str(e),
                job_id=str(ticket.get("job_description_id")),
            )
        
        return Response(
            success=True,
            message="Ticket is valid",
            data={
                "valid": True,
                "ticket_id": ticket["id"],
                "candidate_id": ticket["candidate_id"],
                "job_description_id": ticket["job_description_id"],
                "candidate_name": candidate_name,
                "job_title": job_title,
                "company_name": company_name,
                "interview_mode": ticket.get("interview_mode", "text"),  # Include interview mode
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

