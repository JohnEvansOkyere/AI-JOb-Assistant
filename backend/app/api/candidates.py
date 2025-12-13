"""
Candidates API Routes
Manage candidates
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from uuid import UUID
from app.schemas.common import Response
from app.utils.auth import get_current_user_id
from app.database import db
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("", response_model=Response[List[dict]])
async def list_candidates(
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    List all candidates who have applied to the recruiter's jobs
    
    Args:
        recruiter_id: Current user ID
    
    Returns:
        List of candidates with their applications
    """
    try:
        # Get all job IDs for this recruiter
        jobs = db.service_client.table("job_descriptions").select("id").eq("recruiter_id", str(recruiter_id)).execute()
        job_ids = [job["id"] for job in (jobs.data or [])]
        
        logger.info("Fetching candidates", recruiter_id=str(recruiter_id), job_count=len(job_ids))
        
        if not job_ids:
            return Response(
                success=True,
                message="No candidates found",
                data=[]
            )
        
        # Get all applications for these jobs
        applications_response = db.service_client.table("job_applications").select("*").in_("job_description_id", job_ids).order("applied_at", desc=True).execute()
        applications_data = applications_response.data or []
        
        logger.info("Found applications", application_count=len(applications_data), job_ids=job_ids)
        
        # Also check for candidates via CVs linked to these jobs (in case CVs were uploaded directly)
        cvs_response = db.service_client.table("cvs").select("candidate_id, job_description_id").in_("job_description_id", job_ids).execute()
        cv_candidate_ids = list(set(cv.get("candidate_id") for cv in (cvs_response.data or []) if cv.get("candidate_id")))
        
        logger.info("Found CVs", cv_count=len(cvs_response.data or []), cv_candidate_ids=cv_candidate_ids[:5] if cv_candidate_ids else [])
        
        # Get unique candidate IDs from both applications and CVs
        application_candidate_ids = list(set(app.get("candidate_id") for app in applications_data if app.get("candidate_id")))
        all_candidate_ids = list(set(application_candidate_ids + cv_candidate_ids))
        
        logger.info("Candidate IDs", 
                   from_applications=len(application_candidate_ids),
                   from_cvs=len(cv_candidate_ids),
                   total_unique=len(all_candidate_ids))
        
        if not all_candidate_ids:
            return Response(
                success=True,
                message="No candidates found",
                data=[]
            )
        
        # Get candidate details
        candidates_data = {}
        if all_candidate_ids:
            candidates_response = db.service_client.table("candidates").select("*").in_("id", all_candidate_ids).execute()
            logger.info("Fetched candidates from DB", fetched_count=len(candidates_response.data or []))
            for candidate in (candidates_response.data or []):
                candidates_data[candidate["id"]] = candidate
        
        # Get job details
        job_details = {}
        if job_ids:
            jobs_response = db.service_client.table("job_descriptions").select("id, title").in_("id", job_ids).execute()
            for job in (jobs_response.data or []):
                job_details[job["id"]] = job
        
        # Get screening results
        application_ids = [app.get("id") for app in applications_data if app.get("id")]
        screening_results = {}
        if application_ids:
            screening_response = db.service_client.table("cv_screening_results").select("*").in_("application_id", application_ids).execute()
            for screening in (screening_response.data or []):
                screening_results[screening["application_id"]] = screening
        
        # Group by candidate and aggregate applications
        candidates_map = {}
        
        # Process applications
        for app in applications_data:
            candidate_id = app.get("candidate_id")
            if not candidate_id:
                continue
            
            if candidate_id not in candidates_map:
                candidate_data = candidates_data.get(candidate_id, {})
                candidates_map[candidate_id] = {
                    "id": candidate_id,
                    "full_name": candidate_data.get("full_name", ""),
                    "email": candidate_data.get("email", ""),
                    "phone": candidate_data.get("phone"),
                    "created_at": candidate_data.get("created_at"),
                    "applications": [],
                    "total_applications": 0,
                    "latest_application": None
                }
            
            # Add application info
            job_id = app.get("job_description_id")
            job_info = job_details.get(job_id, {})
            screening_result = screening_results.get(app.get("id"))
            
            application_info = {
                "id": app.get("id"),
                "job_description_id": job_id,
                "job_title": job_info.get("title"),
                "status": app.get("status"),
                "applied_at": app.get("applied_at"),
                "screening_result": screening_result
            }
            
            candidates_map[candidate_id]["applications"].append(application_info)
            candidates_map[candidate_id]["total_applications"] += 1
            
            # Track latest application
            if not candidates_map[candidate_id]["latest_application"] or \
               (app.get("applied_at") and app.get("applied_at") > candidates_map[candidate_id]["latest_application"].get("applied_at", "")):
                candidates_map[candidate_id]["latest_application"] = application_info
        
        # Also add candidates who have CVs but no applications yet
        for cv in (cvs_response.data or []):
            candidate_id = cv.get("candidate_id")
            if not candidate_id or candidate_id in candidates_map:
                continue  # Already processed or no candidate_id
            
            # This candidate has a CV but no application - add them
            candidate_data = candidates_data.get(candidate_id, {})
            if candidate_data:  # Only if we found the candidate
                job_id = cv.get("job_description_id")
                job_info = job_details.get(job_id, {})
                
                candidates_map[candidate_id] = {
                    "id": candidate_id,
                    "full_name": candidate_data.get("full_name", ""),
                    "email": candidate_data.get("email", ""),
                    "phone": candidate_data.get("phone"),
                    "created_at": candidate_data.get("created_at"),
                    "applications": [],
                    "total_applications": 0,
                    "latest_application": None
                }
                
                # Add CV as a placeholder application
                application_info = {
                    "id": None,
                    "job_description_id": job_id,
                    "job_title": job_info.get("title"),
                    "status": "pending",
                    "applied_at": None,
                    "screening_result": None
                }
                
                candidates_map[candidate_id]["applications"].append(application_info)
                candidates_map[candidate_id]["total_applications"] = 1
                candidates_map[candidate_id]["latest_application"] = application_info
        
        # Convert to list and sort by latest application date
        candidates_list = list(candidates_map.values())
        candidates_list.sort(
            key=lambda x: x["latest_application"]["applied_at"] if x["latest_application"] else "",
            reverse=True
        )
        
        return Response(
            success=True,
            message="Candidates retrieved successfully",
            data=candidates_list
        )
    except Exception as e:
        logger.error("Error listing candidates", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{candidate_id}", response_model=Response[dict])
async def get_candidate(
    candidate_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Get a specific candidate with all their applications
    
    Args:
        candidate_id: Candidate ID
        recruiter_id: Current user ID
    
    Returns:
        Candidate details with applications
    """
    try:
        # Get candidate
        candidate = db.service_client.table("candidates").select("*").eq("id", str(candidate_id)).execute()
        if not candidate.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        candidate_data = candidate.data[0]
        
        # Get all job IDs for this recruiter
        jobs = db.service_client.table("job_descriptions").select("id").eq("recruiter_id", str(recruiter_id)).execute()
        job_ids = [job["id"] for job in (jobs.data or [])]
        
        if not job_ids:
            return Response(
                success=True,
                message="Candidate found but no applications",
                data={
                    **candidate_data,
                    "applications": []
                }
            )
        
        # Get applications for this candidate
        applications = db.service_client.table("job_applications").select(
            "*, job_descriptions(id, title, description), cv_screening_results(*), cvs(*)"
        ).eq("candidate_id", str(candidate_id)).in_("job_description_id", job_ids).order("applied_at", desc=True).execute()
        
        return Response(
            success=True,
            message="Candidate retrieved successfully",
            data={
                **candidate_data,
                "applications": applications.data or []
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching candidate", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
