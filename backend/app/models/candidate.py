"""
Candidate Model
Pydantic models for candidate operations
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID


class CandidateBase(BaseModel):
    """Base candidate model with common fields"""
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None


class CandidateCreate(CandidateBase):
    """Model for creating a new candidate"""
    pass


class CandidateUpdate(BaseModel):
    """Model for updating candidate information"""
    full_name: Optional[str] = None
    phone: Optional[str] = None


class Candidate(CandidateBase):
    """Complete candidate model"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

