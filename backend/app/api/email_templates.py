"""
Email Templates API Routes
Handles email template management (CRUD operations)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel
from app.schemas.common import Response
from app.utils.auth import get_current_user_id
from app.database import db
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/email-templates", tags=["Email Templates"])


class EmailTemplateCreate(BaseModel):
    name: str
    subject: str
    body_html: str
    body_text: Optional[str] = None
    template_type: str  # interview_invitation, acceptance, rejection, offer_letter, custom
    available_variables: Optional[List[str]] = None
    branding_id: Optional[UUID] = None


class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    template_type: Optional[str] = None
    available_variables: Optional[List[str]] = None
    branding_id: Optional[UUID] = None


@router.post("", response_model=Response[dict], status_code=status.HTTP_201_CREATED)
async def create_template(
    request: Request,
    template: EmailTemplateCreate,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """Create a new email template"""
    try:
        template_data = {
            "recruiter_id": str(recruiter_id),
            "name": template.name,
            "subject": template.subject,
            "body_html": template.body_html,
            "body_text": template.body_text,
            "template_type": template.template_type,
            "available_variables": template.available_variables or [],
            "branding_id": str(template.branding_id) if template.branding_id else None,
        }
        
        response = db.service_client.table("email_templates").insert(template_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create template")
        
        return Response(
            success=True,
            message="Template created successfully",
            data=response.data[0]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating template", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )


@router.get("", response_model=Response[List[dict]])
async def list_templates(
    request: Request,
    template_type: Optional[str] = None,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """List all email templates for the recruiter"""
    try:
        query = db.service_client.table("email_templates").select("*").eq("recruiter_id", str(recruiter_id))
        
        if template_type:
            query = query.eq("template_type", template_type)
        
        response = query.order("created_at", desc=True).execute()
        
        return Response(
            success=True,
            message="Templates retrieved successfully",
            data=response.data or []
        )
    except Exception as e:
        logger.error("Error listing templates", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}"
        )


@router.get("/{template_id}", response_model=Response[dict])
async def get_template(
    request: Request,
    template_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """Get a specific email template"""
    try:
        response = db.service_client.table("email_templates").select("*").eq("id", str(template_id)).eq("recruiter_id", str(recruiter_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return Response(
            success=True,
            message="Template retrieved successfully",
            data=response.data[0]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching template", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch template: {str(e)}"
        )


@router.put("/{template_id}", response_model=Response[dict])
async def update_template(
    request: Request,
    template_id: UUID,
    template: EmailTemplateUpdate,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """Update an email template"""
    try:
        # Verify template belongs to recruiter
        existing = db.service_client.table("email_templates").select("id").eq("id", str(template_id)).eq("recruiter_id", str(recruiter_id)).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Template not found")
        
        update_data = {}
        if template.name is not None:
            update_data["name"] = template.name
        if template.subject is not None:
            update_data["subject"] = template.subject
        if template.body_html is not None:
            update_data["body_html"] = template.body_html
        if template.body_text is not None:
            update_data["body_text"] = template.body_text
        if template.template_type is not None:
            update_data["template_type"] = template.template_type
        if template.available_variables is not None:
            update_data["available_variables"] = template.available_variables
        if template.branding_id is not None:
            update_data["branding_id"] = str(template.branding_id)
        
        update_data["updated_at"] = "now()"
        
        response = db.service_client.table("email_templates").update(update_data).eq("id", str(template_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to update template")
        
        return Response(
            success=True,
            message="Template updated successfully",
            data=response.data[0]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating template", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update template: {str(e)}"
        )


@router.delete("/{template_id}", response_model=Response[dict])
async def delete_template(
    request: Request,
    template_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """Delete an email template"""
    try:
        # Verify template belongs to recruiter
        existing = db.service_client.table("email_templates").select("id").eq("id", str(template_id)).eq("recruiter_id", str(recruiter_id)).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Template not found")
        
        db.service_client.table("email_templates").delete().eq("id", str(template_id)).execute()
        
        return Response(
            success=True,
            message="Template deleted successfully",
            data={"id": str(template_id)}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting template", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete template: {str(e)}"
        )

