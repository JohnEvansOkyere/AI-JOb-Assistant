"""
CV Screening Model
Pydantic models for CV screening results
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal


class CVScreeningResultBase(BaseModel):
    """Base CV screening result model"""
    match_score: Decimal  # 0-100
    skill_match_score: Optional[Decimal] = None
    experience_match_score: Optional[Decimal] = None
    qualification_match_score: Optional[Decimal] = None
    strengths: Optional[List[str]] = None
    gaps: Optional[List[str]] = None
    recommendation: str  # qualified, maybe_qualified, not_qualified
    screening_notes: Optional[str] = None
    screening_details: Optional[Dict[str, Any]] = None


class CVScreeningResultCreate(CVScreeningResultBase):
    """Model for creating screening result"""
    application_id: UUID


class CVScreeningResult(CVScreeningResultBase):
    """Complete CV screening result model"""
    id: UUID
    application_id: UUID
    screened_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

