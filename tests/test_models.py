"""
Tests for database models.
Tests constraints, relationships, and business logic.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Chunk, Document, DocumentStatus, Query, Upload, UploadStatus


class TestUploadModel:
    """Tests for Upload model."""

    def test_upload_creation(self):
        """Test creating an upload."""
        upload = Upload(
            upload_batch_id="test-batch-001",
            status=UploadStatus.PENDING,
            total_documents=0,
        )
        assert upload.upload_batch_id == "test-batch-001"
        assert upload.status == UploadStatus.PENDING
        assert upload.total_documents == 0

    def test_can_add_document(self):
        """Test can_add_document method."""
        upload = Upload(upload_batch_id="test", total_documents=19)
        assert upload.can_add_document() is True

        upload.total_documents = 20
        assert upload.can_add_document() is False

    def test_increment_document_count(self):
        """Test incrementing document count."""
        upload = Upload(upload_batch_id="test", total_documents=0)
        upload.increment_document_count()
        assert upload.total_documents == 1

    def test_increment_document_count_exceeds_limit(self):
        """Test that incrementing beyond 20 raises error."""
        upload = Upload(upload_batch_id="test", total_documents=20)
        with pytest.raises(ValueError, match="Cannot add more than 20 documents"):
            upload.increment_document_count()

    def test_status_transitions(self):
        """Test status transition methods."""
        upload = Upload(upload_batch_id="test", total_documents=0)

        upload.mark_processing()
        assert upload.status == UploadStatus.PROCESSING

        upload.mark_completed()
        assert upload.status == UploadStatus.COMPLETED
        assert upload.completed_at is not None

        upload2 = Upload(upload_batch_id="test2", total_documents=0)
        upload2.mark_failed("Test error")
        assert upload2.status == UploadStatus.FAILED
        assert upload2.error_message == "Test error"


class TestDocumentModel:
    """Tests for Document model."""

    def test_document_creation(self):
        """Test creating a document."""
        doc = Document(
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            file_type="pdf",
            page_count=10,
        )
        assert doc.filename == "test.pdf"
        assert doc.page_count == 10

    def test_is_valid_page_count(self):
        """Test page count validation."""
        doc = Document(
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            file_type="pdf",
            page_count=1000,
        )
        assert doc.is_valid_page_count() is True

        doc.page_count = 1001
        assert doc.is_valid_page_count() is False

    def test_status_transitions(self):
        """Test document status transitions."""
        doc = Document(
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            file_type="pdf",
            page_count=10,
        )

        doc.mark_processing()
        assert doc.status == DocumentStatus.PROCESSING

        doc.mark_completed()
        assert doc.status == DocumentStatus.COMPLETED
        assert doc.processed_at is not None

    def test_increment_chunk_count(self):
        """Test incrementing chunk count."""
        doc = Document(
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024,
            file_type="pdf",
            page_count=10,
            total_chunks=0,
        )
        doc.increment_chunk_count()
        assert doc.total_chunks == 1


class TestChunkModel:
    """Tests for Chunk model."""

    def test_chunk_creation(self):
        """Test creating a chunk."""
        chunk = Chunk(
            chunk_index=0,
            content="Test content",
            token_count=10,
            page_number=1,
            start_char=0,
            end_char=12,
        )
        assert chunk.chunk_index == 0
        assert chunk.content == "Test content"
        assert chunk.token_count == 10

    def test_has_embedding(self):
        """Test has_embedding method."""
        chunk = Chunk(
            chunk_index=0,
            content="Test",
            token_count=1,
            start_char=0,
            end_char=4,
        )
        assert chunk.has_embedding() is False

        chunk.set_embedding_id("emb-123")
        assert chunk.has_embedding() is True

    def test_get_metadata(self):
        """Test get_metadata method."""
        chunk = Chunk(
            chunk_index=5,
            content="Test",
            token_count=10,
            page_number=2,
            start_char=100,
            end_char=200,
        )
        metadata = chunk.get_metadata()

        assert metadata["chunk_index"] == 5
        assert metadata["page_number"] == 2
        assert metadata["token_count"] == 10
        assert metadata["start_char"] == 100
        assert metadata["end_char"] == 200


class TestQueryModel:
    """Tests for Query model."""

    def test_query_creation(self):
        """Test creating a query."""
        query = Query(
            query_text="What is the capital of France?",
            top_k=10,
            mmr_lambda=0.5,
            response="The capital of France is Paris.",
            chunks_used=[],
            latency_ms=150,
            llm_provider="openai",
        )
        assert query.query_text == "What is the capital of France?"
        assert query.top_k == 10
        assert query.latency_ms == 150

    def test_set_and_get_chunks_used(self):
        """Test setting and getting chunks used."""
        query = Query(
            query_text="Test",
            response="Test response",
            latency_ms=100,
            llm_provider="openai",
        )

        chunk_ids = ["chunk-1", "chunk-2", "chunk-3"]
        query.set_chunks_used(chunk_ids)

        retrieved = query.get_chunks_used()
        assert retrieved == chunk_ids
        assert len(retrieved) == 3

    def test_get_performance_metrics(self):
        """Test get_performance_metrics method."""
        query = Query(
            query_text="Test",
            top_k=8,
            mmr_lambda=0.7,
            response="Test",
            chunks_used=["c1", "c2"],
            latency_ms=200,
            llm_provider="google",
        )

        metrics = query.get_performance_metrics()
        assert metrics["latency_ms"] == 200
        assert metrics["top_k"] == 8
        assert metrics["mmr_lambda"] == 0.7
        assert metrics["chunks_count"] == 2
        assert metrics["llm_provider"] == "google"

