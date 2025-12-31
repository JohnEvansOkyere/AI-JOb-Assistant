"""
CV Detailed Screening API
Endpoints for comprehensive CV analysis (Resume Worded style)
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from typing import Optional
from uuid import UUID
from app.services.cv_detailed_analyzer import CVDetailedAnalyzer
from app.database import db
from app.utils.auth import get_current_user
from app.utils.rate_limit import rate_limit_ai
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/cv-screening", tags=["CV Detailed Screening"])


@router.post("/analyze/{application_id}")
@rate_limit_ai()  # Limit: 10 requests per hour per user (expensive AI operation)
async def analyze_application_cv(
    request: Request,
    application_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger detailed CV analysis for an application
    """
    try:
        # Check usage limits before expensive AI operation
        from app.services.usage_limit_checker import UsageLimitChecker
        from decimal import Decimal
        
        # Estimate cost for detailed CV analysis (this can be expensive - multiple AI calls)
        # Rough estimate: $0.01-0.05 per analysis
        estimated_cost = Decimal('0.03')
        
        try:
            await UsageLimitChecker.check_all_limits(
                recruiter_id=current_user['id'],
                check_interview_limit=False,
                check_cost_limit=True,
                estimated_cost=estimated_cost
            )
        except Exception as e:
            if hasattr(e, 'limit_type'):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=str(e)
                )
            raise
        
        # Get application with CV
        application = db.service_client.table("job_applications").select(
            "*, cvs(id, parsed_text), job_descriptions(*)"
        ).eq("id", str(application_id)).execute()
        
        if not application.data:
            raise HTTPException(status_code=404, detail="Application not found")
        
        app_data = application.data[0]
        
        # Verify recruiter owns the job
        if app_data.get('job_descriptions', {}).get('recruiter_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to analyze this application")
        
        cv_data = app_data.get('cvs')
        if not cv_data or not cv_data.get('parsed_text'):
            raise HTTPException(status_code=400, detail="No CV text available for analysis")
        
        # Run analysis in background for large CVs
        background_tasks.add_task(
            run_detailed_analysis,
            str(application_id),
            str(cv_data['id']),
            cv_data['parsed_text'],
            app_data.get('job_descriptions', {})
        )
        
        return {
            "success": True,
            "message": "CV analysis started. Results will be available shortly.",
            "application_id": str(application_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error starting CV analysis", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def run_detailed_analysis(
    application_id: str,
    cv_id: str,
    cv_text: str,
    job_description: dict
):
    """Background task to run detailed CV analysis"""
    try:
        analyzer = CVDetailedAnalyzer()
        analysis = await analyzer.analyze_cv(
            cv_text=cv_text,
            job_description=job_description,
            cv_id=UUID(cv_id),
            application_id=UUID(application_id)
        )
        await analyzer.save_analysis(analysis)
        logger.info("Background CV analysis completed", application_id=application_id)
    except Exception as e:
        logger.error("Background CV analysis failed", error=str(e), application_id=application_id)


@router.get("/result/{application_id}")
async def get_detailed_screening_result(
    application_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed CV screening result for an application
    """
    try:
        # Get result with authorization check
        result = db.service_client.table("cv_detailed_screening").select(
            "*, job_applications!inner(job_description_id, job_descriptions!inner(recruiter_id))"
        ).eq("application_id", str(application_id)).execute()
        
        if not result.data:
            # Check if application exists
            app_check = db.service_client.table("job_applications").select(
                "id, job_descriptions!inner(recruiter_id)"
            ).eq("id", str(application_id)).execute()
            
            if not app_check.data:
                raise HTTPException(status_code=404, detail="Application not found")
            
            if app_check.data[0].get('job_descriptions', {}).get('recruiter_id') != current_user['id']:
                raise HTTPException(status_code=403, detail="Not authorized")
            
            return {
                "success": True,
                "data": None,
                "message": "No detailed screening available. Trigger analysis first."
            }
        
        screening_data = result.data[0]
        
        # Verify authorization
        if screening_data.get('job_applications', {}).get('job_descriptions', {}).get('recruiter_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Remove nested auth data
        if 'job_applications' in screening_data:
            del screening_data['job_applications']
        
        return {
            "success": True,
            "data": screening_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching screening result", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{application_id}")
async def get_screening_summary(
    application_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a summary view of the CV screening (scores only)
    """
    try:
        result = db.service_client.table("cv_detailed_screening").select(
            """
            id, application_id, overall_score, format_score, structure_score,
            experience_score, education_score, skills_score, language_score,
            ats_score, impact_score, job_match_score, recommendation,
            top_strengths, critical_issues, screened_at
            """
        ).eq("application_id", str(application_id)).execute()
        
        if not result.data:
            return {"success": True, "data": None}
        
        return {
            "success": True,
            "data": result.data[0]
        }
        
    except Exception as e:
        logger.error("Error fetching screening summary", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}/rankings")
async def get_job_cv_rankings(
    job_id: UUID,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    Get ranked candidates by CV screening score for a job
    """
    try:
        # Verify job ownership
        job = db.service_client.table("job_descriptions").select("id").eq(
            "id", str(job_id)
        ).eq("recruiter_id", current_user['id']).execute()
        
        if not job.data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get all detailed screenings for this job with candidate info
        results = db.service_client.table("cv_detailed_screening").select(
            """
            id, application_id, overall_score, job_match_score, 
            experience_score, skills_score, ats_score, recommendation,
            top_strengths, critical_issues, screened_at,
            job_applications!inner(
                id, candidate_id, status,
                candidates(id, full_name, email),
                job_description_id
            )
            """
        ).eq(
            "job_applications.job_description_id", str(job_id)
        ).order("overall_score", desc=True).limit(limit).execute()
        
        rankings = []
        for r in results.data or []:
            app_data = r.get('job_applications', {})
            candidate = app_data.get('candidates', {})
            
            rankings.append({
                "screening_id": r['id'],
                "application_id": app_data.get('id'),
                "candidate_id": candidate.get('id'),
                "candidate_name": candidate.get('full_name'),
                "candidate_email": candidate.get('email'),
                "overall_score": r['overall_score'],
                "job_match_score": r['job_match_score'],
                "experience_score": r['experience_score'],
                "skills_score": r['skills_score'],
                "ats_score": r['ats_score'],
                "recommendation": r['recommendation'],
                "top_strengths": r['top_strengths'][:3] if r['top_strengths'] else [],
                "critical_issues": r['critical_issues'][:2] if r['critical_issues'] else [],
                "screened_at": r['screened_at'],
                "status": app_data.get('status')
            })
        
        return {
            "success": True,
            "data": rankings,
            "total": len(rankings)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching CV rankings", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-analyze/{job_id}")
async def batch_analyze_job_cvs(
    job_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger detailed CV analysis for all applications of a job
    """
    try:
        # Verify job ownership
        job = db.service_client.table("job_descriptions").select("*").eq(
            "id", str(job_id)
        ).eq("recruiter_id", current_user['id']).execute()
        
        if not job.data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job_data = job.data[0]
        
        # Get applications with CVs that don't have detailed screening yet
        applications = db.service_client.table("job_applications").select(
            "id, cv_id, cvs(id, parsed_text)"
        ).eq("job_description_id", str(job_id)).execute()
        
        # Get existing screenings
        existing = db.service_client.table("cv_detailed_screening").select(
            "application_id"
        ).execute()
        existing_ids = {r['application_id'] for r in (existing.data or [])}
        
        # Filter to unscreened applications
        to_analyze = [
            app for app in (applications.data or [])
            if app['id'] not in existing_ids and app.get('cvs', {}).get('parsed_text')
        ]
        
        # Queue background tasks
        for app in to_analyze:
            cv_data = app.get('cvs', {})
            background_tasks.add_task(
                run_detailed_analysis,
                app['id'],
                cv_data['id'],
                cv_data['parsed_text'],
                job_data
            )
        
        return {
            "success": True,
            "message": f"Started detailed analysis for {len(to_analyze)} applications",
            "queued_count": len(to_analyze),
            "already_analyzed": len(existing_ids & {app['id'] for app in (applications.data or [])})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error starting batch analysis", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all-reports")
async def get_all_cv_reports(
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all CV screening reports for the recruiter's jobs
    """
    try:
        # Get all detailed screenings for recruiter's jobs
        results = db.service_client.table("cv_detailed_screening").select(
            """
            id, application_id, overall_score, job_match_score, 
            recommendation, screened_at,
            job_applications!inner(
                id, candidate_id, job_description_id,
                candidates(id, full_name, email),
                job_descriptions!inner(id, title, recruiter_id)
            )
            """
        ).eq(
            "job_applications.job_descriptions.recruiter_id", current_user['id']
        ).order("screened_at", desc=True).limit(limit).execute()
        
        return results.data or []
        
    except Exception as e:
        logger.error("Error fetching all CV reports", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

