"""
Pydantic schemas for document-related API requests and responses.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.document import DocumentStatus
from app.models.upload import UploadStatus


# ============================================================================
# Chunk Schemas
# ============================================================================

class ChunkResponse(BaseModel):
    """Response schema for a single chunk."""
    
    id: UUID
    chunk_index: int
    token_count: int
    start_char: int
    end_char: int
    page_number: Optional[int] = None
    content_preview: str = Field(..., description="First 100 characters of content")
    has_embedding: bool = Field(..., description="Whether chunk has been embedded")
    
    model_config = {
        "from_attributes": True
    }
    
    @field_validator('content_preview', mode='before')
    @classmethod
    def create_preview(cls, v, info):
        """Create preview from content if needed."""
        if isinstance(v, str) and len(v) > 100:
            return v[:100] + "..."
        return v


class ChunkDetailResponse(BaseModel):
    """Detailed response schema for a chunk including full content."""
    
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    token_count: int
    start_char: int
    end_char: int
    page_number: Optional[int] = None
    embedding_id: Optional[str] = None
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }


# ============================================================================
# Document Schemas
# ============================================================================

class DocumentUploadResponse(BaseModel):
    """Response schema for uploaded document."""
    
    id: UUID
    filename: str
    file_size: int
    file_type: str
    page_count: int
    status: DocumentStatus
    created_at: datetime
    error_message: Optional[str] = None
    
    model_config = {
        "from_attributes": True
    }


class DocumentDetailResponse(BaseModel):
    """Detailed response schema for a document."""
    
    id: UUID
    upload_id: UUID
    filename: str
    file_path: str
    file_size: int
    file_type: str
    file_hash: str
    page_count: int
    total_chunks: int
    status: DocumentStatus
    created_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    chunks: List[ChunkResponse] = []
    
    model_config = {
        "from_attributes": True
    }


class DocumentListResponse(BaseModel):
    """Response schema for document list."""
    
    id: UUID
    filename: str
    file_size: int
    file_type: str
    page_count: int
    total_chunks: int
    status: DocumentStatus
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }


# ============================================================================
# Upload Batch Schemas
# ============================================================================

class UploadBatchResponse(BaseModel):
    """Response schema for upload batch."""
    
    id: UUID
    upload_batch_id: str
    status: UploadStatus
    total_documents: int
    successful_documents: int = 0
    failed_documents: int = 0
    created_at: datetime
    completed_at: Optional[datetime] = None
    documents: List[DocumentUploadResponse] = []
    
    model_config = {
        "from_attributes": True
    }


class UploadProgressResponse(BaseModel):
    """Response schema for upload progress."""
    
    upload_id: UUID
    upload_batch_id: str
    status: UploadStatus
    total_documents: int
    processed_documents: int
    successful_documents: int
    failed_documents: int
    progress_percentage: float
    
    model_config = {
        "from_attributes": True
    }


# ============================================================================
# Request Schemas
# ============================================================================

class DocumentQueryParams(BaseModel):
    """Query parameters for document listing."""
    
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=10, ge=1, le=100, description="Number of records to return")
    status: Optional[DocumentStatus] = Field(default=None, description="Filter by status")
    upload_id: Optional[UUID] = Field(default=None, description="Filter by upload batch")


class ChunkQueryParams(BaseModel):
    """Query parameters for chunk listing."""
    
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=20, ge=1, le=100, description="Number of records to return")
    document_id: Optional[UUID] = Field(default=None, description="Filter by document")
    has_embedding: Optional[bool] = Field(default=None, description="Filter by embedding status")


# ============================================================================
# Statistics Schemas
# ============================================================================

class DocumentStatistics(BaseModel):
    """Statistics about documents."""
    
    total_documents: int
    total_pages: int
    total_chunks: int
    total_size_bytes: int
    documents_by_status: dict
    documents_by_type: dict
    average_pages_per_document: float
    average_chunks_per_document: float


class UploadStatistics(BaseModel):
    """Statistics about uploads."""
    
    total_uploads: int
    total_documents: int
    successful_uploads: int
    failed_uploads: int
    pending_uploads: int
    uploads_by_date: dict


# ============================================================================
# Error Response Schemas
# ============================================================================

class ErrorDetail(BaseModel):
    """Detailed error information."""
    
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str
    message: str
    details: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None


# ============================================================================
# Validation Schemas
# ============================================================================

class FileValidationResult(BaseModel):
    """Result of file validation."""
    
    filename: str
    valid: bool
    file_hash: Optional[str] = None
    errors: List[str] = []


class BatchValidationResult(BaseModel):
    """Result of batch validation."""
    
    valid: bool
    total_files: int
    valid_files: int
    invalid_files: int
    file_results: List[FileValidationResult]
    errors: List[str] = []

