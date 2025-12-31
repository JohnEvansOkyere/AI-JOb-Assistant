"""
AI Usage Context Helper
Helper functions to get context IDs for AI usage logging
"""

from typing import Optional, Dict, Any
from uuid import UUID
from app.database import db
import structlog

logger = structlog.get_logger()


async def get_interview_context(interview_id: UUID) -> Dict[str, Optional[UUID]]:
    """
    Get context IDs (recruiter_id, job_description_id, candidate_id) from interview_id
    
    Args:
        interview_id: Interview ID
    
    Returns:
        Dictionary with recruiter_id, job_description_id, candidate_id
    """
    try:
        interview_response = (
            db.service_client.table("interviews")
            .select("job_description_id, candidate_id")
            .eq("id", str(interview_id))
            .execute()
        )
        
        if not interview_response.data:
            return {
                "recruiter_id": None,
                "job_description_id": None,
                "candidate_id": None,
            }
        
        interview = interview_response.data[0]
        job_description_id = UUID(interview["job_description_id"])
        candidate_id = UUID(interview["candidate_id"])
        
        # Get recruiter_id from job_description
        job_response = (
            db.service_client.table("job_descriptions")
            .select("recruiter_id")
            .eq("id", str(job_description_id))
            .execute()
        )
        
        recruiter_id = None
        if job_response.data:
            recruiter_id = UUID(job_response.data[0]["recruiter_id"])
        
        return {
            "recruiter_id": recruiter_id,
            "job_description_id": job_description_id,
            "candidate_id": candidate_id,
        }
    except Exception as e:
        logger.warning("Failed to get interview context", error=str(e), interview_id=str(interview_id))
        return {
            "recruiter_id": None,
            "job_description_id": None,
            "candidate_id": None,
        }


async def get_job_context(job_description_id: UUID) -> Dict[str, Optional[UUID]]:
    """
    Get recruiter_id from job_description_id
    
    Args:
        job_description_id: Job description ID
    
    Returns:
        Dictionary with recruiter_id
    """
    try:
        job_response = (
            db.service_client.table("job_descriptions")
            .select("recruiter_id")
            .eq("id", str(job_description_id))
            .execute()
        )
        
        recruiter_id = None
        if job_response.data:
            recruiter_id = UUID(job_response.data[0]["recruiter_id"])
        
        return {
            "recruiter_id": recruiter_id,
        }
    except Exception as e:
        logger.warning("Failed to get job context", error=str(e), job_description_id=str(job_description_id))
        return {
            "recruiter_id": None,
        }


async def get_application_context(application_id: UUID) -> Dict[str, Optional[UUID]]:
    """
    Get context IDs (recruiter_id, job_description_id, candidate_id) from application_id
    
    Args:
        application_id: Application ID
    
    Returns:
        Dictionary with recruiter_id, job_description_id, candidate_id
    """
    try:
        application_response = (
            db.service_client.table("job_applications")
            .select("job_description_id, candidate_id")
            .eq("id", str(application_id))
            .execute()
        )
        
        if not application_response.data:
            return {
                "recruiter_id": None,
                "job_description_id": None,
                "candidate_id": None,
            }
        
        application = application_response.data[0]
        job_description_id = UUID(application["job_description_id"])
        candidate_id = UUID(application["candidate_id"])
        
        # Get recruiter_id from job_description
        job_response = (
            db.service_client.table("job_descriptions")
            .select("recruiter_id")
            .eq("id", str(job_description_id))
            .execute()
        )
        
        recruiter_id = None
        if job_response.data:
            recruiter_id = UUID(job_response.data[0]["recruiter_id"])
        
        return {
            "recruiter_id": recruiter_id,
            "job_description_id": job_description_id,
            "candidate_id": candidate_id,
        }
    except Exception as e:
        logger.warning("Failed to get application context", error=str(e), application_id=str(application_id))
        return {
            "recruiter_id": None,
            "job_description_id": None,
            "candidate_id": None,
        }

