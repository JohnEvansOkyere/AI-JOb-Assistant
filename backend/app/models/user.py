"""
User Model
Pydantic models for user/recruiter operations
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID


class UserBase(BaseModel):
    """Base user model with common fields"""
    email: EmailStr
    full_name: Optional[str] = None
    company_name: Optional[str] = None


class UserCreate(UserBase):
    """Model for creating a new user"""
    pass


class UserUpdate(BaseModel):
    """Model for updating user information"""
    full_name: Optional[str] = None
    company_name: Optional[str] = None


class User(UserBase):
    """Complete user model"""
    id: UUID
    is_admin: bool = False
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

