from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """Generic response model."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Any] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model."""
    success: bool = True
    message: Optional[str] = None
    data: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
