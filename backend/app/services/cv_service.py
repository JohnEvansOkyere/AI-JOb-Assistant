"""
CV Service
Business logic for CV operations including upload and parsing
"""

from typing import Optional, Dict, Any
from uuid import UUID
from app.models.cv import CV, CVCreate, CVUpdate
from app.database import db
from app.utils.errors import NotFoundError
import structlog
import os

logger = structlog.get_logger()


class CVService:
    """Service for managing CVs"""
    
    @staticmethod
    async def upload_cv(
        candidate_id: UUID,
        file_name: str,
        file_path: str,
        file_size: int,
        mime_type: str,
        job_description_id: Optional[UUID] = None
    ) -> dict:
        """
        Upload a CV file
        
        Args:
            candidate_id: Candidate ID
            file_name: Original file name
            file_path: Storage path
            file_size: File size in bytes
            mime_type: MIME type
            job_description_id: Optional job description ID
        
        Returns:
            Created CV record
        """
        try:
            cv_data = {
                "candidate_id": str(candidate_id),
                "file_name": file_name,
                "file_path": file_path,
                "file_size": file_size,
                "mime_type": mime_type,
            }
            
            if job_description_id:
                cv_data["job_description_id"] = str(job_description_id)
            
            response = db.service_client.table("cvs").insert(cv_data).execute()
            
            if not response.data:
                raise NotFoundError("CV", "creation failed")
            
            logger.info("CV uploaded", cv_id=response.data[0]["id"], candidate_id=str(candidate_id))
            return response.data[0]
            
        except Exception as e:
            logger.error("Error uploading CV", error=str(e))
            raise
    
    @staticmethod
    async def get_cv(cv_id: UUID) -> dict:
        """
        Get a CV by ID
        
        Args:
            cv_id: CV ID
        
        Returns:
            CV data
        
        Raises:
            NotFoundError: If CV not found
        """
        try:
            response = db.service_client.table("cvs").select("*").eq("id", str(cv_id)).execute()
            
            if not response.data:
                raise NotFoundError("CV", str(cv_id))
            
            return response.data[0]
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Error fetching CV", error=str(e), cv_id=str(cv_id))
            raise
    
    @staticmethod
    async def update_cv_parsing(
        cv_id: UUID,
        parsed_text: str,
        parsed_json: Optional[Dict[str, Any]] = None
    ) -> dict:
        """
        Update CV with parsed content
        
        Args:
            cv_id: CV ID
            parsed_text: Extracted text from CV
            parsed_json: Structured CV data
        
        Returns:
            Updated CV record
        """
        try:
            update_data = {
                "parsed_text": parsed_text,
            }
            
            if parsed_json:
                update_data["parsed_json"] = parsed_json
            
            response = db.service_client.table("cvs").update(update_data).eq("id", str(cv_id)).execute()
            
            if not response.data:
                raise NotFoundError("CV", str(cv_id))
            
            logger.info("CV parsing updated", cv_id=str(cv_id))
            return response.data[0]
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Error updating CV parsing", error=str(e), cv_id=str(cv_id))
            raise
    
    @staticmethod
    async def list_cvs_for_job(job_description_id: UUID) -> list:
        """
        List CVs for a specific job
        
        Args:
            job_description_id: Job description ID
        
        Returns:
            List of CVs
        """
        try:
            response = db.service_client.table("cvs").select("*").eq("job_description_id", str(job_description_id)).order("uploaded_at", desc=True).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error("Error listing CVs", error=str(e), job_id=str(job_description_id))
            raise

