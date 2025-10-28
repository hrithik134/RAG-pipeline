"""
Pydantic schemas for request/response validation.
"""

from app.schemas.document import (
    ChunkDetailResponse,
    ChunkQueryParams,
    ChunkResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentQueryParams,
    DocumentStatistics,
    DocumentUploadResponse,
    ErrorDetail,
    ErrorResponse,
    UploadBatchResponse,
    UploadProgressResponse,
    UploadStatistics,
)
from app.schemas.errors import (
    APIError,
    ErrorResponse as EnhancedErrorResponse,
    RateLimitErrorResponse,
    ValidationErrorDetail,
    ValidationErrorResponse,
)
from app.schemas.pagination import (
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
)

__all__ = [
    # Document schemas
    "ChunkDetailResponse",
    "ChunkQueryParams",
    "ChunkResponse",
    "DocumentDetailResponse",
    "DocumentListResponse",
    "DocumentQueryParams",
    "DocumentStatistics",
    "DocumentUploadResponse",
    "ErrorDetail",
    "ErrorResponse",
    "UploadBatchResponse",
    "UploadProgressResponse",
    "UploadStatistics",
    # Error schemas
    "APIError",
    "EnhancedErrorResponse",
    "RateLimitErrorResponse",
    "ValidationErrorDetail",
    "ValidationErrorResponse",
    # Pagination schemas
    "PaginatedResponse",
    "PaginationMeta",
    "PaginationParams",
]
