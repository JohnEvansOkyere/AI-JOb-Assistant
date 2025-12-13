"""
Interview Response Model
Pydantic models for interview response operations
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class InterviewResponseBase(BaseModel):
    """Base interview response model"""
    response_text: str
    response_audio_path: Optional[str] = None
    timestamp_seconds: Optional[int] = None


class InterviewResponseCreate(InterviewResponseBase):
    """Model for creating a new interview response"""
    interview_id: UUID
    question_id: UUID


class InterviewResponseUpdate(BaseModel):
    """Model for updating interview response"""
    response_text: Optional[str] = None
    response_audio_path: Optional[str] = None
    timestamp_seconds: Optional[int] = None


class InterviewResponse(InterviewResponseBase):
    """Complete interview response model"""
    id: UUID
    interview_id: UUID
    question_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

