"""
Job Description Model
Pydantic models for job description operations
"""

from pydantic import BaseModel, field_validator
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
    
    @field_validator('requirements', 'location', 'employment_type', 'experience_level', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        """Convert empty strings to None for optional fields"""
        if v == '':
            return None
        return v


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
    hiring_status: Optional[str] = None  # active, screening, interviewing, filled, closed


class JobDescription(JobDescriptionBase):
    """Complete job description model"""
    id: UUID
    recruiter_id: UUID
    is_active: bool
    hiring_status: str = "active"  # active, screening, interviewing, filled, closed
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PublicJobDescription(JobDescription):
    """Public job description model with company branding fields"""
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None
    company_type: Optional[str] = None
    industry: Optional[str] = None
    headquarters_location: Optional[str] = None
    
    class Config:
        from_attributes = True

