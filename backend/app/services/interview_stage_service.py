"""
Interview Stage Service
Business logic for managing interview stages and candidate progress
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from app.models.interview_stage import (
    InterviewStageCreate, 
    InterviewStageUpdate, 
    CandidateProgressCreate,
    CandidateProgressUpdate,
    InterviewStageTemplate
)
from app.database import db
from app.utils.errors import NotFoundError
import structlog

logger = structlog.get_logger()


# Stage templates
STAGE_TEMPLATES = {
    "quick": InterviewStageTemplate(
        name="Quick",
        description="1-stage process: AI Interview only",
        stages=[
            {"stage_name": "AI Interview", "stage_type": "ai", "is_required": True, "order_index": 1}
        ]
    ),
    "standard": InterviewStageTemplate(
        name="Standard",
        description="2-stage process: AI Interview → Final Interview",
        stages=[
            {"stage_name": "AI Interview", "stage_type": "ai", "is_required": True, "order_index": 1},
            {"stage_name": "Final Interview", "stage_type": "calendar", "is_required": True, "order_index": 2}
        ]
    ),
    "comprehensive": InterviewStageTemplate(
        name="Comprehensive",
        description="3-stage process: Phone Screen → AI Interview → Final Interview",
        stages=[
            {"stage_name": "Phone Screen", "stage_type": "calendar", "is_required": True, "order_index": 1},
            {"stage_name": "AI Interview", "stage_type": "ai", "is_required": True, "order_index": 2},
            {"stage_name": "Final Interview", "stage_type": "calendar", "is_required": True, "order_index": 3}
        ]
    )
}


class InterviewStageService:
    """Service for managing interview stages"""
    
    @staticmethod
    async def get_stage_templates() -> Dict[str, InterviewStageTemplate]:
        """Get available stage templates"""
        return STAGE_TEMPLATES
    
    @staticmethod
    async def create_stages_from_template(
        job_id: UUID, 
        template_name: str,
        recruiter_id: UUID
    ) -> List[dict]:
        """
        Create stages for a job from a template
        
        Args:
            job_id: Job description ID
            template_name: Template name ('quick', 'standard', 'comprehensive')
            recruiter_id: Recruiter ID (for authorization)
        
        Returns:
            List of created stages
        """
        # Verify recruiter owns the job
        job_response = db.service_client.table("job_descriptions").select("id").eq("id", str(job_id)).eq("recruiter_id", str(recruiter_id)).execute()
        if not job_response.data:
            raise NotFoundError("Job description", str(job_id))
        
        # Get template
        if template_name not in STAGE_TEMPLATES:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = STAGE_TEMPLATES[template_name]
        
        # Check if stages already exist
        existing_stages = await InterviewStageService.get_stages_for_job(job_id, recruiter_id)
        if existing_stages:
            raise ValueError("Stages already exist for this job. Delete existing stages first or use update.")
        
        # Create stages
        stages_to_create = []
        for idx, stage_config in enumerate(template.stages, start=1):
            stage_data = {
                "job_id": str(job_id),
                "stage_number": idx,
                "stage_name": stage_config["stage_name"],
                "stage_type": stage_config["stage_type"],
                "is_required": stage_config.get("is_required", True),
                "order_index": stage_config.get("order_index", idx)
            }
            stages_to_create.append(stage_data)
        
        # Insert all stages
        response = db.service_client.table("job_interview_stages").insert(stages_to_create).execute()
        
        if not response.data:
            raise Exception("Failed to create stages")
        
        logger.info(
            "Stages created from template",
            job_id=str(job_id),
            template_name=template_name,
            stage_count=len(response.data)
        )
        
        return response.data
    
    @staticmethod
    async def create_custom_stages(
        job_id: UUID,
        stages: List[dict],
        recruiter_id: UUID
    ) -> List[dict]:
        """
        Create custom stages for a job
        
        Args:
            job_id: Job description ID
            stages: List of stage configurations
            recruiter_id: Recruiter ID (for authorization)
        
        Returns:
            List of created stages
        """
        # Verify recruiter owns the job
        job_response = db.service_client.table("job_descriptions").select("id").eq("id", str(job_id)).eq("recruiter_id", str(recruiter_id)).execute()
        if not job_response.data:
            raise NotFoundError("Job description", str(job_id))
        
        # Check if stages already exist
        existing_stages = await InterviewStageService.get_stages_for_job(job_id, recruiter_id)
        if existing_stages:
            raise ValueError("Stages already exist for this job. Delete existing stages first or use update.")
        
        # Validate: only one AI stage
        ai_count = sum(1 for stage in stages if stage.get("stage_type") == "ai")
        if ai_count > 1:
            raise ValueError("Only one AI interview stage is allowed per job")
        
        # Prepare stages for insertion
        stages_to_create = []
        for idx, stage_config in enumerate(stages, start=1):
            stage_data = {
                "job_id": str(job_id),
                "stage_number": idx,
                "stage_name": stage_config["stage_name"],
                "stage_type": stage_config["stage_type"],
                "is_required": stage_config.get("is_required", True),
                "order_index": stage_config.get("order_index", idx)
            }
            stages_to_create.append(stage_data)
        
        # Insert all stages
        response = db.service_client.table("job_interview_stages").insert(stages_to_create).execute()
        
        if not response.data:
            raise Exception("Failed to create stages")
        
        logger.info(
            "Custom stages created",
            job_id=str(job_id),
            stage_count=len(response.data)
        )
        
        return response.data
    
    @staticmethod
    async def get_stages_for_job(
        job_id: UUID,
        recruiter_id: UUID
    ) -> List[dict]:
        """
        Get all stages for a job
        
        Args:
            job_id: Job description ID
            recruiter_id: Recruiter ID (for authorization)
        
        Returns:
            List of stages, ordered by order_index
        """
        # Verify recruiter owns the job
        job_response = db.service_client.table("job_descriptions").select("id").eq("id", str(job_id)).eq("recruiter_id", str(recruiter_id)).execute()
        if not job_response.data:
            raise NotFoundError("Job description", str(job_id))
        
        # Get stages
        response = db.service_client.table("job_interview_stages").select("*").eq("job_id", str(job_id)).order("order_index").execute()
        
        return response.data or []
    
    @staticmethod
    async def update_stage(
        stage_id: UUID,
        updates: InterviewStageUpdate,
        recruiter_id: UUID
    ) -> dict:
        """
        Update a stage
        
        Args:
            stage_id: Stage ID
            updates: Update data
            recruiter_id: Recruiter ID (for authorization)
        
        Returns:
            Updated stage
        """
        # Get stage and verify ownership via job
        stage_response = db.service_client.table("job_interview_stages").select("*").eq("id", str(stage_id)).execute()
        if not stage_response.data:
            raise NotFoundError("Interview stage", str(stage_id))
        
        stage = stage_response.data[0]
        job_id = UUID(stage["job_id"])
        
        # Verify recruiter owns the job
        job_response = db.service_client.table("job_descriptions").select("recruiter_id").eq("id", str(job_id)).eq("recruiter_id", str(recruiter_id)).execute()
        if not job_response.data:
            raise NotFoundError("Interview stage", str(stage_id))
        
        # Check if locked
        if stage.get("is_locked"):
            raise ValueError("Stage is locked and cannot be modified. Unlock it first or create new stages.")
        
        # Prepare update data
        update_data = updates.model_dump(exclude_unset=True)
        
        # Validate: if changing to AI type, check no other AI stage exists
        if update_data.get("stage_type") == "ai":
            job_id = stage.get("job_id")
            other_ai_stages = db.service_client.table("job_interview_stages").select("id").eq("job_id", str(job_id)).eq("stage_type", "ai").neq("id", str(stage_id)).execute()
            if other_ai_stages.data:
                raise ValueError("Only one AI interview stage is allowed per job")
        
        # Update
        response = db.service_client.table("job_interview_stages").update(update_data).eq("id", str(stage_id)).execute()
        
        if not response.data:
            raise NotFoundError("Interview stage", str(stage_id))
        
        logger.info("Stage updated", stage_id=str(stage_id))
        return response.data[0]
    
    @staticmethod
    async def delete_stage(
        stage_id: UUID,
        recruiter_id: UUID
    ) -> bool:
        """
        Delete a stage
        
        Args:
            stage_id: Stage ID
            recruiter_id: Recruiter ID (for authorization)
        
        Returns:
            True if deleted
        """
        # Get stage and verify ownership
        stage_response = db.service_client.table("job_interview_stages").select("*").eq("id", str(stage_id)).execute()
        if not stage_response.data:
            raise NotFoundError("Interview stage", str(stage_id))
        
        stage = stage_response.data[0]
        job_id = UUID(stage["job_id"])
        
        # Verify recruiter owns the job
        job_response = db.service_client.table("job_descriptions").select("recruiter_id").eq("id", str(job_id)).eq("recruiter_id", str(recruiter_id)).execute()
        if not job_response.data:
            raise NotFoundError("Interview stage", str(stage_id))
        
        # Check if locked
        if stage.get("is_locked"):
            raise ValueError("Stage is locked and cannot be deleted")
        
        # Delete
        db.service_client.table("job_interview_stages").delete().eq("id", str(stage_id)).execute()
        
        logger.info("Stage deleted", stage_id=str(stage_id))
        return True
    
    @staticmethod
    async def get_candidate_progress(
        candidate_id: UUID,
        job_id: UUID,
        recruiter_id: UUID
    ) -> Optional[dict]:
        """
        Get candidate progress for a job
        
        Args:
            candidate_id: Candidate ID
            job_id: Job description ID
            recruiter_id: Recruiter ID (for authorization)
        
        Returns:
            Candidate progress or None
        """
        # Verify recruiter owns the job
        job_response = db.service_client.table("job_descriptions").select("id").eq("id", str(job_id)).eq("recruiter_id", str(recruiter_id)).execute()
        if not job_response.data:
            raise NotFoundError("Job description", str(job_id))
        
        # Get progress
        response = db.service_client.table("candidate_interview_progress").select("*").eq("candidate_id", str(candidate_id)).eq("job_id", str(job_id)).execute()
        
        if response.data:
            return response.data[0]
        return None
    
    @staticmethod
    async def create_or_update_candidate_progress(
        candidate_id: UUID,
        job_id: UUID,
        updates: CandidateProgressUpdate,
        recruiter_id: UUID
    ) -> dict:
        """
        Create or update candidate progress
        
        Args:
            candidate_id: Candidate ID
            job_id: Job description ID
            updates: Progress update data
            recruiter_id: Recruiter ID (for authorization)
        
        Returns:
            Candidate progress
        """
        # Verify recruiter owns the job
        job_response = db.service_client.table("job_descriptions").select("id").eq("id", str(job_id)).eq("recruiter_id", str(recruiter_id)).execute()
        if not job_response.data:
            raise NotFoundError("Job description", str(job_id))
        
        # Check if progress exists
        existing = await InterviewStageService.get_candidate_progress(candidate_id, job_id, recruiter_id)
        
        update_data = updates.model_dump(exclude_unset=True)
        
        if existing:
            # Update
            response = db.service_client.table("candidate_interview_progress").update(update_data).eq("id", existing["id"]).execute()
        else:
            # Create
            progress_data = {
                "candidate_id": str(candidate_id),
                "job_id": str(job_id),
                **update_data
            }
            response = db.service_client.table("candidate_interview_progress").insert(progress_data).execute()
        
        if not response.data:
            raise Exception("Failed to update candidate progress")
        
        logger.info(
            "Candidate progress updated",
            candidate_id=str(candidate_id),
            job_id=str(job_id)
        )
        
        return response.data[0]

