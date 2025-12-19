"""
Company Branding API Routes
Handles company letterhead, branding, and logo management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from typing import Optional
from uuid import UUID
from app.schemas.common import Response
from app.utils.auth import get_current_user_id
from app.utils.file_validation import validate_image_file, sanitize_filename
from app.database import db
from app.config import settings
import structlog
import aiofiles
import os

logger = structlog.get_logger()

router = APIRouter(prefix="/branding", tags=["branding"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_branding(
    request: Request,
    company_name: str = Form(...),
    primary_color: str = Form("#2563eb"),
    secondary_color: str = Form("#1e40af"),
    company_website: Optional[str] = Form(None),
    company_address: Optional[str] = Form(None),
    company_phone: Optional[str] = Form(None),
    company_email: Optional[str] = Form(None),
    sender_name: Optional[str] = Form(None),
    sender_title: Optional[str] = Form(None),
    email_signature: Optional[str] = Form(None),
    letterhead_header_html: Optional[str] = Form(None),
    letterhead_footer_html: Optional[str] = Form(None),
    letterhead_background_color: str = Form("#ffffff"),
    is_default: bool = Form(True),
    logo_file: Optional[UploadFile] = File(None),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Create or update company branding/letterhead
    
    Args:
        company_name: Company name
        primary_color: Primary brand color (hex)
        secondary_color: Secondary brand color (hex)
        company_website: Company website URL
        company_address: Company address
        company_phone: Company phone
        company_email: Company email
        sender_name: Default sender name
        sender_title: Default sender title
        email_signature: HTML email signature
        letterhead_header_html: Custom header HTML
        letterhead_footer_html: Custom footer HTML
        letterhead_background_color: Background color (hex)
        is_default: Set as default branding
        logo_file: Company logo image file
        recruiter_id: Current recruiter ID
    
    Returns:
        Created branding
    """
    try:
        # Upload logo if provided
        logo_url = None
        if logo_file:
            # Validate and sanitize image file
            safe_filename, file_size, validated_mime_type = validate_image_file(logo_file)
            
            # Save to Supabase Storage
            bucket_name = "branding"  # Create this bucket in Supabase
            file_path = f"{recruiter_id}/{safe_filename}"
            
            # Read file
            content = await logo_file.read()
            
            # Verify file size
            actual_size = len(content)
            if actual_size > file_size and file_size > 0:
                from app.utils.file_validation import validate_file_size, MAX_LOGO_FILE_SIZE
                validate_file_size(actual_size, MAX_LOGO_FILE_SIZE, "Image")
            
            # Upload to Supabase Storage
            db.service_client.storage.from_(bucket_name).upload(
                file_path,
                content,
                file_options={"content-type": validated_mime_type}
            )
            
            # Get public URL
            logo_url = db.service_client.storage.from_(bucket_name).get_public_url(file_path)
        
        # If setting as default, unset other defaults
        if is_default:
            db.service_client.table("company_branding").update({"is_default": False}).eq(
                "recruiter_id", str(recruiter_id)
            ).execute()
        
        branding_data = {
            "recruiter_id": str(recruiter_id),
            "company_name": company_name,
            "primary_color": primary_color,
            "secondary_color": secondary_color,
            "company_website": company_website,
            "company_address": company_address,
            "company_phone": company_phone,
            "company_email": company_email,
            "sender_name": sender_name,
            "sender_title": sender_title,
            "email_signature": email_signature,
            "letterhead_header_html": letterhead_header_html,
            "letterhead_footer_html": letterhead_footer_html,
            "letterhead_background_color": letterhead_background_color,
            "is_default": is_default,
        }
        
        if logo_url:
            branding_data["company_logo_url"] = logo_url
        
        response = db.service_client.table("company_branding").insert(branding_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create branding")
        
        return Response(
            success=True,
            message="Branding created successfully",
            data=response.data[0]
        )
    except Exception as e:
        logger.error("Error creating branding", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create branding: {str(e)}"
        )


@router.get("/")
async def get_branding(
    request: Request,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Get company branding (default or all)
    
    Returns:
        Company branding
    """
    try:
        # Get default branding
        response = db.service_client.table("company_branding").select("*").eq(
            "recruiter_id", str(recruiter_id)
        ).eq("is_default", True).execute()
        
        if response.data:
            return Response(
                success=True,
                message="Branding retrieved successfully",
                data=response.data[0]
            )
        
        # Get any branding
        response = db.service_client.table("company_branding").select("*").eq(
            "recruiter_id", str(recruiter_id)
        ).limit(1).execute()
        
        return Response(
            success=True,
            message="Branding retrieved successfully",
            data=response.data[0] if response.data else None
        )
    except Exception as e:
        logger.error("Error fetching branding", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch branding: {str(e)}"
        )


@router.put("/{branding_id}")
async def update_branding(
    request: Request,
    branding_id: UUID,
    company_name: Optional[str] = Form(None),
    primary_color: Optional[str] = Form(None),
    secondary_color: Optional[str] = Form(None),
    company_website: Optional[str] = Form(None),
    company_address: Optional[str] = Form(None),
    company_phone: Optional[str] = Form(None),
    company_email: Optional[str] = Form(None),
    sender_name: Optional[str] = Form(None),
    sender_title: Optional[str] = Form(None),
    email_signature: Optional[str] = Form(None),
    letterhead_header_html: Optional[str] = Form(None),
    letterhead_footer_html: Optional[str] = Form(None),
    letterhead_background_color: Optional[str] = Form(None),
    is_default: Optional[bool] = Form(None),
    logo_file: Optional[UploadFile] = File(None),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Update company branding
    
    Returns:
        Updated branding
    """
    try:
        # Verify ownership
        existing = db.service_client.table("company_branding").select("recruiter_id").eq(
            "id", str(branding_id)
        ).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Branding not found")
        
        if existing.data[0]["recruiter_id"] != str(recruiter_id):
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Upload logo if provided
        logo_url = None
        if logo_file:
            # Validate and sanitize image file
            safe_filename, file_size, validated_mime_type = validate_image_file(logo_file)
            
            bucket_name = "branding"
            file_path = f"{recruiter_id}/{safe_filename}"
            content = await logo_file.read()
            
            # Verify file size
            actual_size = len(content)
            if actual_size > file_size and file_size > 0:
                from app.utils.file_validation import validate_file_size, MAX_LOGO_FILE_SIZE
                validate_file_size(actual_size, MAX_LOGO_FILE_SIZE, "Image")
            
            db.service_client.storage.from_(bucket_name).upload(
                file_path,
                content,
                file_options={"content-type": validated_mime_type}
            )
            logo_url = db.service_client.storage.from_(bucket_name).get_public_url(file_path)
        
        # If setting as default, unset other defaults
        if is_default:
            db.service_client.table("company_branding").update({"is_default": False}).eq(
                "recruiter_id", str(recruiter_id)
            ).neq("id", str(branding_id)).execute()
        
        # Build update data
        update_data = {}
        fields = [
            "company_name", "primary_color", "secondary_color", "company_website",
            "company_address", "company_phone", "company_email", "sender_name",
            "sender_title", "email_signature", "letterhead_header_html",
            "letterhead_footer_html", "letterhead_background_color", "is_default"
        ]
        
        for field in fields:
            value = locals().get(field)
            if value is not None:
                update_data[field] = value
        
        if logo_url:
            update_data["company_logo_url"] = logo_url
        
        response = db.service_client.table("company_branding").update(update_data).eq(
            "id", str(branding_id)
        ).execute()
        
        return Response(
            success=True,
            message="Branding updated successfully",
            data=response.data[0] if response.data else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating branding", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update branding: {str(e)}"
        )

