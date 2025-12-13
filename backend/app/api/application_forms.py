"""
Application Forms API Routes
Manage custom application form fields
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List
from uuid import UUID
from app.schemas.common import Response
from app.models.application_form import (
    ApplicationFormField,
    ApplicationFormFieldCreate,
    ApplicationFormFieldUpdate
)
from app.services.application_form_service import ApplicationFormService
from app.utils.auth import get_current_user_id
from app.utils.errors import NotFoundError
from app.database import db
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/application-forms", tags=["application-forms"])


@router.post("/fields", response_model=Response[ApplicationFormField], status_code=status.HTTP_201_CREATED)
async def create_form_field(
    field_data: ApplicationFormFieldCreate,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Create a custom form field for a job
    
    Args:
        field_data: Form field data
        recruiter_id: Current user ID
    
    Returns:
        Created form field
    """
    try:
        field = await ApplicationFormService.create_form_field(field_data, recruiter_id)
        return Response(
            success=True,
            message="Form field created successfully",
            data=field
        )
    except Exception as e:
        logger.error("Error creating form field", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/fields/job/{job_description_id}", response_model=Response[List[ApplicationFormField]])
async def get_form_fields(
    job_description_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Get all form fields for a job (recruiter only)
    
    Args:
        job_description_id: Job description ID
        recruiter_id: Current user ID
    
    Returns:
        List of form fields
    """
    try:
        fields = await ApplicationFormService.get_form_fields(job_description_id, recruiter_id)
        return Response(
            success=True,
            message="Form fields retrieved successfully",
            data=fields
        )
    except NotFoundError as e:
        # If job not found or no access, return 404
        logger.warning("Form fields not found", job_id=str(job_description_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error fetching form fields", error=str(e), job_id=str(job_description_id))
        # Check if it's a table not found error
        if "could not find the table" in str(e).lower() or "pgrst205" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database tables not found. Please run the migration: database/migrations/003_add_application_forms.sql"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/fields/job/{job_description_id}/public", response_model=Response[List[ApplicationFormField]])
async def get_public_form_fields(job_description_id: UUID):
    """
    Get form fields for a job (public, no auth required)
    Only returns fields for active jobs
    
    Args:
        job_description_id: Job description ID
    
    Returns:
        List of form fields
    """
    try:
        fields = await ApplicationFormService.get_form_fields(job_description_id, recruiter_id=None)
        return Response(
            success=True,
            message="Form fields retrieved successfully",
            data=fields
        )
    except Exception as e:
        logger.error("Error fetching public form fields", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/fields/{field_id}", response_model=Response[ApplicationFormField])
async def update_form_field(
    field_id: UUID,
    field_data: ApplicationFormFieldUpdate,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Update a form field
    
    Args:
        field_id: Form field ID
        field_data: Updated field data
        recruiter_id: Current user ID
    
    Returns:
        Updated form field
    """
    try:
        field = await ApplicationFormService.update_form_field(field_id, field_data, recruiter_id)
        return Response(
            success=True,
            message="Form field updated successfully",
            data=field
        )
    except Exception as e:
        logger.error("Error updating form field", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/fields/{field_id}", response_model=Response[dict])
async def delete_form_field(
    field_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Delete a form field
    
    Args:
        field_id: Form field ID
        recruiter_id: Current user ID
    
    Returns:
        Deletion confirmation
    """
    try:
        await ApplicationFormService.delete_form_field(field_id, recruiter_id)
        return Response(
            success=True,
            message="Form field deleted successfully"
        )
    except Exception as e:
        logger.error("Error deleting form field", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/fields/batch", response_model=Response[List[ApplicationFormField]], status_code=status.HTTP_201_CREATED)
async def create_form_fields_batch(
    fields: List[ApplicationFormFieldCreate] = Body(...),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Create multiple form fields at once
    
    Args:
        fields: List of form field data
        recruiter_id: Current user ID
    
    Returns:
        List of created form fields
    """
    try:
        created_fields = []
        for field_data in fields:
            field = await ApplicationFormService.create_form_field(field_data, recruiter_id)
            created_fields.append(field)
        
        return Response(
            success=True,
            message=f"Created {len(created_fields)} form fields successfully",
            data=created_fields
        )
    except Exception as e:
        logger.error("Error creating form fields batch", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

