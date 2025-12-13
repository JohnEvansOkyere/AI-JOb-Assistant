"""
Application Form Service
Business logic for managing custom application forms
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from app.models.application_form import (
    ApplicationFormField,
    ApplicationFormFieldCreate,
    ApplicationFormFieldUpdate,
    ApplicationFormResponse,
    ApplicationFormResponseCreate
)
from app.database import db
from app.utils.errors import NotFoundError
import structlog

logger = structlog.get_logger()


class ApplicationFormService:
    """Service for managing application form fields"""
    
    @staticmethod
    async def create_form_field(field_data: ApplicationFormFieldCreate, recruiter_id: UUID) -> dict:
        """
        Create a form field for a job
        
        Args:
            field_data: Form field data
            recruiter_id: Recruiter ID (for authorization)
        
        Returns:
            Created form field
        """
        try:
            # Verify recruiter owns the job
            job = db.service_client.table("job_descriptions").select("recruiter_id").eq("id", str(field_data.job_description_id)).execute()
            if not job.data or str(job.data[0]["recruiter_id"]) != str(recruiter_id):
                raise NotFoundError("Job description", str(field_data.job_description_id))
            
            field_dict = field_data.model_dump()
            field_dict["job_description_id"] = str(field_dict["job_description_id"])
            
            response = db.service_client.table("application_form_fields").insert(field_dict).execute()
            
            if not response.data:
                raise NotFoundError("Application form field", "creation failed")
            
            logger.info("Form field created", field_id=response.data[0]["id"], job_id=str(field_data.job_description_id))
            return response.data[0]
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Error creating form field", error=str(e))
            raise
    
    @staticmethod
    async def get_form_fields(job_description_id: UUID, recruiter_id: Optional[UUID] = None) -> List[dict]:
        """
        Get all form fields for a job
        
        Args:
            job_description_id: Job description ID
            recruiter_id: Optional recruiter ID (for authorization check)
        
        Returns:
            List of form fields (ordered by order_index)
        """
        try:
            if recruiter_id:
                # Verify ownership
                job = db.service_client.table("job_descriptions").select("recruiter_id").eq("id", str(job_description_id)).execute()
                if not job.data or str(job.data[0]["recruiter_id"]) != str(recruiter_id):
                    raise NotFoundError("Job description", str(job_description_id))
            
            response = db.service_client.table("application_form_fields").select("*").eq(
                "job_description_id", str(job_description_id)
            ).order("order_index").execute()
            
            return response.data or []
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Error fetching form fields", error=str(e))
            raise
    
    @staticmethod
    async def update_form_field(
        field_id: UUID,
        field_data: ApplicationFormFieldUpdate,
        recruiter_id: UUID
    ) -> dict:
        """
        Update a form field
        
        Args:
            field_id: Form field ID
            field_data: Updated field data
            recruiter_id: Recruiter ID (for authorization)
        
        Returns:
            Updated form field
        """
        try:
            # Verify ownership
            field = db.service_client.table("application_form_fields").select("job_description_id").eq("id", str(field_id)).execute()
            if not field.data:
                raise NotFoundError("Application form field", str(field_id))
            
            job = db.service_client.table("job_descriptions").select("recruiter_id").eq(
                "id", field.data[0]["job_description_id"]
            ).execute()
            
            if not job.data or str(job.data[0]["recruiter_id"]) != str(recruiter_id):
                raise NotFoundError("Application form field", str(field_id))
            
            update_data = {k: v for k, v in field_data.model_dump().items() if v is not None}
            
            response = db.service_client.table("application_form_fields").update(
                update_data
            ).eq("id", str(field_id)).execute()
            
            if not response.data:
                raise NotFoundError("Application form field", str(field_id))
            
            logger.info("Form field updated", field_id=str(field_id))
            return response.data[0]
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Error updating form field", error=str(e))
            raise
    
    @staticmethod
    async def delete_form_field(field_id: UUID, recruiter_id: UUID) -> None:
        """
        Delete a form field
        
        Args:
            field_id: Form field ID
            recruiter_id: Recruiter ID (for authorization)
        """
        try:
            # Verify ownership
            field = db.service_client.table("application_form_fields").select("job_description_id").eq("id", str(field_id)).execute()
            if not field.data:
                raise NotFoundError("Application form field", str(field_id))
            
            job = db.service_client.table("job_descriptions").select("recruiter_id").eq(
                "id", field.data[0]["job_description_id"]
            ).execute()
            
            if not job.data or str(job.data[0]["recruiter_id"]) != str(recruiter_id):
                raise NotFoundError("Application form field", str(field_id))
            
            db.service_client.table("application_form_fields").delete().eq("id", str(field_id)).execute()
            
            logger.info("Form field deleted", field_id=str(field_id))
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Error deleting form field", error=str(e))
            raise
    
    @staticmethod
    async def save_form_responses(responses: List[ApplicationFormResponseCreate]) -> List[dict]:
        """
        Save form responses for an application
        
        Args:
            responses: List of form responses
        
        Returns:
            List of saved responses
        """
        try:
            response_dicts = [
                {
                    "application_id": str(r.application_id),
                    "field_key": r.field_key,
                    "field_value": r.field_value
                }
                for r in responses
            ]
            
            response = db.service_client.table("application_form_responses").insert(
                response_dicts
            ).execute()
            
            logger.info("Form responses saved", count=len(responses), application_id=str(responses[0].application_id))
            return response.data or []
            
        except Exception as e:
            logger.error("Error saving form responses", error=str(e))
            raise
    
    @staticmethod
    async def get_form_responses(application_id: UUID) -> List[dict]:
        """
        Get form responses for an application
        
        Args:
            application_id: Application ID
        
        Returns:
            List of form responses
        """
        try:
            response = db.service_client.table("application_form_responses").select("*").eq(
                "application_id", str(application_id)
            ).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error("Error fetching form responses", error=str(e))
            raise

