"""
Authentication Schemas
Request/Response schemas for authentication endpoints
"""

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema"""
    user_id: str | None = None


class UserLogin(BaseModel):
    """User login request schema"""
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    """User registration request schema"""
    email: EmailStr
    password: str
    full_name: str | None = None
    company_name: str | None = None
    subscription_plan: str | None = "free"  # Optional: starter, professional, enterprise (defaults to free)

