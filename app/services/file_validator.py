"""
File validation service for document uploads.

This module provides validation for uploaded files including type checking,
size validation, batch limits, hash calculation, and duplicate detection.
"""

import hashlib
from pathlib import Path
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document
from app.utils.exceptions import (
    InvalidFileTypeError,
    FileSizeExceededError,
    DocumentLimitExceededError,
    DuplicateDocumentError,
    FileValidationError,
)


class FileValidator:
    """Validates uploaded files before processing."""
    
    def __init__(self):
        """Initialize file validator with settings."""
        self.allowed_extensions = settings.allowed_extensions_list
        self.max_file_size = settings.max_file_size_bytes
        self.max_documents = settings.max_documents_per_upload
    
    def validate_file_type(self, file: UploadFile) -> bool:
        """
        Validate that file type is allowed.
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            True if file type is valid
            
        Raises:
            InvalidFileTypeError: If file type is not allowed
        """
        if not file.filename:
            raise FileValidationError(
                message="File has no filename",
                details={"filename": None}
            )
        
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in self.allowed_extensions:
            raise InvalidFileTypeError(
                filename=file.filename,
                file_type=file_ext,
                allowed_types=self.allowed_extensions
            )
        
        return True
    
    async def validate_file_size(self, file: UploadFile) -> bool:
        """
        Validate that file size is within limits.
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            True if file size is valid
            
        Raises:
            FileSizeExceededError: If file exceeds size limit
        """
        # Read file to get size
        content = await file.read()
        file_size = len(content)
        
        # Reset file pointer
        await file.seek(0)
        
        if file_size > self.max_file_size:
            raise FileSizeExceededError(
                filename=file.filename,
                file_size=file_size,
                max_size=self.max_file_size
            )
        
        return True
    
    def validate_batch_size(self, files: List[UploadFile]) -> bool:
        """
        Validate that batch contains acceptable number of files.
        
        Args:
            files: List of UploadFile objects
            
        Returns:
            True if batch size is valid
            
        Raises:
            DocumentLimitExceededError: If batch exceeds document limit
        """
        file_count = len(files)
        
        if file_count > self.max_documents:
            raise DocumentLimitExceededError(
                document_count=file_count,
                max_documents=self.max_documents
            )
        
        if file_count == 0:
            raise FileValidationError(
                message="No files provided in upload batch",
                details={"file_count": 0}
            )
        
        return True
    
    async def calculate_file_hash(self, file: UploadFile) -> str:
        """
        Calculate SHA-256 hash of file content.
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Hexadecimal hash string
        """
        hasher = hashlib.sha256()
        
        # Read file in chunks to handle large files
        chunk_size = 8192
        while chunk := await file.read(chunk_size):
            hasher.update(chunk)
        
        # Reset file pointer
        await file.seek(0)
        
        return hasher.hexdigest()
    
    def calculate_file_hash_from_path(self, file_path: str) -> str:
        """
        Calculate SHA-256 hash from file path (synchronous).
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hexadecimal hash string
        """
        hasher = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        
        return hasher.hexdigest()
    
    def check_duplicate(
        self,
        file_hash: str,
        db: Session,
        filename: Optional[str] = None
    ) -> Optional[Document]:
        """
        Check if a document with the same hash already exists.
        
        Args:
            file_hash: SHA-256 hash of the file
            db: Database session
            filename: Optional filename for error message
            
        Returns:
            Existing Document if duplicate found, None otherwise
            
        Raises:
            DuplicateDocumentError: If duplicate is found
        """
        existing_doc = db.query(Document).filter(
            Document.file_hash == file_hash
        ).first()
        
        if existing_doc:
            raise DuplicateDocumentError(
                filename=filename or "unknown",
                existing_doc_id=str(existing_doc.id),
                file_hash=file_hash
            )
        
        return None
    
    async def validate_file(
        self,
        file: UploadFile,
        db: Session,
        check_duplicates: bool = True
    ) -> dict:
        """
        Perform all validations on a single file.
        
        Args:
            file: FastAPI UploadFile object
            db: Database session
            check_duplicates: Whether to check for duplicates
            
        Returns:
            Dictionary with validation results including file hash
            
        Raises:
            Various validation errors if validation fails
        """
        # Validate file type
        self.validate_file_type(file)
        
        # Validate file size
        await self.validate_file_size(file)
        
        # Calculate hash
        file_hash = await self.calculate_file_hash(file)
        
        # Check for duplicates if requested
        if check_duplicates:
            self.check_duplicate(file_hash, db, file.filename)
        
        return {
            "filename": file.filename,
            "file_hash": file_hash,
            "valid": True
        }
    
    async def validate_batch(
        self,
        files: List[UploadFile],
        db: Session,
        check_duplicates: bool = True
    ) -> List[dict]:
        """
        Validate an entire batch of files.
        
        Args:
            files: List of UploadFile objects
            db: Database session
            check_duplicates: Whether to check for duplicates
            
        Returns:
            List of validation results for each file
            
        Raises:
            Various validation errors if any validation fails
        """
        # Validate batch size
        self.validate_batch_size(files)
        
        # Validate each file
        results = []
        for file in files:
            result = await self.validate_file(file, db, check_duplicates)
            results.append(result)
        
        return results

