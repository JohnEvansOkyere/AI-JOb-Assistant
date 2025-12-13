"""
Common Schemas
Shared request/response schemas
"""

from pydantic import BaseModel
from typing import Optional, Generic, TypeVar, List

T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    """Generic response wrapper"""
    success: bool = True
    message: str = "Success"
    data: Optional[T] = None


class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response schema"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

