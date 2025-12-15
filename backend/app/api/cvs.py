"""
CVs API Routes
CV upload and management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Optional
from uuid import UUID
from app.schemas.common import Response
from app.models.cv import CV
from app.services.cv_service import CVService
from app.services.cv_parser import CVParser
from app.utils.auth import get_current_user_id
from app.config import settings
from app.database import db
import structlog
import aiofiles
import os
import tempfile

logger = structlog.get_logger()

router = APIRouter(prefix="/cvs", tags=["cvs"])


@router.post("/upload", response_model=Response[CV], status_code=status.HTTP_201_CREATED)
async def upload_cv(
    file: UploadFile = File(...),
    candidate_id: UUID = Form(...),
    job_description_id: Optional[UUID] = Form(None),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Upload a CV file
    
    Args:
        file: CV file (PDF, DOCX, or TXT)
        candidate_id: Candidate ID
        job_description_id: Optional job description ID
        recruiter_id: Current user ID (for authorization)
    
    Returns:
        Created CV record with parsed content
    """
    try:
        # Verify recruiter has access to job if provided (use service client to bypass RLS)
        if job_description_id:
            job = db.service_client.table("job_descriptions").select("id").eq("id", str(job_description_id)).eq("recruiter_id", str(recruiter_id)).execute()
            if not job.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Job description not found"
                )
        
        # Save file to temporary location
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"{candidate_id}_{file.filename}")
        
        async with aiofiles.open(temp_file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        file_size = os.path.getsize(temp_file_path)
        mime_type = file.content_type or "application/octet-stream"
        
        # Upload to Supabase Storage
        storage_path = f"{candidate_id}/{file.filename}"
        bucket_name = settings.supabase_storage_bucket_cvs
        
        try:
            with open(temp_file_path, 'rb') as f:
                db.service_client.storage.from_(bucket_name).upload(
                    storage_path,
                    f.read(),
                    file_options={"content-type": mime_type}
                )
        except Exception as e:
            error_str = str(e)
            os.remove(temp_file_path)
            
            # Handle duplicate file gracefully (409 Conflict)
            if "409" in error_str or "duplicate" in error_str.lower() or "already exists" in error_str.lower():
                logger.info("CV file already exists in storage, using existing file", 
                           storage_path=storage_path, 
                           bucket=bucket_name)
                # File already exists, continue with the existing file
                # No need to raise an error - we'll use the existing file path
            elif "bucket not found" in error_str.lower() or "404" in error_str:
                logger.error("Error uploading to storage - bucket not found", error=error_str, bucket=bucket_name)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Storage bucket '{bucket_name}' not found. Please create the bucket in Supabase Storage. See documentation for setup instructions."
                )
            else:
                logger.error("Error uploading to storage", error=error_str, bucket=bucket_name)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload file to storage: {error_str}"
                )
        
        # Parse CV content
        try:
            parsed_text = CVParser.parse_file(temp_file_path, mime_type)
            parsed_json = CVParser.extract_structured_data(parsed_text)
        except Exception as e:
            logger.warning("Error parsing CV", error=str(e))
            parsed_text = ""
            parsed_json = None
        
        # Clean up temp file
        os.remove(temp_file_path)
        
        # Create CV record
        cv = await CVService.upload_cv(
            candidate_id=candidate_id,
            file_name=file.filename,
            file_path=storage_path,
            file_size=file_size,
            mime_type=mime_type,
            job_description_id=job_description_id
        )
        
        # Update with parsed content
        if parsed_text:
            cv = await CVService.update_cv_parsing(
                cv_id=UUID(cv["id"]),
                parsed_text=parsed_text,
                parsed_json=parsed_json
            )
        
        return Response(
            success=True,
            message="CV uploaded and parsed successfully",
            data=cv
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error uploading CV", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload CV: {str(e)}"
        )


@router.get("/{cv_id}", response_model=Response[CV])
async def get_cv(cv_id: UUID):
    """
    Get a CV by ID
    
    Args:
        cv_id: CV ID
    
    Returns:
        CV data
    """
    try:
        cv = await CVService.get_cv(cv_id)
        return Response(
            success=True,
            message="CV retrieved successfully",
            data=cv
        )
    except Exception as e:
        logger.error("Error fetching CV", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{cv_id}/download-url", response_model=Response[dict])
async def get_cv_download_url(
    cv_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Get a signed URL for downloading a CV file
    
    Args:
        cv_id: CV ID
        recruiter_id: Current user ID (for authorization)
    
    Returns:
        Signed URL for CV download
    """
    try:
        # Get CV data
        cv = await CVService.get_cv(cv_id)
        
        # Verify recruiter has access (check if CV is linked to recruiter's job)
        if cv.get("job_description_id"):
            job = db.service_client.table("job_descriptions").select("recruiter_id").eq("id", cv["job_description_id"]).execute()
            if job.data and str(job.data[0]["recruiter_id"]) != str(recruiter_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        # Get file path
        file_path = cv.get("file_path")
        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CV file path not found"
            )
        
        # Generate signed URL (valid for 1 hour)
        bucket_name = settings.supabase_storage_bucket_cvs
        try:
            # Create signed URL using Supabase storage
            # Supabase returns a dict with 'signedURL' key
            signed_url_response = db.service_client.storage.from_(bucket_name).create_signed_url(
                file_path,
                3600  # 1 hour expiry
            )
            
            # Handle both dict response and string response
            if isinstance(signed_url_response, dict):
                signed_url = signed_url_response.get("signedURL") or signed_url_response.get("url") or signed_url_response.get("signed_url")
            else:
                signed_url = signed_url_response
            
            if not signed_url:
                raise ValueError("Failed to extract signed URL from response")
            
            return Response(
                success=True,
                message="CV download URL generated successfully",
                data={
                    "download_url": signed_url,
                    "file_name": cv.get("file_name", "cv.pdf"),
                    "mime_type": cv.get("mime_type", "application/pdf")
                }
            )
        except Exception as storage_error:
            logger.error("Error generating signed URL", error=str(storage_error), cv_id=str(cv_id), exc_info=True)
            # Fallback: try to construct public URL if bucket is public
            public_url = f"{settings.supabase_url}/storage/v1/object/public/{bucket_name}/{file_path}"
            return Response(
                success=True,
                message="CV download URL generated (public)",
                data={
                    "download_url": public_url,
                    "file_name": cv.get("file_name", "cv.pdf"),
                    "mime_type": cv.get("mime_type", "application/pdf")
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating CV download URL", error=str(e), cv_id=str(cv_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/job/{job_description_id}", response_model=Response[list])
async def list_cvs_for_job(
    job_description_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    List CVs for a specific job
    
    Args:
        job_description_id: Job description ID
        recruiter_id: Current user ID (for authorization)
    
    Returns:
        List of CVs
    """
    try:
        # Verify recruiter owns the job (use service client to bypass RLS)
        job = db.service_client.table("job_descriptions").select("id").eq("id", str(job_description_id)).eq("recruiter_id", str(recruiter_id)).execute()
        if not job.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job description not found"
            )
        
        cvs = await CVService.list_cvs_for_job(job_description_id)
        return Response(
            success=True,
            message="CVs retrieved successfully",
            data=cvs
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing CVs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

