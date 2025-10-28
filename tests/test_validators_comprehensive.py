"""
Comprehensive tests for file validation service.

Tests cover file type, size, batch validation, hash calculation,
and duplicate detection.
"""

import hashlib
import io
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

import pytest
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.services.file_validator import FileValidator
from app.models.document import Document
from app.utils.exceptions import (
    InvalidFileTypeError,
    FileSizeExceededError,
    DocumentLimitExceededError,
    DuplicateDocumentError,
    FileValidationError,
)


@pytest.mark.unit
class TestFileValidatorInitialization:
    """Tests for FileValidator initialization."""
    
    def test_validator_initialization(self):
        """Test validator initializes with default settings."""
        validator = FileValidator()
        
        assert validator.allowed_extensions is not None
        assert validator.max_file_size > 0
        assert validator.max_documents > 0
    
    def test_validator_has_correct_attributes(self):
        """Test validator has all required attributes."""
        validator = FileValidator()
        
        assert hasattr(validator, 'allowed_extensions')
        assert hasattr(validator, 'max_file_size')
        assert hasattr(validator, 'max_documents')


@pytest.mark.unit
class TestFileTypeValidation:
    """Tests for file type validation."""
    
    def test_validate_pdf_file(self):
        """Test validation of PDF file."""
        validator = FileValidator()
        file = Mock(spec=UploadFile)
        file.filename = "document.pdf"
        
        result = validator.validate_file_type(file)
        
        assert result is True
    
    def test_validate_docx_file(self):
        """Test validation of DOCX file."""
        validator = FileValidator()
        file = Mock(spec=UploadFile)
        file.filename = "document.docx"
        
        result = validator.validate_file_type(file)
        
        assert result is True
    
    def test_validate_txt_file(self):
        """Test validation of TXT file."""
        validator = FileValidator()
        file = Mock(spec=UploadFile)
        file.filename = "document.txt"
        
        result = validator.validate_file_type(file)
        
        assert result is True
    
    def test_validate_uppercase_extension(self):
        """Test validation with uppercase extension."""
        validator = FileValidator()
        file = Mock(spec=UploadFile)
        file.filename = "DOCUMENT.PDF"
        
        result = validator.validate_file_type(file)
        
        assert result is True
    
    def test_validate_mixed_case_extension(self):
        """Test validation with mixed case extension."""
        validator = FileValidator()
        file = Mock(spec=UploadFile)
        file.filename = "Document.PdF"
        
        result = validator.validate_file_type(file)
        
        assert result is True
    
    def test_reject_invalid_file_type(self):
        """Test rejection of invalid file type."""
        validator = FileValidator()
        file = Mock(spec=UploadFile)
        file.filename = "document.exe"
        
        with pytest.raises(InvalidFileTypeError):
            validator.validate_file_type(file)
    
    def test_reject_unsupported_extension(self):
        """Test rejection of unsupported extension."""
        validator = FileValidator()
        file = Mock(spec=UploadFile)
        file.filename = "document.xyz"
        
        with pytest.raises(InvalidFileTypeError):
            validator.validate_file_type(file)
    
    def test_reject_no_extension(self):
        """Test rejection of file without extension."""
        validator = FileValidator()
        file = Mock(spec=UploadFile)
        file.filename = "document"
        
        with pytest.raises(InvalidFileTypeError):
            validator.validate_file_type(file)
    
    def test_reject_no_filename(self):
        """Test rejection when filename is None."""
        validator = FileValidator()
        file = Mock(spec=UploadFile)
        file.filename = None
        
        with pytest.raises(FileValidationError):
            validator.validate_file_type(file)
    
    def test_reject_empty_filename(self):
        """Test rejection of empty filename."""
        validator = FileValidator()
        file = Mock(spec=UploadFile)
        file.filename = ""
        
        with pytest.raises(FileValidationError):
            validator.validate_file_type(file)
    
    def test_validate_file_with_path(self):
        """Test validation of file with path."""
        validator = FileValidator()
        file = Mock(spec=UploadFile)
        file.filename = "/path/to/document.pdf"
        
        result = validator.validate_file_type(file)
        
        assert result is True
    
    def test_validate_file_with_spaces(self):
        """Test validation of filename with spaces."""
        validator = FileValidator()
        file = Mock(spec=UploadFile)
        file.filename = "my document.pdf"
        
        result = validator.validate_file_type(file)
        
        assert result is True


@pytest.mark.unit
@pytest.mark.asyncio
class TestFileSizeValidation:
    """Tests for file size validation."""
    
    async def test_validate_small_file(self):
        """Test validation of small file within limit."""
        validator = FileValidator()
        
        content = b"Small file content"
        file = Mock(spec=UploadFile)
        file.filename = "small.pdf"
        file.read = AsyncMock(return_value=content)
        file.seek = AsyncMock()
        
        result = await validator.validate_file_size(file)
        
        assert result is True
        file.seek.assert_called_once_with(0)
    
    async def test_validate_medium_file(self):
        """Test validation of medium-sized file."""
        validator = FileValidator()
        
        content = b"X" * (1024 * 1024)  # 1 MB
        file = Mock(spec=UploadFile)
        file.filename = "medium.pdf"
        file.read = AsyncMock(return_value=content)
        file.seek = AsyncMock()
        
        result = await validator.validate_file_size(file)
        
        assert result is True
    
    async def test_validate_file_at_limit(self):
        """Test validation of file exactly at size limit."""
        validator = FileValidator()
        
        # Create file at exact limit
        content = b"X" * validator.max_file_size
        file = Mock(spec=UploadFile)
        file.filename = "limit.pdf"
        file.read = AsyncMock(return_value=content)
        file.seek = AsyncMock()
        
        result = await validator.validate_file_size(file)
        
        assert result is True
    
    async def test_reject_oversized_file(self):
        """Test rejection of file exceeding size limit."""
        validator = FileValidator()
        
        # Create file larger than limit
        content = b"X" * (validator.max_file_size + 1)
        file = Mock(spec=UploadFile)
        file.filename = "large.pdf"
        file.read = AsyncMock(return_value=content)
        file.seek = AsyncMock()
        
        with pytest.raises(FileSizeExceededError):
            await validator.validate_file_size(file)
    
    async def test_reject_very_large_file(self):
        """Test rejection of very large file."""
        validator = FileValidator()
        
        content = b"X" * (validator.max_file_size * 10)
        file = Mock(spec=UploadFile)
        file.filename = "huge.pdf"
        file.read = AsyncMock(return_value=content)
        file.seek = AsyncMock()
        
        with pytest.raises(FileSizeExceededError):
            await validator.validate_file_size(file)
    
    async def test_validate_empty_file(self):
        """Test validation of empty file."""
        validator = FileValidator()
        
        content = b""
        file = Mock(spec=UploadFile)
        file.filename = "empty.pdf"
        file.read = AsyncMock(return_value=content)
        file.seek = AsyncMock()
        
        result = await validator.validate_file_size(file)
        
        assert result is True
    
    async def test_file_pointer_reset(self):
        """Test that file pointer is reset after size check."""
        validator = FileValidator()
        
        content = b"Test content"
        file = Mock(spec=UploadFile)
        file.filename = "test.pdf"
        file.read = AsyncMock(return_value=content)
        file.seek = AsyncMock()
        
        await validator.validate_file_size(file)
        
        # Verify seek was called to reset pointer
        file.seek.assert_called_once_with(0)


@pytest.mark.unit
class TestBatchSizeValidation:
    """Tests for batch size validation."""
    
    def test_validate_single_file(self):
        """Test validation of single file batch."""
        validator = FileValidator()
        
        file = Mock(spec=UploadFile)
        files = [file]
        
        result = validator.validate_batch_size(files)
        
        assert result is True
    
    def test_validate_multiple_files(self):
        """Test validation of multiple files."""
        validator = FileValidator()
        
        files = [Mock(spec=UploadFile) for _ in range(5)]
        
        result = validator.validate_batch_size(files)
        
        assert result is True
    
    def test_validate_batch_at_limit(self):
        """Test validation of batch at document limit."""
        validator = FileValidator()
        
        files = [Mock(spec=UploadFile) for _ in range(validator.max_documents)]
        
        result = validator.validate_batch_size(files)
        
        assert result is True
    
    def test_reject_batch_over_limit(self):
        """Test rejection of batch exceeding limit."""
        validator = FileValidator()
        
        files = [Mock(spec=UploadFile) for _ in range(validator.max_documents + 1)]
        
        with pytest.raises(DocumentLimitExceededError):
            validator.validate_batch_size(files)
    
    def test_reject_empty_batch(self):
        """Test rejection of empty batch."""
        validator = FileValidator()
        
        files = []
        
        with pytest.raises(FileValidationError):
            validator.validate_batch_size(files)
    
    def test_reject_very_large_batch(self):
        """Test rejection of very large batch."""
        validator = FileValidator()
        
        files = [Mock(spec=UploadFile) for _ in range(validator.max_documents * 10)]
        
        with pytest.raises(DocumentLimitExceededError):
            validator.validate_batch_size(files)


@pytest.mark.unit
@pytest.mark.asyncio
class TestFileHashCalculation:
    """Tests for file hash calculation."""
    
    async def test_calculate_hash_simple_content(self):
        """Test hash calculation for simple content."""
        validator = FileValidator()
        
        content = b"Test content"
        expected_hash = hashlib.sha256(content).hexdigest()
        
        file = Mock(spec=UploadFile)
        file.filename = "test.pdf"
        file.read = AsyncMock(side_effect=[content, b""])
        file.seek = AsyncMock()
        
        result_hash = await validator.calculate_file_hash(file)
        
        assert result_hash == expected_hash
        file.seek.assert_called_once_with(0)
    
    async def test_calculate_hash_large_content(self):
        """Test hash calculation for large content."""
        validator = FileValidator()
        
        content = b"X" * (1024 * 1024)  # 1 MB
        expected_hash = hashlib.sha256(content).hexdigest()
        
        # Simulate chunked reading
        chunk_size = 8192
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        chunks.append(b"")  # End of file
        
        file = Mock(spec=UploadFile)
        file.filename = "large.pdf"
        file.read = AsyncMock(side_effect=chunks)
        file.seek = AsyncMock()
        
        result_hash = await validator.calculate_file_hash(file)
        
        assert result_hash == expected_hash
    
    async def test_calculate_hash_empty_file(self):
        """Test hash calculation for empty file."""
        validator = FileValidator()
        
        content = b""
        expected_hash = hashlib.sha256(content).hexdigest()
        
        file = Mock(spec=UploadFile)
        file.filename = "empty.pdf"
        file.read = AsyncMock(return_value=content)
        file.seek = AsyncMock()
        
        result_hash = await validator.calculate_file_hash(file)
        
        assert result_hash == expected_hash
    
    async def test_calculate_hash_unicode_content(self):
        """Test hash calculation with unicode content."""
        validator = FileValidator()
        
        content = "Unicode: 你好世界 🚀".encode('utf-8')
        expected_hash = hashlib.sha256(content).hexdigest()
        
        file = Mock(spec=UploadFile)
        file.filename = "unicode.txt"
        file.read = AsyncMock(side_effect=[content, b""])
        file.seek = AsyncMock()
        
        result_hash = await validator.calculate_file_hash(file)
        
        assert result_hash == expected_hash
    
    async def test_hash_deterministic(self):
        """Test that hash calculation is deterministic."""
        validator = FileValidator()
        
        content = b"Deterministic content"
        
        # Calculate hash twice
        file1 = Mock(spec=UploadFile)
        file1.read = AsyncMock(side_effect=[content, b""])
        file1.seek = AsyncMock()
        
        file2 = Mock(spec=UploadFile)
        file2.read = AsyncMock(side_effect=[content, b""])
        file2.seek = AsyncMock()
        
        hash1 = await validator.calculate_file_hash(file1)
        hash2 = await validator.calculate_file_hash(file2)
        
        assert hash1 == hash2
    
    async def test_different_content_different_hash(self):
        """Test that different content produces different hash."""
        validator = FileValidator()
        
        content1 = b"Content 1"
        content2 = b"Content 2"
        
        file1 = Mock(spec=UploadFile)
        file1.read = AsyncMock(side_effect=[content1, b""])
        file1.seek = AsyncMock()
        
        file2 = Mock(spec=UploadFile)
        file2.read = AsyncMock(side_effect=[content2, b""])
        file2.seek = AsyncMock()
        
        hash1 = await validator.calculate_file_hash(file1)
        hash2 = await validator.calculate_file_hash(file2)
        
        assert hash1 != hash2
    
    def test_calculate_hash_from_path(self, temp_dir):
        """Test hash calculation from file path."""
        validator = FileValidator()
        
        content = b"File content"
        expected_hash = hashlib.sha256(content).hexdigest()
        
        test_file = temp_dir / "test.pdf"
        test_file.write_bytes(content)
        
        result_hash = validator.calculate_file_hash_from_path(str(test_file))
        
        assert result_hash == expected_hash
    
    def test_calculate_hash_from_path_large_file(self, temp_dir):
        """Test hash calculation from large file path."""
        validator = FileValidator()
        
        content = b"X" * (1024 * 1024)
        expected_hash = hashlib.sha256(content).hexdigest()
        
        test_file = temp_dir / "large.pdf"
        test_file.write_bytes(content)
        
        result_hash = validator.calculate_file_hash_from_path(str(test_file))
        
        assert result_hash == expected_hash


@pytest.mark.unit
class TestDuplicateDetection:
    """Tests for duplicate document detection."""
    
    def test_no_duplicate_found(self, db_session):
        """Test when no duplicate exists."""
        validator = FileValidator()
        
        file_hash = "abc123def456"
        
        # Should not raise error
        result = validator.check_duplicate(file_hash, db_session, "test.pdf")
        
        assert result is None
    
    def test_duplicate_found_raises_error(self, db_session, sample_document):
        """Test that duplicate raises error."""
        validator = FileValidator()
        
        # Use hash from existing document
        file_hash = sample_document.file_hash
        
        with pytest.raises(DuplicateDocumentError):
            validator.check_duplicate(file_hash, db_session, "duplicate.pdf")
    
    def test_duplicate_detection_with_filename(self, db_session, sample_document):
        """Test duplicate detection includes filename."""
        validator = FileValidator()
        
        file_hash = sample_document.file_hash
        
        with pytest.raises(DuplicateDocumentError) as exc_info:
            validator.check_duplicate(file_hash, db_session, "duplicate.pdf")
        
        # Verify error contains filename
        assert "duplicate.pdf" in str(exc_info.value) or hasattr(exc_info.value, 'filename')
    
    def test_duplicate_detection_without_filename(self, db_session, sample_document):
        """Test duplicate detection without providing filename."""
        validator = FileValidator()
        
        file_hash = sample_document.file_hash
        
        with pytest.raises(DuplicateDocumentError):
            validator.check_duplicate(file_hash, db_session)
    
    def test_unique_hash_passes(self, db_session):
        """Test that unique hash passes check."""
        validator = FileValidator()
        
        unique_hash = "unique123456789"
        
        result = validator.check_duplicate(unique_hash, db_session, "unique.pdf")
        
        assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestCompleteFileValidation:
    """Tests for complete file validation."""
    
    async def test_validate_valid_file(self, db_session):
        """Test validation of completely valid file."""
        validator = FileValidator()
        
        content = b"Valid file content"
        file = Mock(spec=UploadFile)
        file.filename = "valid.pdf"
        file.read = AsyncMock(side_effect=[content, content, b""])
        file.seek = AsyncMock()
        
        result = await validator.validate_file(file, db_session)
        
        assert result["valid"] is True
        assert result["filename"] == "valid.pdf"
        assert "file_hash" in result
    
    async def test_validate_file_without_duplicate_check(self, db_session):
        """Test validation without duplicate checking."""
        validator = FileValidator()
        
        content = b"Content"
        file = Mock(spec=UploadFile)
        file.filename = "test.pdf"
        file.read = AsyncMock(side_effect=[content, content, b""])
        file.seek = AsyncMock()
        
        result = await validator.validate_file(file, db_session, check_duplicates=False)
        
        assert result["valid"] is True
    
    async def test_validate_file_stops_on_type_error(self, db_session):
        """Test that validation stops on file type error."""
        validator = FileValidator()
        
        file = Mock(spec=UploadFile)
        file.filename = "invalid.exe"
        
        with pytest.raises(InvalidFileTypeError):
            await validator.validate_file(file, db_session)
    
    async def test_validate_file_stops_on_size_error(self, db_session):
        """Test that validation stops on size error."""
        validator = FileValidator()
        
        content = b"X" * (validator.max_file_size + 1)
        file = Mock(spec=UploadFile)
        file.filename = "large.pdf"
        file.read = AsyncMock(return_value=content)
        file.seek = AsyncMock()
        
        with pytest.raises(FileSizeExceededError):
            await validator.validate_file(file, db_session)
    
    async def test_validate_file_stops_on_duplicate(self, db_session, sample_document):
        """Test that validation stops on duplicate."""
        validator = FileValidator()
        
        content = b"Content"
        expected_hash = sample_document.file_hash
        
        file = Mock(spec=UploadFile)
        file.filename = "duplicate.pdf"
        file.read = AsyncMock(side_effect=[content, content, b""])
        file.seek = AsyncMock()
        
        with patch.object(validator, 'calculate_file_hash', return_value=expected_hash):
            with pytest.raises(DuplicateDocumentError):
                await validator.validate_file(file, db_session, check_duplicates=True)


@pytest.mark.unit
@pytest.mark.asyncio
class TestBatchValidation:
    """Tests for batch file validation."""
    
    async def test_validate_single_file_batch(self, db_session):
        """Test validation of single file batch."""
        validator = FileValidator()
        
        content = b"Content"
        file = Mock(spec=UploadFile)
        file.filename = "test.pdf"
        file.read = AsyncMock(side_effect=[content, content, b""])
        file.seek = AsyncMock()
        
        files = [file]
        
        results = await validator.validate_batch(files, db_session)
        
        assert len(results) == 1
        assert results[0]["valid"] is True
    
    async def test_validate_multiple_files_batch(self, db_session):
        """Test validation of multiple files."""
        validator = FileValidator()
        
        files = []
        for i in range(3):
            content = f"Content {i}".encode()
            file = Mock(spec=UploadFile)
            file.filename = f"test{i}.pdf"
            file.read = AsyncMock(side_effect=[content, content, b""])
            file.seek = AsyncMock()
            files.append(file)
        
        results = await validator.validate_batch(files, db_session)
        
        assert len(results) == 3
        assert all(r["valid"] for r in results)
    
    async def test_validate_batch_stops_on_size_error(self, db_session):
        """Test that batch validation stops on batch size error."""
        validator = FileValidator()
        
        # Create too many files
        files = [Mock(spec=UploadFile) for _ in range(validator.max_documents + 1)]
        
        with pytest.raises(DocumentLimitExceededError):
            await validator.validate_batch(files, db_session)
    
    async def test_validate_batch_stops_on_empty(self, db_session):
        """Test that batch validation stops on empty batch."""
        validator = FileValidator()
        
        files = []
        
        with pytest.raises(FileValidationError):
            await validator.validate_batch(files, db_session)
    
    async def test_validate_batch_without_duplicate_check(self, db_session):
        """Test batch validation without duplicate checking."""
        validator = FileValidator()
        
        content = b"Content"
        file = Mock(spec=UploadFile)
        file.filename = "test.pdf"
        file.read = AsyncMock(side_effect=[content, content, b""])
        file.seek = AsyncMock()
        
        files = [file]
        
        results = await validator.validate_batch(files, db_session, check_duplicates=False)
        
        assert len(results) == 1
        assert results[0]["valid"] is True


@pytest.mark.unit
class TestValidatorEdgeCases:
    """Tests for validator edge cases."""
    
    def test_validator_with_special_filenames(self):
        """Test validator with special characters in filename."""
        validator = FileValidator()
        
        file = Mock(spec=UploadFile)
        file.filename = "file (1) [copy] #2.pdf"
        
        result = validator.validate_file_type(file)
        
        assert result is True
    
    def test_validator_with_very_long_filename(self):
        """Test validator with very long filename."""
        validator = FileValidator()
        
        file = Mock(spec=UploadFile)
        file.filename = "a" * 200 + ".pdf"
        
        result = validator.validate_file_type(file)
        
        assert result is True
    
    def test_validator_with_dots_in_filename(self):
        """Test validator with multiple dots in filename."""
        validator = FileValidator()
        
        file = Mock(spec=UploadFile)
        file.filename = "file.name.with.dots.pdf"
        
        result = validator.validate_file_type(file)
        
        assert result is True

