"""Unit tests for file validation functionality."""

import pytest
from fastapi import UploadFile
from unittest.mock import Mock

from app.utils.exceptions import (
    FileValidationError,
    FileSizeExceededError,
    InvalidFileTypeError,
    DuplicateDocumentError
)
from app.services.file_validator import FileValidator


def create_mock_file(filename: str, size: int = 1024, content_type: str = "application/pdf") -> UploadFile:
    """Create a mock UploadFile for testing."""
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = filename
    mock_file.size = size
    mock_file.content_type = content_type
    return mock_file


def test_validator_valid_pdf():
    """Test validation of valid PDF file."""
    validator = FileValidator()
    test_file = create_mock_file("test.pdf")
    
    # Should not raise any exception
    validator.validate_file(test_file)


def test_validator_file_size():
    """Test file size validation."""
    validator = FileValidator(max_file_size_mb=1)
    large_file = create_mock_file("large.pdf", size=2 * 1024 * 1024)  # 2MB
    
    with pytest.raises(FileSizeExceededError):
        validator.validate_file(large_file)


def test_validator_file_type():
    """Test file type validation."""
    validator = FileValidator()
    invalid_file = create_mock_file("test.xyz", content_type="application/octet-stream")
    
    with pytest.raises(InvalidFileTypeError):
        validator.validate_file(invalid_file)


def test_validator_duplicate_check(db_session):
    """Test duplicate file detection."""
    validator = FileValidator()
    
    # Create mock document in DB
    from app.models.document import Document
    doc = Document(
        filename="test.pdf",
        file_hash="abc123",
        status="completed"
    )
    db_session.add(doc)
    db_session.commit()
    
    # Test with same filename
    test_file = create_mock_file("test.pdf")
    
    with pytest.raises(DuplicateDocumentError):
        validator.check_duplicate(test_file, "abc123", db_session)
