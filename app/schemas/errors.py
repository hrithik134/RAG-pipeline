"""
Enhanced error models for consistent API error responses.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class APIError(BaseModel):
    """Detailed error information."""
    
    code: str = Field(..., description="Error code (e.g., FILE_TOO_LARGE)")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional error details and context"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the error occurred"
    )
    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique request identifier for tracking"
    )


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""
    
    error: APIError
    success: bool = Field(default=False, description="Always false for errors")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": "File size exceeds 50MB limit",
                    "details": {
                        "file_size": "75MB",
                        "max_size": "50MB",
                        "suggestion": "Please compress or split the file"
                    },
                    "timestamp": "2025-10-27T10:30:00Z",
                    "request_id": "123e4567-e89b-12d3-a456-426614174000"
                },
                "success": False
            }
        }


class ValidationErrorDetail(BaseModel):
    """Validation error detail."""
    
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    value: Optional[Any] = Field(None, description="Invalid value provided")


class ValidationErrorResponse(BaseModel):
    """Response for validation errors."""
    
    error: APIError
    validation_errors: list[ValidationErrorDetail] = Field(
        ..., 
        description="List of validation errors"
    )
    success: bool = Field(default=False)
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {"field_count": 2},
                    "timestamp": "2025-10-27T10:30:00Z",
                    "request_id": "123e4567-e89b-12d3-a456-426614174000"
                },
                "validation_errors": [
                    {
                        "field": "query",
                        "message": "Query text must be between 3 and 1000 characters",
                        "value": "Hi"
                    },
                    {
                        "field": "top_k",
                        "message": "top_k must be between 1 and 100",
                        "value": 150
                    }
                ],
                "success": False
            }
        }


class RateLimitErrorResponse(BaseModel):
    """Response for rate limit exceeded errors."""
    
    error: APIError
    retry_after: int = Field(..., description="Seconds until rate limit resets")
    limit: str = Field(..., description="Rate limit (e.g., '10/hour')")
    success: bool = Field(default=False)
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests",
                    "details": {
                        "endpoint": "/v1/documents/upload",
                        "limit": "10 per hour",
                        "suggestion": "Please wait before making more requests"
                    },
                    "timestamp": "2025-10-27T10:30:00Z",
                    "request_id": "123e4567-e89b-12d3-a456-426614174000"
                },
                "retry_after": 1800,
                "limit": "10/hour",
                "success": False
            }
        }

