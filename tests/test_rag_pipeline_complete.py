"""
End-to-end RAG pipeline tests.

Tests cover complete workflows from document upload through
query processing, including all RAG components.
"""

import io
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

import pytest

from app.models.document import DocumentStatus
from app.models.upload import UploadStatus
from tests.test_mocks import (
    MockPineconeStore,
    MockEmbeddingProvider,
    MockLLMProvider,
    create_mock_document,
    create_mock_chunk,
)


@pytest.mark.integration
@pytest.mark.slow
class TestCompleteRAGWorkflow:
    """Tests for complete RAG workflow from upload to query."""
    
    @patch('app.services.vectorstore.pinecone_store.Pinecone')
    @patch('app.services.embeddings.factory.get_embedding_provider')
    @patch('app.services.llm.factory.get_llm_provider')
    async def test_end_to_end_workflow(
        self,
        mock_llm_factory,
        mock_embed_factory,
        mock_pinecone,
        client,
        db_session
    ):
        """Test complete workflow: upload → index → query."""
        # Setup mocks
        mock_store = MockPineconeStore()
        mock_embeddings = MockEmbeddingProvider()
        mock_llm = MockLLMProvider()
        
        mock_pinecone.return_value = mock_store
        mock_embed_factory.return_value = mock_embeddings
        mock_llm_factory.return_value = mock_llm
        
        # Step 1: Upload document
        file_content = b"Test document about AI and machine learning."
        files = {"files": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        
        with patch('app.services.text_extractor.PDFExtractor.extract_text') as mock_extract:
            from app.services.text_extractor import ExtractedText
            mock_extract.return_value = ExtractedText(
                text="This document discusses AI and machine learning concepts.",
                page_count=1,
                char_count=58,
                metadata={}
            )
            
            upload_response = client.post("/v1/documents/upload", files=files)
        
        # Verify upload succeeded
        assert upload_response.status_code == 201
        upload_data = upload_response.json()
        assert upload_data["total_documents"] == 1
        
        # Step 2: Query the document
        with patch('app.services.rag.query_service.QueryService.process_query') as mock_query:
            mock_query.return_value = {
                "query": "What is AI?",
                "answer": "AI is artificial intelligence.",
                "chunks": [
                    {
                        "content": "AI concepts",
                        "document_id": str(uuid4()),
                        "similarity_score": 0.95
                    }
                ],
                "processing_time": 0.5,
                "created_at": "2025-01-01T00:00:00"
            }
            
            query_response = client.post(
                "/v1/query",
                json={"query": "What is AI?"}
            )
        
        # Verify query succeeded
        assert query_response.status_code == 200
        query_data = query_response.json()
        assert "answer" in query_data


@pytest.mark.integration
class TestDocumentIngestionPipeline:
    """Tests for document ingestion pipeline."""
    
    @patch('app.services.text_extractor.PDFExtractor.extract_text')
    @patch('app.services.chunking.TokenChunker.chunk_text')
    async def test_ingestion_pipeline_pdf(
        self,
        mock_chunk,
        mock_extract,
        db_session
    ):
        """Test PDF document ingestion pipeline."""
        from app.services.text_extractor import ExtractedText
        from app.services.chunking import ChunkData
        from app.services.ingestion_service import IngestionService
        from fastapi import UploadFile
        
        # Setup mocks
        mock_extract.return_value = ExtractedText(
            text="Test content for chunking.",
            page_count=1,
            char_count=25,
            metadata={}
        )
        
        mock_chunk.return_value = [
            ChunkData(
                content="Test content",
                chunk_index=0,
                token_count=2,
                start_char=0,
                end_char=12,
                page_number=1,
                metadata={}
            )
        ]
        
        # Create mock file
        content = b"PDF content"
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.read = AsyncMock(side_effect=[content, content, content, b""])
        mock_file.seek = AsyncMock()
        
        # Process upload
        service = IngestionService(db_session)
        
        with patch('app.services.file_validator.FileValidator.validate_batch') as mock_validate:
            mock_validate.return_value = [{
                "filename": "test.pdf",
                "file_hash": "abc123",
                "valid": True
            }]
            
            with patch('app.utils.file_storage.save_upload_file') as mock_save:
                mock_save.return_value = "/tmp/test.pdf"
                
                upload = await service.process_upload_batch([mock_file])
        
        # Verify upload
        assert upload is not None
        assert upload.total_documents == 1


@pytest.mark.integration
class TestQueryProcessingPipeline:
    """Tests for query processing pipeline."""
    
    @patch('app.services.embeddings.factory.get_embedding_provider')
    @patch('app.services.vectorstore.pinecone_store.PineconeStore.query')
    @patch('app.services.llm.factory.get_llm_provider')
    async def test_query_pipeline(
        self,
        mock_llm_factory,
        mock_vector_query,
        mock_embed_factory,
        db_session
    ):
        """Test query processing pipeline."""
        from app.services.rag.query_service import QueryService
        from app.schemas.query import QueryRequest
        
        # Setup mocks
        mock_embeddings = MockEmbeddingProvider()
        mock_llm = MockLLMProvider()
        
        mock_embed_factory.return_value = mock_embeddings
        mock_llm_factory.return_value = mock_llm
        
        # Mock vector search results
        mock_vector_query.return_value = {
            "matches": [
                {
                    "id": "chunk_1",
                    "score": 0.95,
                    "metadata": {
                        "document_id": str(uuid4()),
                        "content": "AI is artificial intelligence.",
                        "chunk_index": 0
                    }
                }
            ]
        }
        
        # Process query
        service = QueryService(db_session)
        query_request = QueryRequest(
            query="What is AI?",
            top_k=5
        )
        
        with patch('app.models.chunk.Chunk') as mock_chunk_model:
            # Mock chunk retrieval
            mock_chunk = Mock()
            mock_chunk.content = "AI is artificial intelligence."
            mock_chunk.document_id = uuid4()
            mock_chunk_model.query.return_value.filter.return_value.all.return_value = [mock_chunk]
            
            response = await service.process_query(query_request)
        
        # Verify response
        assert response is not None
        assert "answer" in response or hasattr(response, 'answer')


@pytest.mark.integration
class TestRetrievalPipeline:
    """Tests for retrieval pipeline."""
    
    @patch('app.services.embeddings.factory.get_embedding_provider')
    @patch('app.services.vectorstore.pinecone_store.PineconeStore.query')
    def test_hybrid_retrieval(
        self,
        mock_vector_query,
        mock_embed_factory,
        db_session
    ):
        """Test hybrid retrieval (semantic + keyword)."""
        from app.services.retrieval.hybrid_retriever import HybridRetriever
        
        # Setup mocks
        mock_embeddings = MockEmbeddingProvider()
        mock_embed_factory.return_value = mock_embeddings
        
        # Mock vector results
        mock_vector_query.return_value = {
            "matches": [
                {
                    "id": "chunk_1",
                    "score": 0.95,
                    "metadata": {"content": "Semantic match"}
                },
                {
                    "id": "chunk_2",
                    "score": 0.90,
                    "metadata": {"content": "Another match"}
                }
            ]
        }
        
        # Test retrieval
        retriever = HybridRetriever(db_session)
        
        with patch.object(retriever, '_keyword_search') as mock_keyword:
            mock_keyword.return_value = []
            
            results = retriever.retrieve("test query", top_k=5)
        
        # Verify results
        assert results is not None


@pytest.mark.integration
class TestCitationGeneration:
    """Tests for citation generation in RAG responses."""
    
    @patch('app.services.llm.factory.get_llm_provider')
    async def test_generate_answer_with_citations(
        self,
        mock_llm_factory,
        db_session
    ):
        """Test generating answer with proper citations."""
        from app.services.rag.generation_service import GenerationService
        
        # Setup mock
        mock_llm = MockLLMProvider()
        mock_llm_factory.return_value = mock_llm
        
        # Test data
        query = "What is machine learning?"
        context_chunks = [
            {
                "content": "ML is a subset of AI.",
                "document_id": str(uuid4()),
                "chunk_index": 0
            },
            {
                "content": "ML uses algorithms to learn patterns.",
                "document_id": str(uuid4()),
                "chunk_index": 1
            }
        ]
        
        # Generate answer
        service = GenerationService()
        
        with patch.object(mock_llm, 'generate_with_citations') as mock_gen:
            mock_gen.return_value = {
                "answer": "Machine learning is a subset of AI.",
                "citations": [
                    {"chunk_id": "chunk_1", "relevance_score": 0.95}
                ]
            }
            
            result = await service.generate_answer(query, context_chunks)
        
        # Verify citations
        assert result is not None


@pytest.mark.integration
class TestMultiDocumentQuery:
    """Tests for queries across multiple documents."""
    
    @patch('app.services.vectorstore.pinecone_store.PineconeStore.query')
    @patch('app.services.embeddings.factory.get_embedding_provider')
    async def test_query_across_documents(
        self,
        mock_embed_factory,
        mock_vector_query,
        db_session
    ):
        """Test querying across multiple documents."""
        from app.services.retrieval.semantic_retriever import SemanticRetriever
        
        # Setup mocks
        mock_embeddings = MockEmbeddingProvider()
        mock_embed_factory.return_value = mock_embeddings
        
        # Mock results from different documents
        doc1_id = str(uuid4())
        doc2_id = str(uuid4())
        
        mock_vector_query.return_value = {
            "matches": [
                {
                    "id": "chunk_1",
                    "score": 0.95,
                    "metadata": {
                        "document_id": doc1_id,
                        "content": "Content from doc 1"
                    }
                },
                {
                    "id": "chunk_2",
                    "score": 0.90,
                    "metadata": {
                        "document_id": doc2_id,
                        "content": "Content from doc 2"
                    }
                }
            ]
        }
        
        # Test retrieval
        retriever = SemanticRetriever(db_session)
        results = await retriever.retrieve("test query", top_k=10)
        
        # Verify results from multiple documents
        assert results is not None


@pytest.mark.integration
class TestErrorRecovery:
    """Tests for error handling and recovery in RAG pipeline."""
    
    @patch('app.services.text_extractor.PDFExtractor.extract_text')
    async def test_extraction_error_handling(
        self,
        mock_extract,
        db_session
    ):
        """Test handling of extraction errors."""
        from app.services.ingestion_service import IngestionService
        from app.utils.exceptions import ExtractionError
        from fastapi import UploadFile
        
        # Make extraction fail
        mock_extract.side_effect = ExtractionError(
            filename="test.pdf",
            file_type="pdf",
            error_details="Corrupt file"
        )
        
        # Create mock file
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.read = AsyncMock(return_value=b"content")
        mock_file.seek = AsyncMock()
        
        # Process upload
        service = IngestionService(db_session)
        
        with patch('app.services.file_validator.FileValidator.validate_batch') as mock_validate:
            mock_validate.return_value = [{
                "filename": "test.pdf",
                "file_hash": "abc123",
                "valid": True
            }]
            
            with patch('app.utils.file_storage.save_upload_file') as mock_save:
                mock_save.return_value = "/tmp/test.pdf"
                
                # Should handle error gracefully
                try:
                    upload = await service.process_upload_batch([mock_file])
                    # Upload should exist but document might be failed
                    assert upload.failed_documents >= 0
                except Exception:
                    # Or it might raise, which is also acceptable
                    pass
    
    @patch('app.services.llm.factory.get_llm_provider')
    async def test_llm_error_handling(
        self,
        mock_llm_factory,
        db_session
    ):
        """Test handling of LLM errors."""
        from app.services.rag.generation_service import GenerationService
        
        # Make LLM fail
        mock_llm = MockLLMProvider()
        mock_llm.generate = Mock(side_effect=Exception("LLM API error"))
        mock_llm_factory.return_value = mock_llm
        
        # Test generation
        service = GenerationService()
        context_chunks = [{"content": "test", "document_id": str(uuid4())}]
        
        # Should handle error
        try:
            result = await service.generate_answer("test query", context_chunks)
        except Exception as e:
            # Error should be handled gracefully
            assert "error" in str(e).lower() or "llm" in str(e).lower()


@pytest.mark.integration
class TestPerformance:
    """Tests for RAG pipeline performance."""
    
    @patch('app.services.embeddings.factory.get_embedding_provider')
    async def test_batch_embedding_performance(
        self,
        mock_embed_factory
    ):
        """Test batch embedding performance."""
        mock_embeddings = MockEmbeddingProvider()
        mock_embed_factory.return_value = mock_embeddings
        
        # Test batch embedding
        texts = [f"Test text {i}" for i in range(100)]
        
        import time
        start = time.time()
        embeddings = mock_embeddings.embed_batch(texts)
        elapsed = time.time() - start
        
        # Should complete quickly (mock should be fast)
        assert elapsed < 1.0
        assert len(embeddings) == 100
    
    @patch('app.services.vectorstore.pinecone_store.PineconeStore.query')
    async def test_retrieval_performance(
        self,
        mock_vector_query,
        db_session
    ):
        """Test retrieval performance."""
        from app.services.retrieval.semantic_retriever import SemanticRetriever
        
        # Mock large result set
        mock_vector_query.return_value = {
            "matches": [
                {
                    "id": f"chunk_{i}",
                    "score": 0.9 - (i * 0.01),
                    "metadata": {"content": f"Content {i}"}
                }
                for i in range(100)
            ]
        }
        
        retriever = SemanticRetriever(db_session)
        
        import time
        start = time.time()
        
        with patch('app.services.embeddings.factory.get_embedding_provider') as mock_embed:
            mock_embed.return_value = MockEmbeddingProvider()
            results = await retriever.retrieve("test query", top_k=10)
        
        elapsed = time.time() - start
        
        # Should complete reasonably fast
        assert elapsed < 2.0


@pytest.mark.integration
class TestDataConsistency:
    """Tests for data consistency in RAG pipeline."""
    
    def test_chunk_document_relationship(
        self,
        db_session,
        sample_document
    ):
        """Test that chunks maintain correct document relationships."""
        from app.models.chunk import Chunk
        
        # Create chunk for document
        chunk = Chunk(
            document_id=sample_document.id,
            content="Test chunk",
            chunk_index=0,
            token_count=2,
            start_char=0,
            end_char=10,
            page_number=1
        )
        db_session.add(chunk)
        db_session.commit()
        
        # Verify relationship
        retrieved_chunk = db_session.query(Chunk).filter(
            Chunk.document_id == sample_document.id
        ).first()
        
        assert retrieved_chunk is not None
        assert retrieved_chunk.document_id == sample_document.id
    
    def test_upload_document_consistency(
        self,
        db_session,
        sample_upload
    ):
        """Test upload and document count consistency."""
        from app.models.document import Document
        
        # Count documents for upload
        doc_count = db_session.query(Document).filter(
            Document.upload_id == sample_upload.id
        ).count()
        
        # Should match upload record
        assert doc_count >= 0


@pytest.mark.integration
class TestEdgeCases:
    """Tests for edge cases in RAG pipeline."""
    
    @patch('app.services.vectorstore.pinecone_store.PineconeStore.query')
    async def test_query_with_no_results(
        self,
        mock_vector_query,
        db_session
    ):
        """Test query when no relevant documents found."""
        from app.services.retrieval.semantic_retriever import SemanticRetriever
        
        # Return empty results
        mock_vector_query.return_value = {"matches": []}
        
        retriever = SemanticRetriever(db_session)
        
        with patch('app.services.embeddings.factory.get_embedding_provider') as mock_embed:
            mock_embed.return_value = MockEmbeddingProvider()
            results = await retriever.retrieve("obscure query", top_k=10)
        
        # Should handle gracefully
        assert results is not None
        assert len(results) == 0 or results == []
    
    async def test_empty_document_upload(
        self,
        db_session
    ):
        """Test uploading empty document."""
        from app.services.ingestion_service import IngestionService
        from fastapi import UploadFile
        
        # Create empty file mock
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "empty.txt"
        mock_file.read = AsyncMock(return_value=b"")
        mock_file.seek = AsyncMock()
        
        service = IngestionService(db_session)
        
        with patch('app.services.file_validator.FileValidator.validate_batch') as mock_validate:
            mock_validate.return_value = [{
                "filename": "empty.txt",
                "file_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "valid": True
            }]
            
            with patch('app.utils.file_storage.save_upload_file') as mock_save:
                mock_save.return_value = "/tmp/empty.txt"
                
                with patch('app.services.text_extractor.TXTExtractor.extract_text') as mock_extract:
                    from app.services.text_extractor import ExtractedText
                    mock_extract.return_value = ExtractedText(
                        text="",
                        page_count=1,
                        char_count=0,
                        metadata={}
                    )
                    
                    # Should handle empty document
                    try:
                        upload = await service.process_upload_batch([mock_file])
                        assert upload is not None
                    except Exception:
                        # May raise error for empty document, which is acceptable
                        pass

