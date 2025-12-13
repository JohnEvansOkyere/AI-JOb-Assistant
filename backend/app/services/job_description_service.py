"""
Job Description Service
Business logic for job description operations
"""

from typing import List, Optional
from uuid import UUID
from app.models.job_description import JobDescription, JobDescriptionCreate, JobDescriptionUpdate
from app.database import db
from app.utils.errors import NotFoundError
import structlog

logger = structlog.get_logger()


class JobDescriptionService:
    """Service for managing job descriptions"""
    
    @staticmethod
    async def create_job_description(
        recruiter_id: UUID,
        job_data: JobDescriptionCreate
    ) -> dict:
        """
        Create a new job description
        
        Args:
            recruiter_id: ID of the recruiter creating the job
            job_data: Job description data
        
        Returns:
            Created job description
        """
        try:
            job_dict = job_data.model_dump()
            job_dict["recruiter_id"] = str(recruiter_id)
            
            # Use service client to bypass RLS (we've already validated authorization in the API layer)
            response = db.service_client.table("job_descriptions").insert(job_dict).execute()
            
            if not response.data:
                raise NotFoundError("Job description", "creation failed")
            
            logger.info("Job description created", job_id=response.data[0]["id"], recruiter_id=str(recruiter_id))
            return response.data[0]
            
        except Exception as e:
            logger.error("Error creating job description", error=str(e), recruiter_id=str(recruiter_id))
            raise
    
    @staticmethod
    async def get_job_description(job_id: UUID, recruiter_id: UUID) -> dict:
        """
        Get a job description by ID
        
        Args:
            job_id: Job description ID
            recruiter_id: Recruiter ID (for authorization)
        
        Returns:
            Job description data
        
        Raises:
            NotFoundError: If job not found or not owned by recruiter
        """
        try:
            response = db.client.table("job_descriptions").select("*").eq("id", str(job_id)).eq("recruiter_id", str(recruiter_id)).execute()
            
            if not response.data:
                raise NotFoundError("Job description", str(job_id))
            
            return response.data[0]
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Error fetching job description", error=str(e), job_id=str(job_id))
            raise
    
    @staticmethod
    async def list_job_descriptions(
        recruiter_id: UUID,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """
        List job descriptions for a recruiter
        
        Args:
            recruiter_id: Recruiter ID
            is_active: Filter by active status
            limit: Maximum number of results
            offset: Offset for pagination
        
        Returns:
            List of job descriptions
        """
        try:
            query = db.client.table("job_descriptions").select("*").eq("recruiter_id", str(recruiter_id))
            
            if is_active is not None:
                query = query.eq("is_active", is_active)
            
            query = query.order("created_at", desc=True).limit(limit).offset(offset)
            response = query.execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error("Error listing job descriptions", error=str(e))
            raise
    
    @staticmethod
    async def update_job_description(
        job_id: UUID,
        recruiter_id: UUID,
        job_data: JobDescriptionUpdate
    ) -> dict:
        """
        Update a job description
        
        Args:
            job_id: Job description ID
            recruiter_id: Recruiter ID (for authorization)
            job_data: Updated job description data
        
        Returns:
            Updated job description
        
        Raises:
            NotFoundError: If job not found or not owned by recruiter
        """
        try:
            # Verify ownership
            await JobDescriptionService.get_job_description(job_id, recruiter_id)
            
            # Update (use service client to bypass RLS - we've already verified ownership)
            update_data = job_data.model_dump(exclude_unset=True)
            response = db.service_client.table("job_descriptions").update(update_data).eq("id", str(job_id)).execute()
            
            if not response.data:
                raise NotFoundError("Job description", str(job_id))
            
            logger.info("Job description updated", job_id=str(job_id))
            return response.data[0]
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Error updating job description", error=str(e), job_id=str(job_id))
            raise
    
    @staticmethod
    async def delete_job_description(job_id: UUID, recruiter_id: UUID) -> bool:
        """
        Delete a job description
        
        Args:
            job_id: Job description ID
            recruiter_id: Recruiter ID (for authorization)
        
        Returns:
            True if deleted successfully
        
        Raises:
            NotFoundError: If job not found or not owned by recruiter
        """
        try:
            # Verify ownership
            await JobDescriptionService.get_job_description(job_id, recruiter_id)
            
            # Delete (use service client to bypass RLS - we've already verified ownership)
            response = db.service_client.table("job_descriptions").delete().eq("id", str(job_id)).execute()
            
            logger.info("Job description deleted", job_id=str(job_id))
            return True
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Error deleting job description", error=str(e), job_id=str(job_id))
            raise

