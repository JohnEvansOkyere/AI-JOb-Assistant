"""
Interview Stages API Routes
Handles interview stage configuration and candidate progress tracking
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional
from uuid import UUID
from app.schemas.common import Response
from app.models.interview_stage import (
    InterviewStageCreate,
    InterviewStageUpdate,
    CandidateProgressUpdate,
    BulkCreateStagesRequest
)
from app.services.interview_stage_service import InterviewStageService
from app.utils.auth import get_current_user_id
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/interview-stages", tags=["interview-stages"])


@router.get("/templates")
async def get_stage_templates(recruiter_id: UUID = Depends(get_current_user_id)):
    """
    Get available interview stage templates
    
    Returns:
        Dictionary of available templates
    """
    try:
        templates = await InterviewStageService.get_stage_templates()
        
        # Convert to dict format for JSON response
        templates_dict = {}
        for key, template in templates.items():
            templates_dict[key] = {
                "name": template.name,
                "description": template.description,
                "stages": template.stages
            }
        
        return Response(
            success=True,
            message="Templates retrieved successfully",
            data=templates_dict
        )
    except Exception as e:
        logger.error("Error fetching templates", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/jobs/{job_id}/stages/template")
async def create_stages_from_template(
    job_id: UUID,
    template_name: str = Body(..., embed=True, description="Template name: 'quick', 'standard', 'comprehensive'"),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Create interview stages for a job from a template
    
    Args:
        job_id: Job description ID
        template_name: Template name ('quick', 'standard', 'comprehensive')
        recruiter_id: Current user ID
    
    Returns:
        Created stages
    """
    try:
        stages = await InterviewStageService.create_stages_from_template(
            job_id=job_id,
            template_name=template_name,
            recruiter_id=recruiter_id
        )
        
        return Response(
            success=True,
            message=f"Stages created from template '{template_name}' successfully",
            data=stages
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error creating stages from template", error=str(e), job_id=str(job_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/jobs/{job_id}/stages/custom")
async def create_custom_stages(
    job_id: UUID,
    stages: List[dict] = Body(..., description="List of stage configurations"),
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Create custom interview stages for a job
    
    Args:
        job_id: Job description ID
        stages: List of stage configurations, each with: stage_name, stage_type, is_required, order_index
        recruiter_id: Current user ID
    
    Returns:
        Created stages
    """
    try:
        created_stages = await InterviewStageService.create_custom_stages(
            job_id=job_id,
            stages=stages,
            recruiter_id=recruiter_id
        )
        
        return Response(
            success=True,
            message="Custom stages created successfully",
            data=created_stages
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error creating custom stages", error=str(e), job_id=str(job_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/jobs/{job_id}/stages")
async def get_job_stages(
    job_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Get all interview stages for a job
    
    Args:
        job_id: Job description ID
        recruiter_id: Current user ID
    
    Returns:
        List of stages
    """
    try:
        stages = await InterviewStageService.get_stages_for_job(
            job_id=job_id,
            recruiter_id=recruiter_id
        )
        
        return Response(
            success=True,
            message="Stages retrieved successfully",
            data=stages
        )
    except Exception as e:
        logger.error("Error fetching stages", error=str(e), job_id=str(job_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/stages/{stage_id}")
async def update_stage(
    stage_id: UUID,
    updates: InterviewStageUpdate,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Update an interview stage
    
    Args:
        stage_id: Stage ID
        updates: Stage update data
        recruiter_id: Current user ID
    
    Returns:
        Updated stage
    """
    try:
        stage = await InterviewStageService.update_stage(
            stage_id=stage_id,
            updates=updates,
            recruiter_id=recruiter_id
        )
        
        return Response(
            success=True,
            message="Stage updated successfully",
            data=stage
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error updating stage", error=str(e), stage_id=str(stage_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/stages/{stage_id}")
async def delete_stage(
    stage_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Delete an interview stage
    
    Args:
        stage_id: Stage ID
        recruiter_id: Current user ID
    
    Returns:
        Success message
    """
    try:
        await InterviewStageService.delete_stage(
            stage_id=stage_id,
            recruiter_id=recruiter_id
        )
        
        return Response(
            success=True,
            message="Stage deleted successfully",
            data={}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error deleting stage", error=str(e), stage_id=str(stage_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/jobs/{job_id}/candidates/{candidate_id}/progress")
async def get_candidate_progress(
    job_id: UUID,
    candidate_id: UUID,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Get candidate progress for a job
    
    Args:
        job_id: Job description ID
        candidate_id: Candidate ID
        recruiter_id: Current user ID
    
    Returns:
        Candidate progress or null if not started
    """
    try:
        progress = await InterviewStageService.get_candidate_progress(
            candidate_id=candidate_id,
            job_id=job_id,
            recruiter_id=recruiter_id
        )
        
        return Response(
            success=True,
            message="Progress retrieved successfully",
            data=progress
        )
    except Exception as e:
        logger.error("Error fetching candidate progress", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/jobs/{job_id}/candidates/{candidate_id}/progress")
async def update_candidate_progress(
    job_id: UUID,
    candidate_id: UUID,
    updates: CandidateProgressUpdate,
    recruiter_id: UUID = Depends(get_current_user_id)
):
    """
    Update candidate progress for a job
    
    Args:
        job_id: Job description ID
        candidate_id: Candidate ID
        updates: Progress update data
        recruiter_id: Current user ID
    
    Returns:
        Updated progress
    """
    try:
        progress = await InterviewStageService.create_or_update_candidate_progress(
            candidate_id=candidate_id,
            job_id=job_id,
            updates=updates,
            recruiter_id=recruiter_id
        )
        
        return Response(
            success=True,
            message="Progress updated successfully",
            data=progress
        )
    except Exception as e:
        logger.error("Error updating candidate progress", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

