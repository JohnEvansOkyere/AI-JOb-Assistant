"""
Job Description Model
Pydantic models for job description operations
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class JobDescriptionBase(BaseModel):
    """Base job description model"""
    title: str
    description: str
    requirements: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None  # full-time, part-time, contract, etc.
    experience_level: Optional[str] = None  # junior, mid, senior


class JobDescriptionCreate(JobDescriptionBase):
    """Model for creating a new job description"""
    pass


class JobDescriptionUpdate(BaseModel):
    """Model for updating job description"""
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    is_active: Optional[bool] = None


class JobDescription(JobDescriptionBase):
    """Complete job description model"""
    id: UUID
    recruiter_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

