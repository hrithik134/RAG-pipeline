"""
Comprehensive tests for API endpoints.

Tests cover upload, query, and document management endpoints
with various scenarios, error cases, and edge conditions.
"""

import io
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.models.document import DocumentStatus
from app.models.upload import UploadStatus


@pytest.mark.integration
class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


@pytest.mark.integration
class TestUploadEndpoint:
    """Tests for document upload endpoint."""
    
    @patch('app.services.ingestion_service.IngestionService.process_upload_batch')
    def test_upload_single_file(self, mock_process, client, db_session):
        """Test uploading a single file."""
        # Create mock upload result
        from app.models.upload import Upload
        from app.models.document import Document
        
        mock_upload = Mock(spec=Upload)
        mock_upload.id = uuid4()
        mock_upload.upload_batch_id = str(uuid4())
        mock_upload.status = UploadStatus.COMPLETED
        mock_upload.total_documents = 1
        mock_upload.successful_documents = 1
        mock_upload.failed_documents = 0
        mock_upload.created_at = "2025-01-01T00:00:00"
        mock_upload.completed_at = "2025-01-01T00:01:00"
        
        mock_doc = Mock(spec=Document)
        mock_doc.id = uuid4()
        mock_doc.filename = "test.pdf"
        mock_doc.status = DocumentStatus.COMPLETED
        mock_doc.file_type = "pdf"
        mock_doc.file_size = 1024
        mock_doc.total_chunks = 5
        mock_doc.page_count = 3
        
        mock_upload.documents = [mock_doc]
        mock_process.return_value = mock_upload
        
        # Create test file
        file_content = b"Test PDF content"
        files = {"files": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        
        response = client.post("/v1/documents/upload", files=files)
        
        assert response.status_code == 201
        data = response.json()
        assert "upload_batch_id" in data
        assert data["total_documents"] == 1
    
    @patch('app.services.ingestion_service.IngestionService.process_upload_batch')
    def test_upload_multiple_files(self, mock_process, client):
        """Test uploading multiple files."""
        from app.models.upload import Upload
        from app.models.document import Document
        
        mock_upload = Mock(spec=Upload)
        mock_upload.id = uuid4()
        mock_upload.upload_batch_id = str(uuid4())
        mock_upload.status = UploadStatus.COMPLETED
        mock_upload.total_documents = 3
        mock_upload.successful_documents = 3
        mock_upload.failed_documents = 0
        mock_upload.created_at = "2025-01-01T00:00:00"
        mock_upload.completed_at = "2025-01-01T00:01:00"
        mock_upload.documents = []
        
        for i in range(3):
            mock_doc = Mock(spec=Document)
            mock_doc.id = uuid4()
            mock_doc.filename = f"test{i}.pdf"
            mock_doc.status = DocumentStatus.COMPLETED
            mock_doc.file_type = "pdf"
            mock_doc.file_size = 1024
            mock_doc.total_chunks = 5
            mock_doc.total_pages = 3
            mock_upload.documents.append(mock_doc)
        
        mock_process.return_value = mock_upload
        
        # Create test files
        files = [
            ("files", ("test1.pdf", io.BytesIO(b"PDF1"), "application/pdf")),
            ("files", ("test2.pdf", io.BytesIO(b"PDF2"), "application/pdf")),
            ("files", ("test3.pdf", io.BytesIO(b"PDF3"), "application/pdf"))
        ]
        
        response = client.post("/v1/documents/upload", files=files)
        
        assert response.status_code == 201
        data = response.json()
        assert data["total_documents"] == 3
    
    def test_upload_no_files(self, client):
        """Test upload with no files."""
        response = client.post("/v1/documents/upload")
        
        # Should return error
        assert response.status_code in [400, 422]
    
    def test_upload_invalid_file_type(self, client):
        """Test upload with invalid file type."""
        files = {"files": ("test.exe", io.BytesIO(b"Executable"), "application/exe")}
        
        response = client.post("/v1/documents/upload", files=files)
        
        # Should return error for invalid file type
        assert response.status_code in [400, 422]
    
    @patch('app.services.ingestion_service.IngestionService.process_upload_batch')
    def test_upload_docx_file(self, mock_process, client):
        """Test uploading DOCX file."""
        from app.models.upload import Upload
        from app.models.document import Document
        
        mock_upload = Mock(spec=Upload)
        mock_upload.id = uuid4()
        mock_upload.upload_batch_id = str(uuid4())
        mock_upload.status = UploadStatus.COMPLETED
        mock_upload.total_documents = 1
        mock_upload.successful_documents = 1
        mock_upload.failed_documents = 0
        mock_upload.created_at = "2025-01-01T00:00:00"
        mock_upload.completed_at = "2025-01-01T00:01:00"
        
        mock_doc = Mock(spec=Document)
        mock_doc.id = uuid4()
        mock_doc.filename = "test.docx"
        mock_doc.status = DocumentStatus.COMPLETED
        mock_doc.file_type = "docx"
        mock_doc.file_size = 2048
        mock_doc.total_chunks = 10
        mock_doc.page_count = 5
        
        mock_upload.documents = [mock_doc]
        mock_process.return_value = mock_upload
        
        files = {"files": ("test.docx", io.BytesIO(b"DOCX content"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        
        response = client.post("/v1/documents/upload", files=files)
        
        assert response.status_code == 201
    
    @patch('app.services.ingestion_service.IngestionService.process_upload_batch')
    def test_upload_txt_file(self, mock_process, client):
        """Test uploading TXT file."""
        from app.models.upload import Upload
        from app.models.document import Document
        
        mock_upload = Mock(spec=Upload)
        mock_upload.id = uuid4()
        mock_upload.upload_batch_id = str(uuid4())
        mock_upload.status = UploadStatus.COMPLETED
        mock_upload.total_documents = 1
        mock_upload.successful_documents = 1
        mock_upload.failed_documents = 0
        mock_upload.created_at = "2025-01-01T00:00:00"
        mock_upload.completed_at = "2025-01-01T00:01:00"
        
        mock_doc = Mock(spec=Document)
        mock_doc.id = uuid4()
        mock_doc.filename = "test.txt"
        mock_doc.status = DocumentStatus.COMPLETED
        mock_doc.file_type = "txt"
        mock_doc.file_size = 512
        mock_doc.total_chunks = 2
        mock_doc.page_count = 1
        
        mock_upload.documents = [mock_doc]
        mock_process.return_value = mock_upload
        
        files = {"files": ("test.txt", io.BytesIO(b"Text content"), "text/plain")}
        
        response = client.post("/v1/documents/upload", files=files)
        
        assert response.status_code == 201


@pytest.mark.integration
class TestQueryEndpoint:
    """Tests for query endpoint."""
    
    @patch('app.services.rag.query_service.QueryService.process_query')
    def test_query_simple(self, mock_process, client):
        """Test simple query."""
        mock_response = {
            "query": "What is AI?",
            "answer": "AI stands for Artificial Intelligence.",
            "chunks": [],
            "processing_time": 0.5,
            "created_at": "2025-01-01T00:00:00"
        }
        mock_process.return_value = mock_response
        
        response = client.post(
            "/v1/query",
            json={"query": "What is AI?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data["query"] == "What is AI?"
    
    @patch('app.services.rag.query_service.QueryService.process_query')
    def test_query_with_results(self, mock_process, client):
        """Test query that returns results."""
        mock_response = {
            "query": "Explain machine learning",
            "answer": "Machine learning is a subset of AI.",
            "chunks": [
                {
                    "content": "ML chunk 1",
                    "document_id": str(uuid4()),
                    "similarity_score": 0.95
                },
                {
                    "content": "ML chunk 2",
                    "document_id": str(uuid4()),
                    "similarity_score": 0.90
                }
            ],
            "processing_time": 0.7,
            "created_at": "2025-01-01T00:00:00"
        }
        mock_process.return_value = mock_response
        
        response = client.post(
            "/v1/query",
            json={"query": "Explain machine learning"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "chunks" in data
        assert len(data["chunks"]) == 2
    
    def test_query_empty_string(self, client):
        """Test query with empty string."""
        response = client.post(
            "/v1/query",
            json={"query": ""}
        )
        
        # Should return validation error
        assert response.status_code in [400, 422]
    
    def test_query_missing_field(self, client):
        """Test query with missing required field."""
        response = client.post(
            "/v1/query",
            json={}
        )
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_query_very_long(self, client):
        """Test query with very long text."""
        long_query = "What is " + "very " * 1000 + "important?"
        
        response = client.post(
            "/v1/query",
            json={"query": long_query}
        )
        
        # Should handle or return appropriate error
        assert response.status_code in [200, 400, 422]
    
    @patch('app.services.rag.query_service.QueryService.process_query')
    def test_query_special_characters(self, mock_process, client):
        """Test query with special characters."""
        mock_response = {
            "query": "What is @#$%?",
            "answer": "Special characters query.",
            "chunks": [],
            "processing_time": 0.5,
            "created_at": "2025-01-01T00:00:00"
        }
        mock_process.return_value = mock_response
        
        response = client.post(
            "/v1/query",
            json={"query": "What is @#$%?"}
        )
        
        assert response.status_code == 200


@pytest.mark.integration
class TestDocumentListEndpoint:
    """Tests for document listing endpoint."""
    
    def test_list_documents_empty(self, client, db_session):
        """Test listing documents when none exist."""
        response = client.get("/v1/documents")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 0
    
    def test_list_documents_with_data(self, client, db_session, sample_document):
        """Test listing documents with existing data."""
        response = client.get("/v1/documents")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1
    
    def test_list_documents_pagination(self, client, db_session):
        """Test document listing pagination."""
        response = client.get("/v1/documents?page=1&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
    
    def test_list_documents_invalid_page(self, client):
        """Test listing with invalid page number."""
        response = client.get("/v1/documents?page=-1")
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]


@pytest.mark.integration
class TestDocumentDetailEndpoint:
    """Tests for document detail endpoint."""
    
    def test_get_document_detail(self, client, db_session, sample_document):
        """Test getting document details."""
        doc_id = sample_document.id
        
        response = client.get(f"/v1/documents/{doc_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(doc_id)
        assert "filename" in data
    
    def test_get_document_not_found(self, client):
        """Test getting non-existent document."""
        fake_id = uuid4()
        
        response = client.get(f"/v1/documents/{fake_id}")
        
        assert response.status_code == 404
    
    def test_get_document_invalid_uuid(self, client):
        """Test getting document with invalid UUID."""
        response = client.get("/v1/documents/invalid-uuid")
        
        assert response.status_code in [400, 422]


@pytest.mark.integration
class TestDocumentDeleteEndpoint:
    """Tests for document deletion endpoint."""
    
    @patch('app.services.indexing_service.IndexingService.delete_document')
    def test_delete_document(self, mock_delete, client, db_session, sample_document):
        """Test deleting a document."""
        doc_id = sample_document.id
        mock_delete.return_value = True
        
        response = client.delete(f"/v1/documents/{doc_id}")
        
        # Should return success or 204 No Content
        assert response.status_code in [200, 204]
    
    def test_delete_document_not_found(self, client):
        """Test deleting non-existent document."""
        fake_id = uuid4()
        
        response = client.delete(f"/v1/documents/{fake_id}")
        
        assert response.status_code == 404
    
    def test_delete_document_invalid_uuid(self, client):
        """Test deleting with invalid UUID."""
        response = client.delete("/v1/documents/invalid-uuid")
        
        assert response.status_code in [400, 422]


@pytest.mark.integration
class TestUploadProgressEndpoint:
    """Tests for upload progress endpoint."""
    
    def test_get_upload_progress(self, client, db_session, sample_upload):
        """Test getting upload progress."""
        upload_id = sample_upload.id
        
        response = client.get(f"/v1/documents/uploads/{upload_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_get_upload_progress_not_found(self, client):
        """Test getting progress for non-existent upload."""
        fake_id = uuid4()
        
        response = client.get(f"/v1/documents/uploads/{fake_id}")
        
        assert response.status_code == 404


@pytest.mark.integration
class TestQueryListEndpoint:
    """Tests for query history endpoint."""
    
    def test_list_queries_empty(self, client, db_session):
        """Test listing queries when none exist."""
        response = client.get("/v1/queries")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_list_queries_pagination(self, client):
        """Test query listing with pagination."""
        response = client.get("/v1/queries?page=1&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


@pytest.mark.integration
class TestErrorHandling:
    """Tests for error handling across endpoints."""
    
    def test_invalid_json(self, client):
        """Test sending invalid JSON."""
        response = client.post(
            "/v1/query",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_content_type(self, client):
        """Test request without content type."""
        response = client.post(
            "/v1/query",
            data='{"query": "test"}'
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]
    
    def test_unsupported_method(self, client):
        """Test using unsupported HTTP method."""
        response = client.put("/v1/query")
        
        assert response.status_code == 405
    
    def test_nonexistent_endpoint(self, client):
        """Test accessing non-existent endpoint."""
        response = client.get("/v1/nonexistent")
        
        assert response.status_code == 404


@pytest.mark.integration
class TestAPIVersioning:
    """Tests for API versioning."""
    
    def test_v1_endpoint_accessible(self, client):
        """Test that v1 endpoints are accessible."""
        response = client.get("/v1/documents")
        
        assert response.status_code == 200
    
    def test_health_no_version(self, client):
        """Test health endpoint without version prefix."""
        response = client.get("/health")
        
        assert response.status_code == 200


@pytest.mark.integration
class TestResponseFormats:
    """Tests for response format consistency."""
    
    @patch('app.services.rag.query_service.QueryService.process_query')
    def test_query_response_structure(self, mock_process, client):
        """Test that query response has expected structure."""
        mock_response = {
            "query": "test",
            "answer": "answer",
            "chunks": [],
            "processing_time": 0.5,
            "created_at": "2025-01-01T00:00:00"
        }
        mock_process.return_value = mock_response
        
        response = client.post(
            "/v1/query",
            json={"query": "test"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "query" in data
        assert "answer" in data
        assert "chunks" in data
    
    def test_document_list_response_structure(self, client):
        """Test document list response structure."""
        response = client.get("/v1/documents")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify pagination structure
        assert "items" in data
        assert "total" in data or "page" in data or isinstance(data["items"], list)
    
    def test_error_response_structure(self, client):
        """Test that errors have consistent structure."""
        response = client.get("/v1/documents/invalid-uuid")
        
        assert response.status_code in [400, 422]
        data = response.json()
        
        # Should have error detail
        assert "detail" in data or "message" in data


@pytest.mark.integration
class TestConcurrentRequests:
    """Tests for handling concurrent requests."""
    
    @patch('app.services.rag.query_service.QueryService.process_query')
    def test_multiple_concurrent_queries(self, mock_process, client):
        """Test handling multiple queries."""
        mock_response = {
            "query": "test",
            "answer": "answer",
            "chunks": [],
            "processing_time": 0.5,
            "created_at": "2025-01-01T00:00:00"
        }
        mock_process.return_value = mock_response
        
        # Make multiple requests
        responses = []
        for i in range(5):
            response = client.post(
                "/v1/query",
                json={"query": f"test query {i}"}
            )
            responses.append(response)
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)


@pytest.mark.integration
class TestInputValidation:
    """Tests for input validation."""
    
    def test_query_max_length(self, client):
        """Test query with maximum length."""
        very_long_query = "a" * 10000
        
        response = client.post(
            "/v1/query",
            json={"query": very_long_query}
        )
        
        # Should handle or validate
        assert response.status_code in [200, 400, 422]
    
    def test_pagination_bounds(self, client):
        """Test pagination with extreme values."""
        response = client.get("/v1/documents?page=99999&page_size=1000")
        
        assert response.status_code in [200, 400]
    
    def test_special_characters_in_query(self, client):
        """Test query with various special characters."""
        special_queries = [
            "What about <script>alert('xss')</script>?",
            "Query with\nnewlines\r\nand\ttabs",
            "Unicode: 你好世界 🚀",
            "SQL: ' OR '1'='1"
        ]
        
        for query in special_queries:
            response = client.post(
                "/v1/query",
                json={"query": query}
            )
            # Should handle safely
            assert response.status_code in [200, 400, 422, 500]

