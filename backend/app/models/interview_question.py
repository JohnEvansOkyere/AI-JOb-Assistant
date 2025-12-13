"""
Interview Question Model
Pydantic models for interview question operations
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class InterviewQuestionBase(BaseModel):
    """Base interview question model"""
    question_text: str
    question_type: Optional[str] = None  # warmup, skill, experience, soft_skill, wrapup
    skill_category: Optional[str] = None
    order_index: int


class InterviewQuestionCreate(InterviewQuestionBase):
    """Model for creating a new interview question"""
    interview_id: UUID


class InterviewQuestionUpdate(BaseModel):
    """Model for updating interview question"""
    asked_at: Optional[datetime] = None


class InterviewQuestion(InterviewQuestionBase):
    """Complete interview question model"""
    id: UUID
    interview_id: UUID
    asked_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

