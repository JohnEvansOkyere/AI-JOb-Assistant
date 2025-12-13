"""
Interview Service
Business logic for interview session management
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models.interview import Interview, InterviewCreate, InterviewUpdate
from app.database import db
from app.utils.errors import NotFoundError, ForbiddenError
from app.services.ticket_service import TicketService
import structlog

logger = structlog.get_logger()


class InterviewService:
    """Service for managing interviews"""
    
    @staticmethod
    async def create_interview_from_ticket(ticket_code: str) -> dict:
        """
        Create an interview session from a validated ticket
        
        Args:
            ticket_code: Valid ticket code
        
        Returns:
            Created interview session
        
        Raises:
            NotFoundError: If ticket not found
            ForbiddenError: If ticket is invalid
        """
        try:
            # Validate ticket
            ticket = await TicketService.validate_ticket(ticket_code)
            
            # Mark ticket as used
            await TicketService.mark_ticket_used(UUID(ticket["id"]))
            
            # Create interview
            interview_data = {
                "candidate_id": ticket["candidate_id"],
                "job_description_id": ticket["job_description_id"],
                "ticket_id": ticket["id"],
                "status": "pending"
            }
            
            response = db.client.table("interviews").insert(interview_data).execute()
            
            if not response.data:
                raise NotFoundError("Interview", "creation failed")
            
            logger.info("Interview created", interview_id=response.data[0]["id"], ticket_code=ticket_code)
            return response.data[0]
            
        except (NotFoundError, ForbiddenError):
            raise
        except Exception as e:
            logger.error("Error creating interview", error=str(e), ticket_code=ticket_code)
            raise
    
    @staticmethod
    async def get_interview(interview_id: UUID) -> dict:
        """
        Get an interview by ID
        
        Args:
            interview_id: Interview ID
        
        Returns:
            Interview data
        
        Raises:
            NotFoundError: If interview not found
        """
        try:
            response = db.client.table("interviews").select("*").eq("id", str(interview_id)).execute()
            
            if not response.data:
                raise NotFoundError("Interview", str(interview_id))
            
            return response.data[0]
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Error fetching interview", error=str(e), interview_id=str(interview_id))
            raise
    
    @staticmethod
    async def start_interview(interview_id: UUID) -> dict:
        """
        Start an interview session
        
        Args:
            interview_id: Interview ID
        
        Returns:
            Updated interview data
        """
        try:
            interview = await InterviewService.get_interview(interview_id)
            
            if interview["status"] != "pending":
                raise ForbiddenError(f"Interview is already {interview['status']}")
            
            update_data = {
                "status": "in_progress",
                "started_at": datetime.utcnow().isoformat()
            }
            
            response = db.client.table("interviews").update(update_data).eq("id", str(interview_id)).execute()
            
            if not response.data:
                raise NotFoundError("Interview", str(interview_id))
            
            logger.info("Interview started", interview_id=str(interview_id))
            return response.data[0]
            
        except (NotFoundError, ForbiddenError):
            raise
        except Exception as e:
            logger.error("Error starting interview", error=str(e), interview_id=str(interview_id))
            raise
    
    @staticmethod
    async def complete_interview(
        interview_id: UUID,
        transcript: Optional[str] = None,
        audio_file_path: Optional[str] = None
    ) -> dict:
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
            interview = await InterviewService.get_interview(interview_id)
            
            if interview["status"] not in ["in_progress", "pending"]:
                raise ForbiddenError(f"Cannot complete interview with status {interview['status']}")
            
            # Calculate duration
            started_at = datetime.fromisoformat(interview["started_at"].replace('Z', '+00:00')) if interview.get("started_at") else datetime.utcnow()
            completed_at = datetime.utcnow()
            duration_seconds = int((completed_at - started_at.replace(tzinfo=None)).total_seconds())
            
            update_data = {
                "status": "completed",
                "completed_at": completed_at.isoformat(),
                "duration_seconds": duration_seconds
            }
            
            if transcript:
                update_data["transcript"] = transcript
            
            if audio_file_path:
                update_data["audio_file_path"] = audio_file_path
            
            response = db.client.table("interviews").update(update_data).eq("id", str(interview_id)).execute()
            
            if not response.data:
                raise NotFoundError("Interview", str(interview_id))
            
            logger.info("Interview completed", interview_id=str(interview_id), duration=duration_seconds)
            return response.data[0]
            
        except (NotFoundError, ForbiddenError):
            raise
        except Exception as e:
            logger.error("Error completing interview", error=str(e), interview_id=str(interview_id))
            raise
    
    @staticmethod
    async def list_interviews_for_job(job_description_id: UUID, recruiter_id: UUID) -> list:
        """
        List interviews for a job description
        
        Args:
            job_description_id: Job description ID
            recruiter_id: Recruiter ID (for authorization)
        
        Returns:
            List of interviews
        """
        try:
            # Verify recruiter owns the job (use service client to bypass RLS)
            job = db.service_client.table("job_descriptions").select("id").eq("id", str(job_description_id)).eq("recruiter_id", str(recruiter_id)).execute()
            
            if not job.data:
                raise NotFoundError("Job description", str(job_description_id))
            
            response = db.client.table("interviews").select("*").eq("job_description_id", str(job_description_id)).order("created_at", desc=True).execute()
            
            return response.data or []
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Error listing interviews", error=str(e), job_id=str(job_description_id))
            raise

