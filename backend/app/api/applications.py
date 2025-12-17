"""
Job Applications API Routes
Public application submission and recruiter management
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from typing import Optional, List
from uuid import UUID
from app.schemas.common import Response
from app.models.job_application import JobApplication, JobApplicationCreate
from app.services.application_service import ApplicationService
from app.services.application_form_service import ApplicationFormService
from app.services.cv_screening_service import CVScreeningService
from app.services.cv_parser import CVParser
from app.models.application_form import ApplicationFormResponseCreate
from app.utils.auth import get_current_user_id
from app.config import settings
from app.database import db
import structlog
import aiofiles
import os
import tempfile

logger = structlog.get_logger()

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("/apply", response_model=Response[JobApplication], status_code=status.HTTP_201_CREATED)
async def apply_for_job(
    job_description_id: UUID = Form(...),
    email: str = Form(...),
    full_name: str = Form(...),
    phone: Optional[str] = Form(None),
    cover_letter: Optional[str] = Form(None),
    cv_file: UploadFile = File(...),
    custom_fields: Optional[str] = Form(None)  # JSON string of custom field responses
):
    """
    Apply for a job (public endpoint, no auth required)
    
    Args:
        job_description_id: Job description ID
        email: Candidate email
        full_name: Candidate full name
        phone: Optional phone number
        cover_letter: Optional cover letter
        cv_file: CV file (PDF, DOCX, or TXT)
    
    Returns:
        Created application
    """
    try:
        # Verify job exists and is active
        job = db.service_client.table("job_descriptions").select("*").eq("id", str(job_description_id)).eq("is_active", True).execute()
        if not job.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found or not active"
            )
        
        # Save file temporarily
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"{job_description_id}_{cv_file.filename}")
        
        async with aiofiles.open(temp_file_path, 'wb') as out_file:
            content = await cv_file.read()
            await out_file.write(content)
        
        file_size = os.path.getsize(temp_file_path)
        mime_type = cv_file.content_type or "application/octet-stream"
        
        # Upload to Supabase Storage
        storage_path = f"applications/{job_description_id}/{cv_file.filename}"
        bucket_name = getattr(settings, 'supabase_storage_bucket_cvs', 'cvs')
        
        try:
            with open(temp_file_path, 'rb') as f:
                # Use the same bucket as CVs
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
                logger.error("Error uploading CV - bucket not found", error=error_str, bucket=bucket_name)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Storage bucket '{bucket_name}' not found. Please create the bucket in Supabase Storage. See documentation for setup instructions."
                )
            else:
                logger.error("Error uploading CV", error=error_str, bucket=bucket_name)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload CV: {error_str}"
                )
        
        # Parse CV
        try:
            parsed_text = CVParser.parse_file(temp_file_path, mime_type)
        except Exception as e:
            logger.warning("Error parsing CV", error=str(e))
            parsed_text = ""
        
        # Clean up temp file
        os.remove(temp_file_path)
        
        # Create application
        application_data = JobApplicationCreate(
            job_description_id=job_description_id,
            email=email,
            full_name=full_name,
            phone=phone,
            cover_letter=cover_letter
        )
        
        application = await ApplicationService.create_application(
            application_data=application_data,
            cv_file_name=cv_file.filename,
            cv_file_path=storage_path,
            cv_file_size=file_size,
            cv_mime_type=mime_type,
            cv_text=parsed_text
        )
        
        # Save custom form field responses if provided
        if custom_fields:
            try:
                import json
                custom_data = json.loads(custom_fields)
                responses = []
                for key, value in custom_data.items():
                    # Handle different value types
                    if value is None:
                        field_value = ""
                    elif isinstance(value, list):
                        # For checkbox fields (arrays), convert to JSON string
                        field_value = json.dumps(value)
                    elif isinstance(value, (dict, bool)):
                        # For complex types, convert to JSON string
                        field_value = json.dumps(value)
                    else:
                        # For simple types, convert to string
                        field_value = str(value)
                    
                    responses.append(
                        ApplicationFormResponseCreate(
                            application_id=UUID(application["id"]),
                            field_key=key,
                            field_value=field_value
                        )
                    )
                
                if responses:
                    await ApplicationFormService.save_form_responses(responses)
            except Exception as e:
                logger.warning("Error saving custom form responses", error=str(e), exc_info=True)
                # Don't fail the application if custom fields fail
        
        return Response(
            success=True,
            message="Application submitted successfully",
            data=application
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating application", error=str(e), exc_info=True)
        # Provide more detailed error message
        error_detail = str(e)
        if "could not find the table" in error_detail.lower():
            error_detail = "Database tables not found. Please run migrations."
        elif "RLS" in error_detail or "row-level security" in error_detail.lower():
            error_detail = "Database access error. Please check RLS policies."
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit application: {error_detail}"
        )


@router.get("", response_model=Response[List[dict]])
async def list_all_applications(
    status: Optional[str] = Query(None, description="Filter by status"),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    List all applications for the recruiter (across all jobs)
    
    Args:
        status: Optional status filter
        recruiter_id: Current user ID
    
    Returns:
        List of applications with job and candidate details
    """
    try:
        # Get all job IDs for this recruiter
        jobs = db.service_client.table("job_descriptions").select("id").eq("recruiter_id", str(recruiter_id)).execute()
        job_ids = [job["id"] for job in (jobs.data or [])]
        
        logger.info("Fetching applications", recruiter_id=str(recruiter_id), job_count=len(job_ids), job_ids=job_ids[:3] if job_ids else [])
        
        if not job_ids:
            return Response(
                success=True,
                message="No applications found",
                data=[]
            )
        
        # Get all applications for these jobs
        # Fetch applications first - Applications page reads from job_applications table
        query = db.service_client.table("job_applications").select("*").in_("job_description_id", job_ids)
        
        if status:
            query = query.eq("status", status)
        
        query = query.order("applied_at", desc=True)
        applications_response = query.execute()
        applications_data = applications_response.data or []
        
        logger.info("Found applications in job_applications table", 
                   application_count=len(applications_data),
                   job_ids=job_ids[:3] if job_ids else [])
        
        if not applications_data:
            logger.warning("No applications found in job_applications table", 
                          recruiter_id=str(recruiter_id),
                          job_ids=job_ids,
                          note="This means applications were not created when candidates submitted forms")
            return Response(
                success=True,
                message="Applications retrieved successfully",
                data=[]
            )
        
        # Get related data separately
        candidate_ids = list(set(app.get("candidate_id") for app in applications_data if app.get("candidate_id")))
        application_ids = [app.get("id") for app in applications_data if app.get("id")]
        
        # Fetch candidates
        candidates_data = {}
        if candidate_ids:
            candidates_response = db.service_client.table("candidates").select("*").in_("id", candidate_ids).execute()
            for candidate in (candidates_response.data or []):
                candidates_data[candidate["id"]] = candidate
        
        # Fetch job details
        job_details = {}
        if job_ids:
            jobs_response = db.service_client.table("job_descriptions").select("id, title").in_("id", job_ids).execute()
            for job in (jobs_response.data or []):
                job_details[job["id"]] = job
        
        # Fetch screening results
        screening_results = {}
        if application_ids:
            screening_response = db.service_client.table("cv_screening_results").select("*").in_("application_id", application_ids).execute()
            for screening in (screening_response.data or []):
                screening_results[screening["application_id"]] = screening
        
        # Combine data
        enriched_applications = []
        for app in applications_data:
            candidate_id = app.get("candidate_id")
            job_id = app.get("job_description_id")
            app_id = app.get("id")
            
            enriched_app = {
                **app,
                "candidates": candidates_data.get(candidate_id),
                "job_descriptions": job_details.get(job_id),
                "cv_screening_results": screening_results.get(app_id)
            }
            enriched_applications.append(enriched_app)
        
        return Response(
            success=True,
            message="Applications retrieved successfully",
            data=enriched_applications
        )
    except Exception as e:
        logger.error("Error listing all applications", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{application_id}", response_model=Response[dict])
async def get_application(
    application_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Get a single application by ID
    
    Args:
        application_id: Application ID
        recruiter_id: Current user ID (for authorization)
    
    Returns:
        Application with candidate and job details
    """
    try:
        # Get application with related data
        result = db.service_client.table("job_applications").select(
            "*, candidates(id, full_name, email, phone), job_descriptions(id, title, recruiter_id)"
        ).eq("id", str(application_id)).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        application = result.data[0]
        
        # Verify recruiter owns the job
        job_data = application.get("job_descriptions", {})
        if job_data.get("recruiter_id") != str(recruiter_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this application"
            )
        
        return Response(
            success=True,
            message="Application retrieved successfully",
            data=application
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting application", error=str(e), application_id=str(application_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/job/{job_description_id}", response_model=Response[List[dict]])
async def list_applications(
    job_description_id: UUID,
    application_status: Optional[str] = Query(None, description="Filter by status", alias="status"),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    List applications for a job (recruiter only)
    
    Args:
        job_description_id: Job description ID
        application_status: Optional status filter (aliased as 'status' in query)
        recruiter_id: Current user ID
    
    Returns:
        List of applications
    """
    try:
        applications = await ApplicationService.list_applications_for_job(
            job_description_id=job_description_id,
            recruiter_id=recruiter_id,
            status=application_status
        )
        return Response(
            success=True,
            message="Applications retrieved successfully",
            data=applications
        )
    except Exception as e:
        logger.error("Error listing applications", error=str(e), job_id=str(job_description_id), recruiter_id=str(recruiter_id))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{application_id}/screen", response_model=Response[dict])
async def screen_application(
    application_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Screen a single application (recruiter only)
    
    Args:
        application_id: Application ID
        recruiter_id: Current user ID
    
    Returns:
        Screening result
    """
    try:
        # Verify access
        app = await ApplicationService.get_application(application_id)
        job = db.service_client.table("job_descriptions").select("*").eq("id", app["job_description_id"]).eq("recruiter_id", str(recruiter_id)).execute()
        if not job.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Get CV text
        cv = db.service_client.table("cvs").select("parsed_text").eq("id", app["cv_id"]).execute()
        if not cv.data or not cv.data[0].get("parsed_text"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CV not found or not parsed"
            )
        
        cv_text = cv.data[0]["parsed_text"]
        job_description = job.data[0]
        
        # Screen
        screening_service = CVScreeningService()
        result = await screening_service.screen_application(
            application_id=application_id,
            cv_text=cv_text,
            job_description=job_description
        )
        
        return Response(
            success=True,
            message="Application screened successfully",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error screening application", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/job/{job_description_id}/screen-all", response_model=Response[dict])
async def screen_all_applications(
    job_description_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Screen all pending applications for a job (recruiter only)
    
    Args:
        job_description_id: Job description ID
        recruiter_id: Current user ID
    
    Returns:
        Screening summary
    """
    try:
        # Verify access
        job = db.service_client.table("job_descriptions").select("id").eq("id", str(job_description_id)).eq("recruiter_id", str(recruiter_id)).execute()
        if not job.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Get pending applications
        applications = db.service_client.table("job_applications").select("id").eq("job_description_id", str(job_description_id)).eq("status", "pending").execute()
        
        if not applications.data:
            return Response(
                success=True,
                message="No pending applications to screen",
                data={"screened": 0}
            )
        
        application_ids = [UUID(app["id"]) for app in applications.data]
        
        # Batch screen
        screening_service = CVScreeningService()
        results = await screening_service.batch_screen_applications(
            job_description_id=job_description_id,
            application_ids=application_ids
        )
        
        # Count qualified
        qualified_count = sum(1 for r in results if r.get("recommendation") == "qualified")
        
        return Response(
            success=True,
            message=f"Screened {len(results)} applications",
            data={
                "screened": len(results),
                "qualified": qualified_count,
                "maybe_qualified": sum(1 for r in results if r.get("recommendation") == "maybe_qualified"),
                "not_qualified": sum(1 for r in results if r.get("recommendation") == "not_qualified")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in batch screening", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{application_id}/screening", response_model=Response[dict])
async def get_screening_result(
    application_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Get screening result for an application (recruiter only)
    
    Args:
        application_id: Application ID
        recruiter_id: Current user ID
    
    Returns:
        Screening result
    """
    try:
        # Verify access
        app = await ApplicationService.get_application(application_id)
        job = db.service_client.table("job_descriptions").select("recruiter_id").eq("id", app["job_description_id"]).execute()
        if not job.data or str(job.data[0]["recruiter_id"]) != str(recruiter_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Get screening result
        screening = db.service_client.table("cv_screening_results").select("*").eq("application_id", str(application_id)).execute()
        
        if not screening.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Screening result not found"
            )
        
        return Response(
            success=True,
            message="Screening result retrieved successfully",
            data=screening.data[0]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching screening result", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/{application_id}/status", response_model=Response[JobApplication])
async def update_application_status(
    application_id: UUID,
    status: str = Query(..., description="New status"),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Update application status (recruiter only)
    
    Args:
        application_id: Application ID
        status: New status
        recruiter_id: Current user ID
    
    Returns:
        Updated application
    """
    try:
        application = await ApplicationService.update_application_status(
            application_id=application_id,
            status=status,
            recruiter_id=recruiter_id
        )
        return Response(
            success=True,
            message="Application status updated successfully",
            data=application
        )
    except Exception as e:
        logger.error("Error updating application status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

