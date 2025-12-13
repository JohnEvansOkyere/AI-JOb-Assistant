"""
Interview Model
Pydantic models for interview operations
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class InterviewBase(BaseModel):
    """Base interview model"""
    status: str = "pending"  # pending, in_progress, completed, cancelled
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    audio_file_path: Optional[str] = None
    transcript: Optional[str] = None


class InterviewCreate(BaseModel):
    """Model for creating a new interview"""
    candidate_id: UUID
    job_description_id: UUID
    ticket_id: UUID


class InterviewUpdate(BaseModel):
    """Model for updating interview"""
    status: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    audio_file_path: Optional[str] = None
    transcript: Optional[str] = None


class Interview(InterviewBase):
    """Complete interview model"""
    id: UUID
    candidate_id: UUID
    job_description_id: UUID
    ticket_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

