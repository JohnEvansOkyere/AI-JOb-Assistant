"""
Job Application Model
Pydantic models for job application operations
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID


class JobApplicationBase(BaseModel):
    """Base job application model"""
    cover_letter: Optional[str] = None
    status: str = "pending"  # pending, screening, qualified, rejected, interview_scheduled


class JobApplicationCreate(BaseModel):
    """Model for creating a job application"""
    job_description_id: UUID
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    cover_letter: Optional[str] = None


class JobApplicationUpdate(BaseModel):
    """Model for updating job application"""
    status: Optional[str] = None
    cover_letter: Optional[str] = None


class JobApplication(JobApplicationBase):
    """Complete job application model"""
    id: UUID
    job_description_id: UUID
    candidate_id: UUID
    cv_id: Optional[UUID] = None
    applied_at: datetime
    screened_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

