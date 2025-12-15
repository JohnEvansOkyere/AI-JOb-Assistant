"""
CV Rankings API Routes
Get ranked candidates by job based on CV screening scores
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.schemas.common import Response
from app.utils.auth import get_current_user_id
from app.database import db
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/rankings/cv", tags=["cv-rankings"])


@router.get("/jobs", response_model=Response[List[dict]])
async def list_jobs_with_cv_rankings(
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    List all jobs with screened candidates count for ranking view
    
    Args:
        recruiter_id: Current user ID
    
    Returns:
        List of jobs with screened candidates count
    """
    try:
        # Get all jobs for this recruiter
        jobs = db.service_client.table("job_descriptions").select("*").eq("recruiter_id", str(recruiter_id)).order("created_at", desc=True).execute()
        
        if not jobs.data:
            return Response(
                success=True,
                message="No jobs found",
                data=[]
            )
        
        # Get screened applications count for each job
        job_ids = [job["id"] for job in jobs.data]
        
        # Get all applications for these jobs
        applications = db.service_client.table("job_applications").select("id, job_description_id").in_("job_description_id", job_ids).execute()
        
        if not applications.data:
            # No applications, return jobs with zero stats
            result = []
            for job in jobs.data:
                result.append({
                    **job,
                    "screened_count": 0,
                    "qualified_count": 0,
                    "maybe_qualified_count": 0,
                    "not_qualified_count": 0
                })
            return Response(
                success=True,
                message="Jobs with rankings retrieved successfully",
                data=result
            )
        
        # Get screening results separately
        application_ids = [app.get("id") for app in applications.data if app.get("id")]
        screening_results = {}
        if application_ids:
            screening_response = db.service_client.table("cv_screening_results").select("*").in_("application_id", application_ids).execute()
            for screening in (screening_response.data or []):
                screening_results[screening["application_id"]] = screening
        
        # Count screened candidates per job
        job_stats = {}
        for app in (applications.data or []):
            job_id = app.get("job_description_id")
            app_id = app.get("id")
            screening = screening_results.get(app_id)
            
            if job_id not in job_stats:
                job_stats[job_id] = {
                    "total_screened": 0,
                    "qualified": 0,
                    "maybe_qualified": 0,
                    "not_qualified": 0
                }
            
            if screening:
                job_stats[job_id]["total_screened"] += 1
                recommendation = screening.get("recommendation", "")
                if recommendation == "qualified":
                    job_stats[job_id]["qualified"] += 1
                elif recommendation == "maybe_qualified":
                    job_stats[job_id]["maybe_qualified"] += 1
                elif recommendation == "not_qualified":
                    job_stats[job_id]["not_qualified"] += 1
        
        # Combine job data with stats
        result = []
        for job in jobs.data:
            stats = job_stats.get(job["id"], {
                "total_screened": 0,
                "qualified": 0,
                "maybe_qualified": 0,
                "not_qualified": 0
            })
            result.append({
                **job,
                "screened_count": stats["total_screened"],
                "qualified_count": stats["qualified"],
                "maybe_qualified_count": stats["maybe_qualified"],
                "not_qualified_count": stats["not_qualified"]
            })
        
        return Response(
            success=True,
            message="Jobs with rankings retrieved successfully",
            data=result
        )
    except Exception as e:
        logger.error("Error listing jobs with rankings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/job/{job_description_id}", response_model=Response[List[dict]])
async def get_cv_ranked_candidates(
    job_description_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Get ranked candidates for a specific job, ordered by match score (highest first)
    
    Args:
        job_description_id: Job description ID
        recruiter_id: Current user ID
    
    Returns:
        List of candidates ranked by match score
    """
    try:
        # Verify job ownership
        job = db.service_client.table("job_descriptions").select("*").eq("id", str(job_description_id)).eq("recruiter_id", str(recruiter_id)).execute()
        if not job.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        job_data = job.data[0]
        
        # Get all applications for this job
        applications = db.service_client.table("job_applications").select("*").eq("job_description_id", str(job_description_id)).execute()
        
        if not applications.data:
            return Response(
                success=True,
                message="No applications found for this job",
                data=[]
            )
        
        # Get related data separately
        candidate_ids = list(set(app.get("candidate_id") for app in applications.data if app.get("candidate_id")))
        application_ids = [app.get("id") for app in applications.data if app.get("id")]
        
        # Fetch candidates
        candidates_data = {}
        if candidate_ids:
            candidates_response = db.service_client.table("candidates").select("*").in_("id", candidate_ids).execute()
            for candidate in (candidates_response.data or []):
                candidates_data[candidate["id"]] = candidate
        
        # Fetch screening results
        screening_results = {}
        if application_ids:
            screening_response = db.service_client.table("cv_screening_results").select("*").in_("application_id", application_ids).execute()
            for screening in (screening_response.data or []):
                screening_results[screening["application_id"]] = screening
        
        # Combine data and filter applications with screening results
        ranked_applications = []
        for app in applications.data:
            app_id = app.get("id")
            candidate_id = app.get("candidate_id")
            screening = screening_results.get(app_id)
            
            # Only include applications with screening results
            if screening and screening.get("match_score") is not None:
                ranked_applications.append({
                    **app,
                    "candidates": candidates_data.get(candidate_id),
                    "cv_screening_results": screening,
                    "rank": 0  # Will be set after sorting
                })
        
        # Sort by match score (descending)
        ranked_applications.sort(
            key=lambda x: x.get("cv_screening_results", {}).get("match_score", 0),
            reverse=True
        )
        
        # Assign ranks
        for index, app in enumerate(ranked_applications, start=1):
            app["rank"] = index
        
        return Response(
            success=True,
            message="Ranked candidates retrieved successfully",
            data=ranked_applications
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting ranked candidates", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

