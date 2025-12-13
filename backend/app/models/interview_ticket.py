"""
Interview Ticket Model
Pydantic models for interview ticket operations
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class InterviewTicketBase(BaseModel):
    """Base interview ticket model"""
    ticket_code: str
    is_used: bool = False
    is_expired: bool = False
    expires_at: Optional[datetime] = None


class InterviewTicketCreate(BaseModel):
    """Model for creating a new interview ticket"""
    candidate_id: UUID
    job_description_id: UUID
    expires_at: Optional[datetime] = None


class InterviewTicketUpdate(BaseModel):
    """Model for updating interview ticket"""
    is_used: Optional[bool] = None
    is_expired: Optional[bool] = None
    used_at: Optional[datetime] = None


class InterviewTicket(InterviewTicketBase):
    """Complete interview ticket model"""
    id: UUID
    candidate_id: UUID
    job_description_id: UUID
    used_at: Optional[datetime] = None
    created_at: datetime
    created_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True

