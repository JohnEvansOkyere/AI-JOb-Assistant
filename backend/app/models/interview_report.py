"""
Interview Report Model
Pydantic models for interview report operations
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal


class InterviewReportBase(BaseModel):
    """Base interview report model"""
    skill_match_score: Optional[Decimal] = None  # 0-100
    experience_level: Optional[str] = None  # junior, mid, senior
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    red_flags: Optional[List[str]] = None
    hiring_recommendation: Optional[str] = None  # strong_hire, hire, neutral, no_hire
    recommendation_justification: Optional[str] = None
    full_report: Optional[Dict[str, Any]] = None
    recruiter_notes: Optional[str] = None


class InterviewReportCreate(InterviewReportBase):
    """Model for creating a new interview report"""
    interview_id: UUID


class InterviewReportUpdate(BaseModel):
    """Model for updating interview report"""
    skill_match_score: Optional[Decimal] = None
    experience_level: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    red_flags: Optional[List[str]] = None
    hiring_recommendation: Optional[str] = None
    recommendation_justification: Optional[str] = None
    full_report: Optional[Dict[str, Any]] = None
    recruiter_notes: Optional[str] = None


class InterviewReport(InterviewReportBase):
    """Complete interview report model"""
    id: UUID
    interview_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

