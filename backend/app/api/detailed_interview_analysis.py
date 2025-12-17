"""
Detailed Interview Analysis API Routes
Comprehensive AI-powered interview analysis endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List
from uuid import UUID

from app.schemas.common import Response
from app.services.detailed_interview_analyzer import DetailedInterviewAnalyzer
from app.utils.auth import get_current_user
from app.database import db
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/interview-analysis", tags=["interview-analysis"])


@router.post("/analyze/{interview_id}")
async def analyze_interview(
    interview_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger comprehensive analysis of a completed interview.
    
    This performs deep analysis including:
    - Soft skills assessment (8 categories)
    - Technical skills evaluation
    - Communication analysis
    - Sentiment analysis
    - Behavioral indicators
    - Culture & role fit
    - Hiring recommendation
    
    Args:
        interview_id: ID of the interview to analyze
        current_user: Authenticated recruiter
    
    Returns:
        Complete analysis results
    """
    try:
        # Verify recruiter owns this interview's job
        interview = (
            db.service_client.table("interviews")
            .select("*, job_descriptions(recruiter_id)")
            .eq("id", str(interview_id))
            .execute()
        )
        
        if not interview.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )
        
        job_data = interview.data[0].get("job_descriptions", {})
        if job_data.get("recruiter_id") != str(current_user["id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to analyze this interview"
            )
        
        # Check if interview is completed
        if interview.data[0].get("status") != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Interview must be completed before analysis"
            )
        
        # Run analysis
        analyzer = DetailedInterviewAnalyzer()
        analysis = await analyzer.analyze_interview(interview_id)
        
        return Response(
            success=True,
            message="Interview analysis completed successfully",
            data=analysis
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error analyzing interview", error=str(e), interview_id=str(interview_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/result/{interview_id}")
async def get_interview_analysis(
    interview_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the detailed analysis for an interview.
    
    Args:
        interview_id: ID of the interview
        current_user: Authenticated recruiter
    
    Returns:
        Full detailed analysis or 404 if not found
    """
    try:
        # Verify recruiter owns this interview's job
        interview = (
            db.service_client.table("interviews")
            .select("*, job_descriptions(recruiter_id)")
            .eq("id", str(interview_id))
            .execute()
        )
        
        if not interview.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )
        
        job_data = interview.data[0].get("job_descriptions", {})
        if job_data.get("recruiter_id") != str(current_user["id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this analysis"
            )
        
        # Get analysis
        analyzer = DetailedInterviewAnalyzer()
        analysis = await analyzer.get_analysis(interview_id)
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found. Run /analyze first."
            )
        
        return Response(
            success=True,
            message="Analysis retrieved successfully",
            data=analysis
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting analysis", error=str(e), interview_id=str(interview_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/summary/{interview_id}")
async def get_interview_analysis_summary(
    interview_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a summary of the interview analysis.
    
    Args:
        interview_id: ID of the interview
        current_user: Authenticated recruiter
    
    Returns:
        Analysis summary with key metrics
    """
    try:
        # Verify authorization
        interview = (
            db.service_client.table("interviews")
            .select("*, job_descriptions(recruiter_id)")
            .eq("id", str(interview_id))
            .execute()
        )
        
        if not interview.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )
        
        job_data = interview.data[0].get("job_descriptions", {})
        if job_data.get("recruiter_id") != str(current_user["id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        analyzer = DetailedInterviewAnalyzer()
        summary = await analyzer.get_analysis_summary(interview_id)
        
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        return Response(
            success=True,
            message="Summary retrieved",
            data=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting summary", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/job/{job_id}/interviews")
async def list_job_interview_analyses(
    job_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    List all interview analyses for a job.
    
    Args:
        job_id: Job description ID
        current_user: Authenticated recruiter
    
    Returns:
        List of interview analyses with summaries
    """
    try:
        # Verify recruiter owns the job
        job = (
            db.service_client.table("job_descriptions")
            .select("id")
            .eq("id", str(job_id))
            .eq("recruiter_id", str(current_user["id"]))
            .execute()
        )
        
        if not job.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Get all interviews for this job
        interviews = (
            db.service_client.table("interviews")
            .select("id, candidate_id, status, started_at, completed_at, candidates(full_name, email)")
            .eq("job_description_id", str(job_id))
            .order("created_at", desc=True)
            .execute()
        )
        
        # Get analyses for these interviews
        interview_ids = [i["id"] for i in (interviews.data or [])]
        
        if not interview_ids:
            return Response(
                success=True,
                message="No interviews found",
                data=[]
            )
        
        analyses = (
            db.service_client.table("detailed_interview_analysis")
            .select("*")
            .in_("interview_id", interview_ids)
            .execute()
        )
        
        # Map analyses to interviews
        analysis_map = {a["interview_id"]: a for a in (analyses.data or [])}
        
        result = []
        for interview in (interviews.data or []):
            analysis = analysis_map.get(interview["id"])
            candidate = interview.get("candidates", {})
            
            result.append({
                "interview_id": interview["id"],
                "candidate_name": candidate.get("full_name", "Unknown"),
                "candidate_email": candidate.get("email", ""),
                "status": interview.get("status"),
                "started_at": interview.get("started_at"),
                "completed_at": interview.get("completed_at"),
                "has_analysis": analysis is not None,
                "analysis_summary": {
                    "overall_score": analysis.get("overall_score") if analysis else None,
                    "technical_score": analysis.get("technical_score") if analysis else None,
                    "soft_skills_score": analysis.get("soft_skills_score") if analysis else None,
                    "communication_score": analysis.get("communication_score") if analysis else None,
                    "recommendation": analysis.get("recommendation") if analysis else None,
                    "sentiment": analysis.get("overall_sentiment") if analysis else None,
                    "key_strengths": analysis.get("key_strengths", [])[:3] if analysis else [],
                    "analyzed_at": analysis.get("analyzed_at") if analysis else None,
                } if analysis else None
            })
        
        return Response(
            success=True,
            message=f"Found {len(result)} interviews",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing analyses", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/all-reports")
async def get_all_interview_reports(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all interview analyses for the recruiter's jobs.
    
    Args:
        current_user: Authenticated recruiter
    
    Returns:
        List of all interview analyses
    """
    try:
        # Get all jobs for this recruiter
        jobs = (
            db.service_client.table("job_descriptions")
            .select("id, title")
            .eq("recruiter_id", str(current_user["id"]))
            .execute()
        )
        
        if not jobs.data:
            return Response(
                success=True,
                message="No jobs found",
                data=[]
            )
        
        job_ids = [j["id"] for j in jobs.data]
        job_titles = {j["id"]: j["title"] for j in jobs.data}
        
        # Get all completed interviews for these jobs
        interviews = (
            db.service_client.table("interviews")
            .select("id, job_description_id, candidate_id, status, completed_at, candidates(full_name, email)")
            .in_("job_description_id", job_ids)
            .eq("status", "completed")
            .order("completed_at", desc=True)
            .execute()
        )
        
        if not interviews.data:
            return Response(
                success=True,
                message="No completed interviews found",
                data=[]
            )
        
        interview_ids = [i["id"] for i in interviews.data]
        
        # Get analyses
        analyses = (
            db.service_client.table("detailed_interview_analysis")
            .select("*")
            .in_("interview_id", interview_ids)
            .execute()
        )
        
        analysis_map = {a["interview_id"]: a for a in (analyses.data or [])}
        
        result = []
        for interview in interviews.data:
            analysis = analysis_map.get(interview["id"])
            candidate = interview.get("candidates", {})
            
            result.append({
                "interview_id": interview["id"],
                "job_id": interview["job_description_id"],
                "job_title": job_titles.get(interview["job_description_id"], "Unknown"),
                "candidate_id": interview["candidate_id"],
                "candidate_name": candidate.get("full_name", "Unknown"),
                "candidate_email": candidate.get("email", ""),
                "completed_at": interview.get("completed_at"),
                "has_analysis": analysis is not None,
                "overall_score": analysis.get("overall_score") if analysis else None,
                "technical_score": analysis.get("technical_score") if analysis else None,
                "soft_skills_score": analysis.get("soft_skills_score") if analysis else None,
                "communication_score": analysis.get("communication_score") if analysis else None,
                "recommendation": analysis.get("recommendation") if analysis else None,
                "recommendation_summary": analysis.get("recommendation_summary") if analysis else None,
                "sentiment": analysis.get("overall_sentiment") if analysis else None,
                "analyzed_at": analysis.get("analyzed_at") if analysis else None,
            })
        
        return Response(
            success=True,
            message=f"Found {len(result)} completed interviews",
            data=result
        )
        
    except Exception as e:
        logger.error("Error getting all reports", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/batch-analyze/{job_id}")
async def batch_analyze_interviews(
    job_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Batch analyze all completed interviews for a job.
    
    Args:
        job_id: Job description ID
        current_user: Authenticated recruiter
    
    Returns:
        Summary of batch analysis results
    """
    try:
        # Verify recruiter owns the job
        job = (
            db.service_client.table("job_descriptions")
            .select("id")
            .eq("id", str(job_id))
            .eq("recruiter_id", str(current_user["id"]))
            .execute()
        )
        
        if not job.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Get all completed interviews without analysis
        interviews = (
            db.service_client.table("interviews")
            .select("id")
            .eq("job_description_id", str(job_id))
            .eq("status", "completed")
            .execute()
        )
        
        if not interviews.data:
            return Response(
                success=True,
                message="No completed interviews to analyze",
                data={"analyzed": 0, "failed": 0, "results": []}
            )
        
        interview_ids = [i["id"] for i in interviews.data]
        
        # Check which already have analysis
        existing = (
            db.service_client.table("detailed_interview_analysis")
            .select("interview_id")
            .in_("interview_id", interview_ids)
            .execute()
        )
        
        existing_ids = {e["interview_id"] for e in (existing.data or [])}
        to_analyze = [i for i in interview_ids if i not in existing_ids]
        
        if not to_analyze:
            return Response(
                success=True,
                message="All interviews already analyzed",
                data={"analyzed": 0, "skipped": len(interview_ids), "failed": 0}
            )
        
        # Analyze each interview
        analyzer = DetailedInterviewAnalyzer()
        results = []
        failed = 0
        
        for interview_id in to_analyze:
            try:
                analysis = await analyzer.analyze_interview(UUID(interview_id))
                results.append({
                    "interview_id": interview_id,
                    "success": True,
                    "overall_score": analysis.get("overall_score"),
                })
            except Exception as e:
                logger.error("Batch analysis failed", interview_id=interview_id, error=str(e))
                results.append({
                    "interview_id": interview_id,
                    "success": False,
                    "error": str(e),
                })
                failed += 1
        
        return Response(
            success=True,
            message=f"Batch analysis completed",
            data={
                "analyzed": len(to_analyze) - failed,
                "failed": failed,
                "skipped": len(existing_ids),
                "results": results
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Batch analysis error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

