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
        try:
            with open(temp_file_path, 'rb') as f:
                db.service_client.storage.from_(settings.supabase_storage_bucket_cvs).upload(
                    storage_path,
                    f.read(),
                    file_options={"content-type": mime_type}
                )
        except Exception as e:
            logger.error("Error uploading to storage", error=str(e))
            os.remove(temp_file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to storage"
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

