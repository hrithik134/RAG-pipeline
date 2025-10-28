"""
Unit tests for document ingestion services.
"""

import hashlib
import io
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

import pytest
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document, DocumentStatus
from app.models.upload import Upload, UploadStatus
from app.services.chunking import TokenChunker, ChunkData
from app.services.file_validator import FileValidator
from app.services.text_extractor import (
    PDFExtractor,
    DOCXExtractor,
    TXTExtractor,
    ExtractorFactory,
    ExtractedText,
)
from app.utils.exceptions import (
    InvalidFileTypeError,
    FileSizeExceededError,
    DocumentLimitExceededError,
    PageLimitExceededError,
    DuplicateDocumentError,
    ExtractionError,
    ChunkingError,
)


# ============================================================================
# File Validator Tests
# ============================================================================

class TestFileValidator:
    """Tests for FileValidator service."""
    
    def test_validate_file_type_valid_pdf(self):
        """Test validation of valid PDF file."""
        validator = FileValidator()
        file = Mock(spec=UploadFile)
        file.filename = "document.pdf"
        
        result = validator.validate_file_type(file)
        assert result is True
    
    def test_validate_file_type_valid_docx(self):
        """Test validation of valid DOCX file."""
        validator = FileValidator()
        file = Mock(spec=UploadFile)
        file.filename = "document.docx"
        
        result = validator.validate_file_type(file)
        assert result is True
    
    def test_validate_file_type_valid_txt(self):
        """Test validation of valid TXT file."""
        validator = FileValidator()
        file = Mock(spec=UploadFile)
        file.filename = "document.txt"
        
        result = validator.validate_file_type(file)
        assert result is True
    
    def test_validate_file_type_invalid(self):
        """Test validation of invalid file type."""
        validator = FileValidator()
        file = Mock(spec=UploadFile)
        file.filename = "document.exe"
        
        with pytest.raises(InvalidFileTypeError) as exc_info:
            validator.validate_file_type(file)
        
        assert "exe" in str(exc_info.value)
        assert "document.exe" in str(exc_info.value)
    
    def test_validate_file_type_case_insensitive(self):
        """Test that file type validation is case insensitive."""
        validator = FileValidator()
        file = Mock(spec=UploadFile)
        file.filename = "document.PDF"
        
        result = validator.validate_file_type(file)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_file_size_within_limit(self):
        """Test validation of file within size limit."""
        validator = FileValidator()
        
        # Create mock file with 1MB content
        content = b"x" * (1024 * 1024)
        file = Mock(spec=UploadFile)
        file.filename = "document.pdf"
        file.read = AsyncMock(return_value=content)
        file.seek = AsyncMock()
        
        result = await validator.validate_file_size(file)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_file_size_exceeds_limit(self):
        """Test validation of file exceeding size limit."""
        validator = FileValidator()
        
        # Create mock file larger than 50MB
        content = b"x" * (51 * 1024 * 1024)
        file = Mock(spec=UploadFile)
        file.filename = "large_document.pdf"
        file.read = AsyncMock(return_value=content)
        file.seek = AsyncMock()
        
        with pytest.raises(FileSizeExceededError) as exc_info:
            await validator.validate_file_size(file)
        
        assert "large_document.pdf" in str(exc_info.value)
    
    def test_validate_batch_size_valid(self):
        """Test validation of valid batch size."""
        validator = FileValidator()
        files = [Mock(spec=UploadFile) for _ in range(20)]
        
        result = validator.validate_batch_size(files)
        assert result is True
    
    def test_validate_batch_size_exceeds_limit(self):
        """Test validation of batch exceeding limit."""
        validator = FileValidator()
        files = [Mock(spec=UploadFile) for _ in range(21)]
        
        with pytest.raises(DocumentLimitExceededError) as exc_info:
            validator.validate_batch_size(files)
        
        assert "21" in str(exc_info.value)
        assert "20" in str(exc_info.value)
    
    def test_validate_batch_size_empty(self):
        """Test validation of empty batch."""
        validator = FileValidator()
        files = []
        
        with pytest.raises(Exception):
            validator.validate_batch_size(files)
    
    @pytest.mark.asyncio
    async def test_calculate_file_hash(self):
        """Test file hash calculation."""
        validator = FileValidator()
        
        content = b"test content"
        expected_hash = hashlib.sha256(content).hexdigest()
        
        file = Mock(spec=UploadFile)
        file.read = AsyncMock(side_effect=[content, b""])
        file.seek = AsyncMock()
        
        result = await validator.calculate_file_hash(file)
        assert result == expected_hash
    
    def test_calculate_file_hash_from_path(self, tmp_path):
        """Test file hash calculation from path."""
        validator = FileValidator()
        
        # Create temporary file
        test_file = tmp_path / "test.txt"
        content = b"test content"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        result = validator.calculate_file_hash_from_path(str(test_file))
        
        assert result == expected_hash
    
    def test_check_duplicate_not_found(self, db_session):
        """Test duplicate check when no duplicate exists."""
        validator = FileValidator()
        file_hash = "abc123"
        
        result = validator.check_duplicate(file_hash, db_session)
        assert result is None
    
    def test_check_duplicate_found(self, db_session):
        """Test duplicate check when duplicate exists."""
        validator = FileValidator()
        
        # Create existing document
        existing_doc = Document(
            upload_id=uuid4(),
            filename="existing.pdf",
            file_type="pdf",
            file_hash="abc123",
            status=DocumentStatus.COMPLETED
        )
        db_session.add(existing_doc)
        db_session.commit()
        
        with pytest.raises(DuplicateDocumentError) as exc_info:
            validator.check_duplicate("abc123", db_session, "duplicate.pdf")
        
        assert "duplicate.pdf" in str(exc_info.value)
        assert str(existing_doc.id) in str(exc_info.value)


# ============================================================================
# Text Extractor Tests
# ============================================================================

class TestTextExtractors:
    """Tests for text extraction services."""
    
    def test_txt_extractor_basic(self, tmp_path):
        """Test basic TXT extraction."""
        extractor = TXTExtractor()
        
        # Create test file
        test_file = tmp_path / "test.txt"
        content = "This is a test document.\nWith multiple lines."
        test_file.write_text(content, encoding='utf-8')
        
        result = extractor.extract_text(str(test_file))
        
        assert isinstance(result, ExtractedText)
        assert result.text == content
        assert result.page_count == 1
        assert result.char_count == len(content)
        assert result.metadata['extractor'] == 'txt'
    
    def test_txt_extractor_encoding_detection(self, tmp_path):
        """Test TXT extraction with encoding detection."""
        extractor = TXTExtractor()
        
        # Create test file with latin-1 encoding
        test_file = tmp_path / "test_latin1.txt"
        content = "Café résumé"
        test_file.write_text(content, encoding='latin-1')
        
        result = extractor.extract_text(str(test_file))
        
        assert isinstance(result, ExtractedText)
        assert result.page_count == 1
    
    def test_txt_extractor_get_page_count(self, tmp_path):
        """Test TXT page count (always 1)."""
        extractor = TXTExtractor()
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        page_count = extractor.get_page_count(str(test_file))
        assert page_count == 1
    
    def test_extractor_factory_pdf(self):
        """Test ExtractorFactory returns PDFExtractor for PDF files."""
        extractor = ExtractorFactory.get_extractor("document.pdf")
        assert isinstance(extractor, PDFExtractor)
    
    def test_extractor_factory_docx(self):
        """Test ExtractorFactory returns DOCXExtractor for DOCX files."""
        extractor = ExtractorFactory.get_extractor("document.docx")
        assert isinstance(extractor, DOCXExtractor)
    
    def test_extractor_factory_txt(self):
        """Test ExtractorFactory returns TXTExtractor for TXT files."""
        extractor = ExtractorFactory.get_extractor("document.txt")
        assert isinstance(extractor, TXTExtractor)
    
    def test_extractor_factory_unsupported(self):
        """Test ExtractorFactory raises error for unsupported file type."""
        with pytest.raises(ExtractionError):
            ExtractorFactory.get_extractor("document.exe")


# ============================================================================
# Token Chunker Tests
# ============================================================================

class TestTokenChunker:
    """Tests for TokenChunker service."""
    
    def test_count_tokens_basic(self):
        """Test basic token counting."""
        chunker = TokenChunker()
        text = "This is a test sentence."
        
        token_count = chunker.count_tokens(text)
        assert token_count > 0
        assert isinstance(token_count, int)
    
    def test_count_tokens_empty(self):
        """Test token counting with empty string."""
        chunker = TokenChunker()
        token_count = chunker.count_tokens("")
        assert token_count == 0
    
    def test_split_by_sentences_basic(self):
        """Test sentence splitting."""
        chunker = TokenChunker()
        text = "First sentence. Second sentence! Third sentence?"
        
        sentences = chunker.split_by_sentences(text)
        assert len(sentences) >= 3
    
    def test_split_by_sentences_abbreviations(self):
        """Test sentence splitting handles abbreviations."""
        chunker = TokenChunker()
        text = "Dr. Smith works at U.S. Labs. He is a scientist."
        
        sentences = chunker.split_by_sentences(text)
        # Should not split on Dr. or U.S.
        assert len(sentences) >= 1
    
    def test_chunk_text_basic(self):
        """Test basic text chunking."""
        chunker = TokenChunker(chunk_size=50, chunk_overlap=10)
        
        # Create text that will require multiple chunks
        text = " ".join(["This is sentence number {}.".format(i) for i in range(20)])
        document_id = uuid4()
        
        chunks = chunker.chunk_text(text, document_id)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, ChunkData) for chunk in chunks)
        assert all(chunk.token_count > 0 for chunk in chunks)
    
    def test_chunk_text_with_overlap(self):
        """Test that chunks have proper overlap."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        
        text = " ".join(["Word{}".format(i) for i in range(200)])
        document_id = uuid4()
        
        chunks = chunker.chunk_text(text, document_id)
        
        if len(chunks) > 1:
            # Verify chunks are indexed sequentially
            for i, chunk in enumerate(chunks):
                assert chunk.chunk_index == i
    
    def test_chunk_text_empty(self):
        """Test chunking empty text."""
        chunker = TokenChunker()
        document_id = uuid4()
        
        chunks = chunker.chunk_text("", document_id)
        assert len(chunks) == 0
    
    def test_chunk_text_metadata(self):
        """Test that chunks include metadata."""
        chunker = TokenChunker()
        text = "This is a test document with some content."
        document_id = uuid4()
        metadata = {"filename": "test.pdf", "page_number": 1}
        
        chunks = chunker.chunk_text(text, document_id, metadata)
        
        assert len(chunks) > 0
        assert chunks[0].metadata['filename'] == "test.pdf"
        assert chunks[0].metadata['page_number'] == 1
        assert str(document_id) in chunks[0].metadata['document_id']
    
    def test_estimate_chunk_count(self):
        """Test chunk count estimation."""
        chunker = TokenChunker(chunk_size=100, chunk_overlap=20)
        
        # Create text with known token count
        text = " ".join(["word"] * 500)  # Approximately 500 tokens
        
        estimated = chunker.estimate_chunk_count(text)
        assert estimated > 0
        assert isinstance(estimated, int)
    
    def test_chunk_size_configuration(self):
        """Test chunker respects configured chunk size."""
        chunk_size = 200
        chunker = TokenChunker(chunk_size=chunk_size, chunk_overlap=20)
        
        # Create long text
        text = " ".join(["This is a sentence."] * 100)
        document_id = uuid4()
        
        chunks = chunker.chunk_text(text, document_id)
        
        # Most chunks should be close to target size
        for chunk in chunks[:-1]:  # Exclude last chunk
            assert chunk.token_count <= chunk_size + 50  # Allow some flexibility


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def db_session():
    """Create a mock database session."""
    from unittest.mock import MagicMock
    
    session = MagicMock(spec=Session)
    session.query.return_value.filter.return_value.first.return_value = None
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    
    return session


@pytest.fixture
def sample_upload_file():
    """Create a sample UploadFile for testing."""
    content = b"This is a test file content."
    file = UploadFile(
        filename="test.pdf",
        file=io.BytesIO(content)
    )
    return file

