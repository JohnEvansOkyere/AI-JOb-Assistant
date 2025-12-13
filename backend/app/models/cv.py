"""
CV Model
Pydantic models for CV operations
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID


class CVBase(BaseModel):
    """Base CV model"""
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    parsed_text: Optional[str] = None
    parsed_json: Optional[Dict[str, Any]] = None


class CVCreate(CVBase):
    """Model for creating a new CV"""
    candidate_id: UUID
    job_description_id: Optional[UUID] = None


class CVUpdate(BaseModel):
    """Model for updating CV information"""
    parsed_text: Optional[str] = None
    parsed_json: Optional[Dict[str, Any]] = None


class CV(CVBase):
    """Complete CV model"""
    id: UUID
    candidate_id: UUID
    job_description_id: Optional[UUID] = None
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

