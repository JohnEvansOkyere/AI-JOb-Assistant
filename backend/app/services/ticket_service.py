"""
Interview Ticket Service
Business logic for interview ticket generation and validation
"""

from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from app.models.interview_ticket import InterviewTicket, InterviewTicketCreate
from app.database import db
from app.utils.errors import NotFoundError, ForbiddenError
import structlog
import secrets
import string

logger = structlog.get_logger()


class TicketService:
    """Service for managing interview tickets"""
    
    @staticmethod
    def generate_ticket_code() -> str:
        """
        Generate a unique ticket code
        
        Returns:
            Unique 12-character ticket code
        """
        # Use uppercase letters and numbers, excluding ambiguous characters
        chars = string.ascii_uppercase.replace('I', '').replace('O', '') + string.digits.replace('0', '').replace('1', '')
        return ''.join(secrets.choice(chars) for _ in range(12))
    
    @staticmethod
    async def create_ticket(
        candidate_id: UUID,
        job_description_id: UUID,
        created_by: UUID,
        expires_in_hours: Optional[int] = None
    ) -> dict:
        """
        Create a new interview ticket
        
        Args:
            candidate_id: Candidate ID
            job_description_id: Job description ID
            created_by: Recruiter ID who created the ticket
            expires_in_hours: Optional expiration time in hours
        
        Returns:
            Created ticket with ticket code
        """
        try:
            # Generate unique ticket code
            ticket_code = TicketService.generate_ticket_code()
            
            # Check for uniqueness (retry if collision)
            max_retries = 5
            for _ in range(max_retries):
                existing = db.client.table("interview_tickets").select("id").eq("ticket_code", ticket_code).execute()
                if not existing.data:
                    break
                ticket_code = TicketService.generate_ticket_code()
            else:
                raise Exception("Failed to generate unique ticket code")
            
            # Calculate expiration
            expires_at = None
            if expires_in_hours:
                expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
            
            ticket_data = {
                "candidate_id": str(candidate_id),
                "job_description_id": str(job_description_id),
                "ticket_code": ticket_code,
                "is_used": False,
                "is_expired": False,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "created_by": str(created_by)
            }
            
            response = db.client.table("interview_tickets").insert(ticket_data).execute()
            
            if not response.data:
                raise NotFoundError("Interview ticket", "creation failed")
            
            logger.info("Ticket created", ticket_id=response.data[0]["id"], ticket_code=ticket_code)
            return response.data[0]
            
        except Exception as e:
            logger.error("Error creating ticket", error=str(e))
            raise
    
    @staticmethod
    async def validate_ticket(ticket_code: str) -> dict:
        """
        Validate an interview ticket
        
        Args:
            ticket_code: Ticket code to validate
        
        Returns:
            Ticket data if valid
        
        Raises:
            NotFoundError: If ticket not found
            ForbiddenError: If ticket is used or expired
        """
        try:
            response = db.client.table("interview_tickets").select("*").eq("ticket_code", ticket_code).execute()
            
            if not response.data:
                raise NotFoundError("Interview ticket", ticket_code)
            
            ticket = response.data[0]
            
            # Check if already used
            if ticket.get("is_used"):
                raise ForbiddenError("This ticket has already been used")
            
            # Check if expired
            if ticket.get("is_expired"):
                raise ForbiddenError("This ticket has expired")
            
            # Check expiration date
            if ticket.get("expires_at"):
                expires_at = datetime.fromisoformat(ticket["expires_at"].replace('Z', '+00:00'))
                if datetime.utcnow() > expires_at.replace(tzinfo=None):
                    # Mark as expired
                    db.client.table("interview_tickets").update({"is_expired": True}).eq("id", ticket["id"]).execute()
                    raise ForbiddenError("This ticket has expired")
            
            logger.info("Ticket validated", ticket_code=ticket_code)
            return ticket
            
        except (NotFoundError, ForbiddenError):
            raise
        except Exception as e:
            logger.error("Error validating ticket", error=str(e), ticket_code=ticket_code)
            raise
    
    @staticmethod
    async def mark_ticket_used(ticket_id: UUID) -> bool:
        """
        Mark a ticket as used
        
        Args:
            ticket_id: Ticket ID
        
        Returns:
            True if successful
        """
        try:
            response = db.client.table("interview_tickets").update({
                "is_used": True,
                "used_at": datetime.utcnow().isoformat()
            }).eq("id", str(ticket_id)).execute()
            
            logger.info("Ticket marked as used", ticket_id=str(ticket_id))
            return True
            
        except Exception as e:
            logger.error("Error marking ticket as used", error=str(e), ticket_id=str(ticket_id))
            raise
    
    @staticmethod
    async def get_tickets_for_job(job_description_id: UUID, recruiter_id: UUID) -> list:
        """
        Get all tickets for a job description
        
        Args:
            job_description_id: Job description ID
            recruiter_id: Recruiter ID (for authorization)
        
        Returns:
            List of tickets
        """
        try:
            # Verify recruiter owns the job (use service client to bypass RLS)
            job = db.service_client.table("job_descriptions").select("id").eq("id", str(job_description_id)).eq("recruiter_id", str(recruiter_id)).execute()
            
            if not job.data:
                raise NotFoundError("Job description", str(job_description_id))
            
            response = db.client.table("interview_tickets").select("*").eq("job_description_id", str(job_description_id)).order("created_at", desc=True).execute()
            
            return response.data or []
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Error fetching tickets", error=str(e), job_id=str(job_description_id))
            raise

