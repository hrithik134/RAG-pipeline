"""
Custom exceptions for the RAG pipeline ingestion system.

This module defines all custom exceptions used throughout the document
ingestion and processing pipeline.
"""


class IngestionError(Exception):
    """Base exception for all ingestion-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class FileValidationError(IngestionError):
    """Raised when file validation fails."""
    pass


class InvalidFileTypeError(FileValidationError):
    """Raised when file type is not supported."""
    
    def __init__(self, filename: str, file_type: str, allowed_types: list):
        message = (
            f"Invalid file type '{file_type}' for file '{filename}'. "
            f"Allowed types: {', '.join(allowed_types)}"
        )
        details = {
            "filename": filename,
            "file_type": file_type,
            "allowed_types": allowed_types
        }
        super().__init__(message, details)


class FileSizeExceededError(FileValidationError):
    """Raised when file size exceeds the limit."""
    
    def __init__(self, filename: str, file_size: int, max_size: int):
        message = (
            f"File '{filename}' size ({file_size / (1024**2):.2f} MB) "
            f"exceeds maximum allowed size ({max_size / (1024**2):.2f} MB)"
        )
        details = {
            "filename": filename,
            "file_size": file_size,
            "max_size": max_size
        }
        super().__init__(message, details)


class DocumentLimitExceededError(FileValidationError):
    """Raised when upload batch exceeds 20 documents."""
    
    def __init__(self, document_count: int, max_documents: int = 20):
        message = (
            f"Upload batch contains {document_count} documents, "
            f"but maximum allowed is {max_documents}"
        )
        details = {
            "document_count": document_count,
            "max_documents": max_documents
        }
        super().__init__(message, details)


class PageLimitExceededError(IngestionError):
    """Raised when document exceeds 1000 pages."""
    
    def __init__(self, filename: str, page_count: int, max_pages: int = 1000):
        message = (
            f"Document '{filename}' has {page_count} pages, "
            f"but maximum allowed is {max_pages}"
        )
        details = {
            "filename": filename,
            "page_count": page_count,
            "max_pages": max_pages
        }
        super().__init__(message, details)


class DuplicateDocumentError(IngestionError):
    """Raised when a duplicate document is detected."""
    
    def __init__(self, filename: str, existing_doc_id: str, file_hash: str):
        message = (
            f"Document '{filename}' already exists (ID: {existing_doc_id}). "
            f"Duplicate detected via hash: {file_hash[:16]}..."
        )
        details = {
            "filename": filename,
            "existing_document_id": existing_doc_id,
            "file_hash": file_hash
        }
        super().__init__(message, details)


class ExtractionError(IngestionError):
    """Raised when text extraction fails."""
    
    def __init__(self, filename: str, file_type: str, error_details: str):
        message = (
            f"Failed to extract text from '{filename}' ({file_type}): "
            f"{error_details}"
        )
        details = {
            "filename": filename,
            "file_type": file_type,
            "error_details": error_details
        }
        super().__init__(message, details)


class ChunkingError(IngestionError):
    """Raised when text chunking fails."""
    
    def __init__(self, document_id: str, error_details: str):
        message = f"Failed to chunk document {document_id}: {error_details}"
        details = {
            "document_id": document_id,
            "error_details": error_details
        }
        super().__init__(message, details)


class StorageError(IngestionError):
    """Raised when file storage operations fail."""
    
    def __init__(self, operation: str, file_path: str, error_details: str):
        message = (
            f"Storage operation '{operation}' failed for '{file_path}': "
            f"{error_details}"
        )
        details = {
            "operation": operation,
            "file_path": file_path,
            "error_details": error_details
        }
        super().__init__(message, details)


class InsufficientStorageError(StorageError):
    """Raised when disk space is insufficient."""
    
    def __init__(self, required_space: int, available_space: int):
        message = (
            f"Insufficient storage space. Required: {required_space / (1024**2):.2f} MB, "
            f"Available: {available_space / (1024**2):.2f} MB"
        )
        details = {
            "required_space": required_space,
            "available_space": available_space
        }
        super().__init__("disk_space_check", "storage", message)

