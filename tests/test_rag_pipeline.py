"""Integration tests for the complete RAG pipeline."""

import pytest
from fastapi import UploadFile
from pathlib import Path
from typing import List

from app.models.document import Document, DocumentStatus
from app.models.upload import Upload, UploadStatus
from app.services.ingestion_service import IngestionService
from app.services.rag.query_service import QueryService
from tests.mocks import (
    MockEmbeddingService,
    MockLLMService,
    MockPineconeService,
    MockDocumentExtractor
)


class TestRAGPipeline:
    """Test suite for end-to-end RAG pipeline."""

    @pytest.mark.asyncio
    async def test_document_ingestion_flow(
        self,
        db_session,
        mock_embedding_service,
        mock_document_extractor,
        mock_pinecone_service
    ):
        """Test complete document ingestion flow."""
        # Create test file
        test_file = Path("test.pdf")
        test_file.write_text("This is a test document content.")
        
        try:
            # Create services
            ingestion_service = IngestionService(
                db_session,
                embedding_service=mock_embedding_service,
                vector_store=mock_pinecone_service
            )
            
            # Process upload
            with test_file.open("rb") as f:
                file = UploadFile(filename="test.pdf", file=f)
                upload_batch = await ingestion_service.process_upload_batch([file])
            
            # Verify upload status
            assert upload_batch.status == UploadStatus.COMPLETED
            assert upload_batch.total_documents == 1
            assert upload_batch.successful_documents == 1
            
            # Verify document creation
            document = db_session.query(Document).first()
            assert document is not None
            assert document.status == DocumentStatus.COMPLETED
            assert document.filename == "test.pdf"
            
            # Verify chunks were created
            assert len(document.chunks) > 0
            
        finally:
            test_file.unlink()

    @pytest.mark.asyncio
    async def test_query_processing_flow(
        self,
        db_session,
        mock_embedding_service,
        mock_llm_service,
        mock_pinecone_service
    ):
        """Test complete query processing flow."""
        # Create test document and chunks in DB
        document = Document(
            filename="test.pdf",
            status=DocumentStatus.COMPLETED
        )
        db_session.add(document)
        db_session.commit()
        
        # Create query service
        query_service = QueryService(
            db_session,
            embedding_service=mock_embedding_service,
            llm_service=mock_llm_service,
            vector_store=mock_pinecone_service
        )
        
        # Process query
        result = await query_service.process_query(
            "What is in the test document?",
            upload_id=None  # Query all documents
        )
        
        assert result is not None
        assert "answer" in result
        assert "citations" in result
        assert len(result["citations"]) > 0

    @pytest.mark.asyncio
    async def test_error_recovery(
        self,
        db_session,
        mock_embedding_service,
        mock_llm_service,
        mock_pinecone_service
    ):
        """Test error handling and recovery in pipeline."""
        # Create service with failing mock
        failing_embedding_service = MockEmbeddingService()
        failing_embedding_service.encode_batch.side_effect = Exception("Embedding failed")
        
        ingestion_service = IngestionService(
            db_session,
            embedding_service=failing_embedding_service,
            vector_store=mock_pinecone_service
        )
        
        # Test file
        test_file = Path("test.pdf")
        test_file.write_text("Test content")
        
        try:
            # Attempt ingestion
            with test_file.open("rb") as f:
                file = UploadFile(filename="test.pdf", file=f)
                upload_batch = await ingestion_service.process_upload_batch([file])
            
            # Verify failure was handled
            assert upload_batch.status == UploadStatus.FAILED
            assert upload_batch.failed_documents == 1
            
            # Verify document status
            document = db_session.query(Document).first()
            assert document.status == DocumentStatus.FAILED
            
        finally:
            test_file.unlink()

    @pytest.mark.asyncio
    async def test_concurrent_operations(
        self,
        db_session,
        mock_embedding_service,
        mock_llm_service,
        mock_pinecone_service
    ):
        """Test concurrent ingestion and querying."""
        ingestion_service = IngestionService(
            db_session,
            embedding_service=mock_embedding_service,
            vector_store=mock_pinecone_service
        )
        
        query_service = QueryService(
            db_session,
            embedding_service=mock_embedding_service,
            llm_service=mock_llm_service,
            vector_store=mock_pinecone_service
        )
        
        # Create test files
        files = []
        for i in range(3):
            path = Path(f"test_{i}.pdf")
            path.write_text(f"Test document {i} content")
            files.append(path)
        
        try:
            # Process multiple files concurrently
            upload_files = []
            for f in files:
                with f.open("rb") as file:
                    upload_files.append(UploadFile(filename=f.name, file=file))
            
            upload_batch = await ingestion_service.process_upload_batch(upload_files)
            
            # Verify all documents processed
            assert upload_batch.total_documents == len(files)
            assert upload_batch.successful_documents == len(files)
            
            # Run concurrent queries
            import asyncio
            queries = [
                query_service.process_query(f"Query {i}")
                for i in range(3)
            ]
            results = await asyncio.gather(*queries)
            
            assert all(r is not None for r in results)
            assert all("answer" in r for r in results)
            
        finally:
            for f in files:
                f.unlink()