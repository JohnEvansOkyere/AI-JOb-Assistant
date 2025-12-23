"""
Job Application Service
Business logic for job applications
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.models.job_application import JobApplication, JobApplicationCreate, JobApplicationUpdate
from app.models.candidate import Candidate, CandidateCreate
from app.database import db
from app.utils.errors import NotFoundError
from app.services.cv_service import CVService
import structlog

logger = structlog.get_logger()


class ApplicationService:
    """Service for managing job applications"""
    
    @staticmethod
    async def create_application(
        application_data: JobApplicationCreate,
        cv_file_name: str,
        cv_file_path: str,
        cv_file_size: int,
        cv_mime_type: str,
        cv_text: str
    ) -> dict:
        """
        Create a job application with CV
        
        Args:
            application_data: Application data
            cv_file_name: CV file name
            cv_file_path: CV storage path
            cv_file_size: CV file size
            cv_mime_type: CV MIME type
            cv_text: Parsed CV text
        
        Returns:
            Created application
        """
        try:
            # Find or create candidate
            candidate = db.service_client.table("candidates").select("*").eq("email", application_data.email).execute()
            
            if candidate.data:
                candidate_id = UUID(candidate.data[0]["id"])
            else:
                # Create new candidate
                candidate_data = CandidateCreate(
                    email=application_data.email,
                    full_name=application_data.full_name,
                    phone=application_data.phone
                )
                candidate_result = db.service_client.table("candidates").insert(
                    candidate_data.model_dump()
                ).execute()
                candidate_id = UUID(candidate_result.data[0]["id"])
            
            # Upload CV
            cv = await CVService.upload_cv(
                candidate_id=candidate_id,
                file_name=cv_file_name,
                file_path=cv_file_path,
                file_size=cv_file_size,
                mime_type=cv_mime_type,
                job_description_id=application_data.job_description_id
            )
            
            # Update CV with parsed text
            if cv_text:
                await CVService.update_cv_parsing(
                    cv_id=UUID(cv["id"]),
                    parsed_text=cv_text
                )
            
            # Create application
            # Generate UUID for the application
            import uuid
            from datetime import datetime
            application_id = str(uuid.uuid4())
            
            # Check if application already exists (UNIQUE constraint: job_description_id, candidate_id)
            # Fetch full record so API response validation has all required fields
            existing = db.service_client.table("job_applications").select("*").eq(
                "job_description_id", str(application_data.job_description_id)
            ).eq("candidate_id", str(candidate_id)).execute()
            
            if existing.data:
                record = existing.data[0]
                
                # Ensure timestamps exist for Pydantic response model
                if "created_at" not in record or record.get("created_at") is None:
                    logger.warning(
                        "created_at missing from existing application record, setting explicitly",
                        application_id=record.get("id"),
                    )
                    record["created_at"] = datetime.utcnow().isoformat()
                
                if "updated_at" not in record or record.get("updated_at") is None:
                    logger.warning(
                        "updated_at missing from existing application record, setting explicitly",
                        application_id=record.get("id"),
                    )
                    record["updated_at"] = datetime.utcnow().isoformat()
                
                logger.info(
                    "Application already exists, returning existing record",
                    application_id=record.get("id"),
                    job_id=str(application_data.job_description_id),
                    candidate_id=str(candidate_id),
                )
                return record
            
            application_dict = {
                "id": application_id,
                "job_description_id": str(application_data.job_description_id),
                "candidate_id": str(candidate_id),
                "cv_id": cv["id"],
                "cover_letter": application_data.cover_letter,
                "status": "pending",
                "applied_at": datetime.utcnow().isoformat()  # Explicitly set applied_at
            }
            
            logger.info("Creating job application", 
                       application_id=application_id,
                       job_id=str(application_data.job_description_id),
                       candidate_id=str(candidate_id),
                       cv_id=cv["id"])
            
            response = db.service_client.table("job_applications").insert(application_dict).execute()
            
            if not response.data:
                logger.error("Application insert returned no data", application_dict=application_dict)
                raise NotFoundError("Job application", "creation failed - no data returned")
            
            # Fetch the full record to ensure we have created_at and updated_at timestamps
            # Supabase insert might not return all fields, especially timestamps
            application_id = response.data[0]["id"]
            full_record = db.service_client.table("job_applications").select("*").eq("id", application_id).execute()
            
            if not full_record.data:
                logger.error("Failed to fetch full application record after insert", application_id=application_id)
                raise NotFoundError("Job application", "creation failed - could not fetch full record")
            
            record = full_record.data[0]
            
            # Log what fields we got back
            logger.info("Fetched application record", 
                       application_id=record.get("id"),
                       has_created_at="created_at" in record,
                       has_updated_at="updated_at" in record,
                       fields=list(record.keys()))
            
            # Ensure created_at and updated_at exist - if not, set them explicitly
            # This handles cases where Supabase doesn't return these fields even with select("*")
            if "created_at" not in record or record.get("created_at") is None:
                logger.warning("created_at missing from fetched record, setting explicitly", application_id=application_id)
                record["created_at"] = datetime.utcnow().isoformat()
            
            if "updated_at" not in record or record.get("updated_at") is None:
                logger.warning("updated_at missing from fetched record, setting explicitly", application_id=application_id)
                record["updated_at"] = datetime.utcnow().isoformat()
            
            logger.info("Application created successfully", 
                       application_id=record["id"], 
                       job_id=str(application_data.job_description_id),
                       candidate_id=str(candidate_id))
            return record
            
        except Exception as e:
            logger.error("Error creating application", error=str(e), exc_info=True, 
                        job_id=str(application_data.job_description_id) if 'application_data' in locals() else None,
                        candidate_id=str(candidate_id) if 'candidate_id' in locals() else None)
            raise
    
    @staticmethod
    async def get_application(application_id: UUID) -> dict:
        """Get application by ID"""
        try:
            response = db.service_client.table("job_applications").select("*").eq("id", str(application_id)).execute()
            if not response.data:
                raise NotFoundError("Job application", str(application_id))
            return response.data[0]
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Error fetching application", error=str(e))
            raise
    
    @staticmethod
    async def list_applications_for_job(
        job_description_id: UUID,
        recruiter_id: UUID,
        status: Optional[str] = None
    ) -> List[dict]:
        """
        List applications for a job
        
        Args:
            job_description_id: Job description ID
            recruiter_id: Recruiter ID (for authorization)
            status: Optional status filter
        
        Returns:
            List of applications
        """
        try:
            # Verify recruiter owns the job
            job = db.service_client.table("job_descriptions").select("id").eq("id", str(job_description_id)).eq("recruiter_id", str(recruiter_id)).execute()
            if not job.data:
                logger.warning("Job not found or not owned by recruiter", 
                              job_id=str(job_description_id), 
                              recruiter_id=str(recruiter_id))
                raise NotFoundError("Job description", str(job_description_id))
            
            query = db.service_client.table("job_applications").select("*, candidates!inner(*), cvs(*)").eq("job_description_id", str(job_description_id))
            
            if status:
                query = query.eq("status", status)
            
            query = query.order("applied_at", desc=True)
            response = query.execute()
            
            return response.data or []
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Error listing applications", error=str(e))
            raise
    
    @staticmethod
    async def update_application_status(
        application_id: UUID,
        status: str,
        recruiter_id: UUID
    ) -> dict:
        """
        Update application status
        
        Args:
            application_id: Application ID
            status: New status
            recruiter_id: Recruiter ID (for authorization)
        
        Returns:
            Updated application
        """
        try:
            # Verify recruiter has access
            app = await ApplicationService.get_application(application_id)
            job = db.service_client.table("job_descriptions").select("recruiter_id").eq("id", app["job_description_id"]).execute()
            
            if not job.data or str(job.data[0]["recruiter_id"]) != str(recruiter_id):
                raise NotFoundError("Job application", str(application_id))
            
            response = db.service_client.table("job_applications").update({
                "status": status
            }).eq("id", str(application_id)).execute()
            
            if not response.data:
                raise NotFoundError("Job application", str(application_id))
            
            logger.info("Application status updated", application_id=str(application_id), status=status)
            return response.data[0]
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Error updating application", error=str(e))
            raise

