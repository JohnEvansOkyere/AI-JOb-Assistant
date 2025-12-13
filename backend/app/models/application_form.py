"""
Application Form Models
Pydantic models for custom application form fields
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class ApplicationFormFieldBase(BaseModel):
    """Base application form field model"""
    field_key: str = Field(..., description="Unique key for the field (e.g., 'years_experience')")
    field_label: str = Field(..., description="Display label")
    field_type: str = Field(..., description="Field type: text, email, tel, number, textarea, select, checkbox, radio, date")
    field_options: Optional[Dict[str, Any]] = None  # For select, radio, checkbox
    is_required: bool = False
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None
    order_index: int = 0


class ApplicationFormFieldCreate(ApplicationFormFieldBase):
    """Model for creating a form field"""
    job_description_id: UUID


class ApplicationFormFieldUpdate(BaseModel):
    """Model for updating a form field"""
    field_label: Optional[str] = None
    field_type: Optional[str] = None
    field_options: Optional[Dict[str, Any]] = None
    is_required: Optional[bool] = None
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None
    order_index: Optional[int] = None


class ApplicationFormField(ApplicationFormFieldBase):
    """Complete form field model"""
    id: UUID
    job_description_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ApplicationFormResponseCreate(BaseModel):
    """Model for creating a form response"""
    application_id: UUID
    field_key: str
    field_value: str


class ApplicationFormResponse(BaseModel):
    """Form response model"""
    id: UUID
    application_id: UUID
    field_key: str
    field_value: str
    created_at: datetime
    
    class Config:
        from_attributes = True

