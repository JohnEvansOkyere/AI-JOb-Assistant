"""
Public Job Descriptions API Routes
Public endpoints for viewing job descriptions (no auth required)
"""

from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from app.schemas.common import Response
from app.database import db
from app.models.job_description import PublicJobDescription
from app.database import db
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/public/job-descriptions", tags=["public"])


@router.get("/{job_id}", response_model=Response[PublicJobDescription])
async def get_public_job_description(job_id: UUID):
    """
    Get a job description by ID (public, no auth required)
    Only returns active jobs
    
    Args:
        job_id: Job description ID
    
    Returns:
        Job description data
    """
    try:
        response = db.service_client.table("job_descriptions").select("*").eq("id", str(job_id)).eq("is_active", True).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found or not active"
            )

        job = response.data[0]

        # Enrich with recruiter/company information for candidate-facing pages
        try:
            recruiter_id = job.get("recruiter_id")
            if recruiter_id:
                # First try to load default branding (most authoritative source)
                branding_resp = db.service_client.table("company_branding").select(
                    "company_name, company_logo_url, company_type, industry, headquarters_location, is_default"
                ).eq("recruiter_id", str(recruiter_id)).eq("is_default", True).limit(1).execute()
                
                logger.info("Checking for default branding", 
                    job_id=str(job_id),
                    recruiter_id=str(recruiter_id),
                    found_default=bool(branding_resp.data))
                
                # If no default branding, try any branding for this recruiter (ordered by created_at desc)
                if not branding_resp.data:
                    branding_resp = db.service_client.table("company_branding").select(
                        "company_name, company_logo_url, company_type, industry, headquarters_location, is_default"
                    ).eq("recruiter_id", str(recruiter_id)).order("created_at", desc=True).limit(1).execute()
                    
                    logger.info("Checking for any branding", 
                        job_id=str(job_id),
                        recruiter_id=str(recruiter_id),
                        found_any=bool(branding_resp.data))
                
                if branding_resp.data:
                    branding = branding_resp.data[0]
                    logger.info("Found branding data", 
                        job_id=str(job_id),
                        branding_company_name=branding.get("company_name"),
                        is_default=branding.get("is_default"))
                    
                    # Prefer branding company_name (most specific)
                    if branding.get("company_name"):
                        job["company_name"] = branding.get("company_name")
                    job["company_logo_url"] = branding.get("company_logo_url")
                    job["company_type"] = branding.get("company_type")
                    job["industry"] = branding.get("industry")
                    job["headquarters_location"] = branding.get("headquarters_location")
                
                # Fallback to user profile company_name if branding doesn't have it
                if not job.get("company_name"):
                    user_resp = db.service_client.table("users").select("company_name").eq("id", str(recruiter_id)).limit(1).execute()
                    if user_resp.data and user_resp.data[0].get("company_name"):
                        job["company_name"] = user_resp.data[0].get("company_name")
                        logger.info("Using user profile company_name", 
                            job_id=str(job_id),
                            company_name=job.get("company_name"))
                
                # Log final result for debugging
                logger.info("Final enriched job data", 
                    job_id=str(job_id),
                    recruiter_id=str(recruiter_id),
                    final_company_name=job.get("company_name"))
        except Exception as e:
            logger.warning("Failed to enrich public job description with company info", 
                error=str(e), 
                job_id=str(job_id),
                recruiter_id=str(recruiter_id) if recruiter_id else None)

        return Response(
            success=True,
            message="Job description retrieved successfully",
            data=job
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching public job description", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

