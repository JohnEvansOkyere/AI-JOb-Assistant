"""
Interview Stage Models
Pydantic models for interview stage configuration and candidate progress
"""

from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class InterviewStageBase(BaseModel):
    """Base interview stage model"""
    stage_number: int
    stage_name: str
    stage_type: str  # 'ai' or 'calendar'
    is_required: bool = True
    order_index: int


class InterviewStageCreate(InterviewStageBase):
    """Model for creating a new interview stage"""
    job_id: UUID
    
    @field_validator('stage_type')
    @classmethod
    def validate_stage_type(cls, v: str) -> str:
        if v not in ['ai', 'calendar']:
            raise ValueError("stage_type must be 'ai' or 'calendar'")
        return v
    
    @field_validator('stage_number', 'order_index')
    @classmethod
    def validate_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Must be greater than 0")
        return v


class InterviewStageUpdate(BaseModel):
    """Model for updating an interview stage"""
    stage_name: Optional[str] = None
    stage_type: Optional[str] = None
    is_required: Optional[bool] = None
    order_index: Optional[int] = None
    
    @field_validator('stage_type')
    @classmethod
    def validate_stage_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ['ai', 'calendar']:
            raise ValueError("stage_type must be 'ai' or 'calendar'")
        return v


class InterviewStage(InterviewStageBase):
    """Complete interview stage model"""
    id: UUID
    job_id: UUID
    is_locked: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class InterviewStageTemplate(BaseModel):
    """Template for creating interview stages"""
    name: str  # "Quick", "Standard", "Comprehensive", "Custom"
    description: str
    stages: List[dict]  # List of stage configs: [{"stage_name": "AI Interview", "stage_type": "ai", ...}]


class CandidateProgressBase(BaseModel):
    """Base candidate progress model"""
    candidate_id: UUID
    job_id: UUID
    current_stage_number: Optional[int] = None
    status: str = "not_started"  # not_started, in_progress, completed, rejected, offer, accepted
    completed_stages: List[int] = []  # Array of stage numbers
    skipped_stages: List[int] = []  # Array of stage numbers


class CandidateProgressCreate(CandidateProgressBase):
    """Model for creating candidate progress"""
    pass


class CandidateProgressUpdate(BaseModel):
    """Model for updating candidate progress"""
    current_stage_number: Optional[int] = None
    status: Optional[str] = None
    completed_stages: Optional[List[int]] = None
    skipped_stages: Optional[List[int]] = None
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ['not_started', 'in_progress', 'completed', 'rejected', 'offer', 'accepted']:
            raise ValueError("Invalid status")
        return v


class CandidateProgress(CandidateProgressBase):
    """Complete candidate progress model"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BulkCreateStagesRequest(BaseModel):
    """Request model for bulk creating stages from template"""
    job_id: UUID
    template_name: Optional[str] = None  # "quick", "standard", "comprehensive"
    stages: Optional[List[InterviewStageBase]] = None  # For custom template
    
    @field_validator('template_name')
    @classmethod
    def validate_template_or_stages(cls, v: Optional[str], info) -> Optional[str]:
        # Either template_name or stages must be provided
        if v is None and not info.data.get('stages'):
            raise ValueError("Either template_name or stages must be provided")
        return v

