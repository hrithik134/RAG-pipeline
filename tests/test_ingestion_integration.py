"""
Integration tests for the complete document ingestion pipeline.
"""

import io
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.chunk import Chunk
from app.models.document import Document, DocumentStatus
from app.models.upload import Upload, UploadStatus
from app.services.ingestion_service import IngestionService
from app.utils.exceptions import DocumentLimitExceededError


# ============================================================================
# Test Database Setup
# ============================================================================

@pytest.fixture(scope="function")
def test_db():
    """Create a test database for integration tests."""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    engine.dispose()


@pytest.fixture
def ingestion_service(test_db):
    """Create an IngestionService instance with test database."""
    return IngestionService(test_db)


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_file(filename: str, content: str, content_type: str = "text/plain") -> UploadFile:
    """Create a test UploadFile."""
    # Create file in memory
    bytes_io = io.BytesIO(content.encode('utf-8'))
    bytes_io.name = filename
    
    # Create UploadFile using the custom SpooledTemporaryFile
    file = UploadFile(file=bytes_io, filename=filename)
    
    # SpooledTemporaryFile acts like a file object but keeps data in memory
    # until it exceeds a size threshold
    return file


def create_test_txt_file(filename: str = "test.txt", size_kb: int = 1) -> UploadFile:
    """Create a test TXT file with specified size."""
    content = "This is a test document. " * (size_kb * 50)  # Approximate size
    return create_test_file(filename, content)


# ============================================================================
# Integration Tests
# ============================================================================

class TestIngestionPipeline:
    """Integration tests for the complete ingestion pipeline."""
    
    @pytest.mark.asyncio
    async def test_single_document_ingestion(self, ingestion_service, test_db):
        """Test ingestion of a single document through the complete pipeline."""
        # Create test file
        content = "This is a test document. " * 100
        file = create_test_file("test.txt", content)
        
        # Process upload
        upload = await ingestion_service.process_upload_batch([file])
        
        # Verify upload record
        assert upload is not None
        assert upload.status == UploadStatus.COMPLETED
        assert upload.total_documents == 1
        assert upload.successful_documents == 1
        assert upload.failed_documents == 0
        
        # Verify document was created
        documents = test_db.query(Document).filter(Document.upload_id == upload.id).all()
        assert len(documents) == 1
        
        document = documents[0]
        assert document.status == DocumentStatus.COMPLETED
        assert document.filename == "test.txt"
        assert document.page_count == 1
        assert document.total_chunks > 0
        
        # Verify chunks were created
        chunks = test_db.query(Chunk).filter(Chunk.document_id == document.id).all()
        assert len(chunks) > 0
        assert all(chunk.content for chunk in chunks)
        assert all(chunk.token_count > 0 for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_multiple_documents_ingestion(self, ingestion_service, test_db):
        """Test ingestion of multiple documents in a batch."""
        # Create multiple test files
        files = [
            create_test_file("doc1.txt", "Content for document 1. " * 50),
            create_test_file("doc2.txt", "Content for document 2. " * 50),
            create_test_file("doc3.txt", "Content for document 3. " * 50),
        ]
        
        # Process upload
        upload = await ingestion_service.process_upload_batch(files)
        
        # Verify upload record
        assert upload.status == UploadStatus.COMPLETED
        assert upload.total_documents == 3
        assert upload.successful_documents == 3
        
        # Verify all documents were created
        documents = test_db.query(Document).filter(Document.upload_id == upload.id).all()
        assert len(documents) == 3
        
        # Verify all documents have chunks
        for document in documents:
            chunks = test_db.query(Chunk).filter(Chunk.document_id == document.id).all()
            assert len(chunks) > 0
    
    @pytest.mark.asyncio
    async def test_batch_limit_enforcement(self, ingestion_service):
        """Test that batch size limit (20 documents) is enforced."""
        # Create 21 files (exceeds limit)
        files = [
            create_test_file(f"doc{i}.txt", f"Content {i}")
            for i in range(21)
        ]
        
        # Should raise DocumentLimitExceededError
        with pytest.raises(DocumentLimitExceededError):
            await ingestion_service.process_upload_batch(files)
    
    @pytest.mark.asyncio
    async def test_empty_file_handling(self, ingestion_service, test_db):
        """Test handling of empty files."""
        # Create empty file
        file = create_test_file("empty.txt", "")
        
        # Process upload
        upload = await ingestion_service.process_upload_batch([file])
        
        # Upload should complete but document might have no chunks
        assert upload is not None
        documents = test_db.query(Document).filter(Document.upload_id == upload.id).all()
        assert len(documents) == 1
    
    @pytest.mark.asyncio
    async def test_upload_status_tracking(self, ingestion_service, test_db):
        """Test that upload status is properly tracked."""
        file = create_test_file("test.txt", "Test content " * 50)
        
        # Process upload
        upload = await ingestion_service.process_upload_batch([file])
        
        # Get upload status
        status = ingestion_service.get_upload_status(upload.id)
        
        assert status is not None
        assert status.id == upload.id
        assert status.status == UploadStatus.COMPLETED
        assert status.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_document_retrieval(self, ingestion_service, test_db):
        """Test document retrieval after ingestion."""
        file = create_test_file("test.txt", "Test content " * 50)
        
        # Process upload
        upload = await ingestion_service.process_upload_batch([file])
        
        # Get documents
        documents = test_db.query(Document).filter(Document.upload_id == upload.id).all()
        document_id = documents[0].id
        
        # Retrieve document
        retrieved = ingestion_service.get_document(document_id)
        
        assert retrieved is not None
        assert retrieved.id == document_id
        assert retrieved.filename == "test.txt"
    
    @pytest.mark.asyncio
    async def test_chunk_retrieval(self, ingestion_service, test_db):
        """Test chunk retrieval for a document."""
        file = create_test_file("test.txt", "Test content. " * 100)
        
        # Process upload
        upload = await ingestion_service.process_upload_batch([file])
        
        # Get document
        documents = test_db.query(Document).filter(Document.upload_id == upload.id).all()
        document_id = documents[0].id
        
        # Retrieve chunks
        chunks = ingestion_service.get_document_chunks(document_id)
        
        assert len(chunks) > 0
        assert all(chunk.document_id == document_id for chunk in chunks)
        assert all(chunk.content for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_chunk_pagination(self, ingestion_service, test_db):
        """Test chunk retrieval with pagination."""
        # Create large document that will generate many chunks
        content = "This is a test sentence. " * 500
        file = create_test_file("large.txt", content)
        
        # Process upload
        upload = await ingestion_service.process_upload_batch([file])
        
        # Get document
        documents = test_db.query(Document).filter(Document.upload_id == upload.id).all()
        document_id = documents[0].id
        
        # Get first page of chunks
        chunks_page1 = ingestion_service.get_document_chunks(document_id, skip=0, limit=5)
        
        # Get second page of chunks
        chunks_page2 = ingestion_service.get_document_chunks(document_id, skip=5, limit=5)
        
        # Verify pagination works
        if len(chunks_page1) == 5:  # Only if we have enough chunks
            assert chunks_page1[0].chunk_index != chunks_page2[0].chunk_index
    
    @pytest.mark.asyncio
    async def test_document_deletion(self, ingestion_service, test_db):
        """Test document deletion."""
        file = create_test_file("test.txt", "Test content " * 50)
        
        # Process upload
        upload = await ingestion_service.process_upload_batch([file])
        
        # Get document
        documents = test_db.query(Document).filter(Document.upload_id == upload.id).all()
        document_id = documents[0].id
        
        # Verify chunks exist
        chunks_before = test_db.query(Chunk).filter(Chunk.document_id == document_id).all()
        assert len(chunks_before) > 0
        
        # Delete document
        deleted = ingestion_service.delete_document(document_id)
        assert deleted is True
        
        # Verify document is deleted
        document = ingestion_service.get_document(document_id)
        assert document is None
        
        # Verify chunks are cascade deleted
        chunks_after = test_db.query(Chunk).filter(Chunk.document_id == document_id).all()
        assert len(chunks_after) == 0
    
    @pytest.mark.asyncio
    async def test_upload_batch_deletion(self, ingestion_service, test_db):
        """Test deletion of entire upload batch."""
        files = [
            create_test_file("doc1.txt", "Content 1 " * 50),
            create_test_file("doc2.txt", "Content 2 " * 50),
        ]
        
        # Process upload
        upload = await ingestion_service.process_upload_batch(files)
        upload_id = upload.id
        
        # Verify documents exist
        documents_before = test_db.query(Document).filter(Document.upload_id == upload_id).all()
        assert len(documents_before) == 2
        
        # Delete upload batch
        deleted = ingestion_service.delete_upload_batch(upload_id)
        assert deleted is True
        
        # Verify upload is deleted
        upload_after = ingestion_service.get_upload_status(upload_id)
        assert upload_after is None
        
        # Verify documents are deleted
        documents_after = test_db.query(Document).filter(Document.upload_id == upload_id).all()
        assert len(documents_after) == 0
    
    @pytest.mark.asyncio
    async def test_chunk_indexing(self, ingestion_service, test_db):
        """Test that chunks are properly indexed."""
        content = "This is a test sentence. " * 200
        file = create_test_file("test.txt", content)
        
        # Process upload
        upload = await ingestion_service.process_upload_batch([file])
        
        # Get document
        documents = test_db.query(Document).filter(Document.upload_id == upload.id).all()
        document_id = documents[0].id
        
        # Get chunks
        chunks = ingestion_service.get_document_chunks(document_id, limit=100)
        
        # Verify chunks are indexed sequentially
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
    
    @pytest.mark.asyncio
    async def test_chunk_metadata(self, ingestion_service, test_db):
        """Test that chunk metadata is properly stored."""
        file = create_test_file("test.txt", "Test content " * 50)
        
        # Process upload
        upload = await ingestion_service.process_upload_batch([file])
        
        # Get chunks
        documents = test_db.query(Document).filter(Document.upload_id == upload.id).all()
        document_id = documents[0].id
        chunks = ingestion_service.get_document_chunks(document_id)
        
        # Verify metadata
        for chunk in chunks:
            assert chunk.metadata is not None
            assert 'document_id' in chunk.metadata
            assert 'filename' in chunk.metadata
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self, ingestion_service, test_db):
        """Test that multiple files are processed concurrently."""
        # Create multiple files
        files = [
            create_test_file(f"doc{i}.txt", f"Content for document {i}. " * 100)
            for i in range(5)
        ]
        
        # Process upload (should use async processing)
        upload = await ingestion_service.process_upload_batch(files)
        
        # Verify all documents processed successfully
        assert upload.successful_documents == 5
        assert upload.failed_documents == 0
        
        # Verify all have chunks
        documents = test_db.query(Document).filter(Document.upload_id == upload.id).all()
        for document in documents:
            assert document.total_chunks > 0


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    @pytest.mark.asyncio
    async def test_very_short_document(self, ingestion_service, test_db):
        """Test handling of very short documents."""
        file = create_test_file("short.txt", "Short.")
        
        upload = await ingestion_service.process_upload_batch([file])
        
        assert upload.status == UploadStatus.COMPLETED
        documents = test_db.query(Document).filter(Document.upload_id == upload.id).all()
        assert len(documents) == 1
    
    @pytest.mark.asyncio
    async def test_special_characters_in_filename(self, ingestion_service, test_db):
        """Test handling of special characters in filenames."""
        file = create_test_file("test-file_123.txt", "Content " * 50)
        
        upload = await ingestion_service.process_upload_batch([file])
        
        assert upload.status == UploadStatus.COMPLETED
        documents = test_db.query(Document).filter(Document.upload_id == upload.id).all()
        assert documents[0].filename == "test-file_123.txt"
    
    @pytest.mark.asyncio
    async def test_unicode_content(self, ingestion_service, test_db):
        """Test handling of Unicode content."""
        content = "Hello 世界 🌍 café résumé " * 50
        file = create_test_file("unicode.txt", content)
        
        upload = await ingestion_service.process_upload_batch([file])
        
        assert upload.status == UploadStatus.COMPLETED
        documents = test_db.query(Document).filter(Document.upload_id == upload.id).all()
        
        # Verify chunks contain Unicode content
        chunks = test_db.query(Chunk).filter(Chunk.document_id == documents[0].id).all()
        assert any("世界" in chunk.content or "café" in chunk.content for chunk in chunks)

