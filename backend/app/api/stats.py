"""
Statistics API Routes
Dashboard statistics and analytics
"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from app.schemas.common import Response
from app.utils.auth import get_current_user_id
from app.database import db
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/dashboard", response_model=Response[dict])
async def get_dashboard_stats(recruiter_id: UUID = Depends(get_current_user_id)):
    """
    Get dashboard statistics for the current recruiter
    
    Args:
        recruiter_id: Current user ID
    
    Returns:
        Dashboard statistics
    """
    try:
        # Get job descriptions count
        jobs = db.service_client.table("job_descriptions").select("id", count="exact").eq("recruiter_id", str(recruiter_id)).execute()
        total_jobs = jobs.count if hasattr(jobs, 'count') else len(jobs.data) if jobs.data else 0
        
        active_jobs = db.service_client.table("job_descriptions").select("id", count="exact").eq("recruiter_id", str(recruiter_id)).eq("is_active", True).execute()
        active_jobs_count = active_jobs.count if hasattr(active_jobs, 'count') else len(active_jobs.data) if active_jobs.data else 0
        
        # Get applications count (for all jobs by this recruiter)
        job_ids = db.service_client.table("job_descriptions").select("id").eq("recruiter_id", str(recruiter_id)).execute()
        job_id_list = [job["id"] for job in (job_ids.data or [])]
        
        total_applications = 0
        pending_applications = 0
        qualified_applications = 0
        
        if job_id_list:
            applications = db.service_client.table("job_applications").select("id, status", count="exact").in_("job_description_id", job_id_list).execute()
            total_applications = applications.count if hasattr(applications, 'count') else len(applications.data) if applications.data else 0
            
            pending = db.service_client.table("job_applications").select("id", count="exact").in_("job_description_id", job_id_list).eq("status", "pending").execute()
            pending_applications = pending.count if hasattr(pending, 'count') else len(pending.data) if pending.data else 0
            
            qualified = db.service_client.table("job_applications").select("id", count="exact").in_("job_description_id", job_id_list).eq("status", "qualified").execute()
            qualified_applications = qualified.count if hasattr(qualified, 'count') else len(qualified.data) if qualified.data else 0
        
        # Get interviews count
        interviews = db.service_client.table("interviews").select("id", count="exact").in_("job_description_id", job_id_list).execute()
        total_interviews = interviews.count if hasattr(interviews, 'count') else len(interviews.data) if interviews.data else 0
        
        completed_interviews = db.service_client.table("interviews").select("id", count="exact").in_("job_description_id", job_id_list).eq("status", "completed").execute()
        completed_interviews_count = completed_interviews.count if hasattr(completed_interviews, 'count') else len(completed_interviews.data) if completed_interviews.data else 0
        
        # Get candidates count
        candidates = db.service_client.table("candidates").select("id", count="exact").execute()
        total_candidates = candidates.count if hasattr(candidates, 'count') else len(candidates.data) if candidates.data else 0
        
        stats = {
            "jobs": {
                "total": total_jobs,
                "active": active_jobs_count,
            },
            "applications": {
                "total": total_applications,
                "pending": pending_applications,
                "qualified": qualified_applications,
            },
            "interviews": {
                "total": total_interviews,
                "completed": completed_interviews_count,
            },
            "candidates": {
                "total": total_candidates,
            },
        }
        
        return Response(
            success=True,
            message="Dashboard statistics retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        logger.error("Error fetching dashboard stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

