"""
Pagination models and helpers for list endpoints.
"""

from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field, computed_field


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    limit: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    
    @computed_field
    @property
    def pages(self) -> int:
        """Total number of pages."""
        if self.total == 0:
            return 0
        return (self.total + self.limit - 1) // self.limit
    
    @computed_field
    @property
    def has_next(self) -> bool:
        """Whether there is a next page."""
        return self.page < self.pages
    
    @computed_field
    @property
    def has_prev(self) -> bool:
        """Whether there is a previous page."""
        return self.page > 1
    
    @computed_field
    @property
    def next_page(self) -> Optional[int]:
        """Next page number if available."""
        return self.page + 1 if self.has_next else None
    
    @computed_field
    @property
    def prev_page(self) -> Optional[int]:
        """Previous page number if available."""
        return self.page - 1 if self.has_prev else None
    
    class Config:
        json_schema_extra = {
            "example": {
                "page": 2,
                "limit": 10,
                "total": 150,
                "pages": 15,
                "has_next": True,
                "has_prev": True,
                "next_page": 3,
                "prev_page": 1
            }
        }


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    
    items: List[T] = Field(..., description="List of items for current page")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    success: bool = Field(default=True, description="Request success status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {"id": "123e4567-e89b-12d3-a456-426614174000", "name": "Item 1"},
                    {"id": "123e4567-e89b-12d3-a456-426614174001", "name": "Item 2"}
                ],
                "pagination": {
                    "page": 1,
                    "limit": 10,
                    "total": 150,
                    "pages": 15,
                    "has_next": True,
                    "has_prev": False,
                    "next_page": 2,
                    "prev_page": None
                },
                "success": True
            }
        }


class PaginationParams(BaseModel):
    """Common pagination query parameters."""
    
    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-indexed)"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Items per page (max 100)"
    )
    
    @property
    def skip(self) -> int:
        """Calculate skip value for database queries."""
        return (self.page - 1) * self.limit
    
    def create_response(
        self,
        items: List[T],
        total: int
    ) -> PaginatedResponse[T]:
        """Create a paginated response from query results."""
        return PaginatedResponse(
            items=items,
            pagination=PaginationMeta(
                page=self.page,
                limit=self.limit,
                total=total
            ),
            success=True
        )

