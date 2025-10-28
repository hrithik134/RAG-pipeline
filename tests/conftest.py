"""
Pytest configuration and shared fixtures.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app
from app.models.base import Base
from app.models.document import Document, DocumentStatus
from app.models.upload import Upload, UploadStatus
from app.models.query import Query
from tests.mocks import (
    MockEmbeddingService,
    MockLLMService, 
    MockPineconeService,
    MockDocumentExtractor
)

# Create in-memory SQLite database for testing
TEST_DB_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session with in-memory SQLite."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    """Get test client with overridden dependencies."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def mock_embedding_service():
    """Get mock embedding service."""
    return MockEmbeddingService()

@pytest.fixture
def mock_llm_service():
    """Get mock LLM service."""
    return MockLLMService()

@pytest.fixture
def mock_pinecone_service():
    """Get mock Pinecone service."""
    return MockPineconeService()

@pytest.fixture
def mock_document_extractor():
    """Get mock document extractor."""
    return MockDocumentExtractor()


@pytest.fixture
def mock_document():
    """Create a mock document with required attributes."""
    doc = Mock(spec=Document)
    doc.id = uuid4()
    doc.upload_id = uuid4()
    doc.filename = "test.pdf"
    doc.file_path = "/test/test.pdf"
    doc.file_size = 1024
    doc.file_type = "pdf"
    doc.file_hash = "hash123"
    doc.page_count = 5
    doc.total_chunks = 10
    doc.status = DocumentStatus.COMPLETED
    doc.processed_at = None
    doc.error_message = None
    return doc


@pytest.fixture
def client() -> TestClient:
    """
    Create a FastAPI test client.
    """
    return TestClient(app)


@pytest.fixture
def settings():
    """
    Get application settings for testing.
    """
    from app.config import get_settings

    return get_settings()


@pytest.fixture
def temp_dir():
    """
    Create a temporary directory for test files.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_uuid():
    """Generate a sample UUID for testing."""
    return uuid4()


@pytest.fixture
def mock_pinecone_client():
    """Create a mock Pinecone client."""
    mock_client = Mock()
    mock_index = Mock()
    
    # Mock upsert
    mock_index.upsert.return_value = {"status": "success"}
    
    # Mock query with fake results
    mock_index.query.return_value = {
        "matches": [
            {
                "id": "chunk1",
                "score": 0.95,
                "metadata": {"document_id": "doc1", "chunk_index": 0}
            },
            {
                "id": "chunk2", 
                "score": 0.90,
                "metadata": {"document_id": "doc1", "chunk_index": 1}
            }
        ]
    }
    
    # Mock delete
    mock_index.delete.return_value = {"status": "success"}
    
    # Setup client to return index
    mock_client.Index.return_value = mock_index
    
    return mock_client


@pytest.fixture
def mock_embedding_provider():
    """Create a mock embedding provider."""
    mock_provider = Mock()
    
    def embed_text(text: str) -> list:
        """Return fake 768-dimensional embedding."""
        return [0.1] * 768
    
    def embed_batch(texts: list) -> list:
        """Return fake batch embeddings."""
        return [embed_text(text) for text in texts]
    
    mock_provider.embed_text = embed_text
    mock_provider.embed_batch = embed_batch
    
    return mock_provider


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider."""
    mock_provider = Mock()
    
    def generate_response(prompt: str, **kwargs) -> str:
        """Return fake LLM response."""
        return f"Mocked response for: {prompt[:50]}..."
    
    mock_provider.generate_response = generate_response
    
    return mock_provider


@pytest.fixture
def sample_document(db_session):
    """Create a sample document in the database."""
    upload = Upload(
        upload_batch_id=str(uuid4()),
        status=UploadStatus.COMPLETED
    )
    db_session.add(upload)
    db_session.flush()
    
    doc = Document(
        upload_id=upload.id,
        filename="test_document.pdf",
        file_type="pdf",
        file_size=1024,
        file_hash="abc123",
        file_path="uploads/test_document.pdf",
        status=DocumentStatus.COMPLETED,
        total_chunks=5,
        page_count=3
    )
    db_session.add(doc)
    db_session.commit()
    
    return doc


@pytest.fixture
def sample_upload(db_session):
    """Create a sample upload in the database."""
    upload = Upload(
        upload_batch_id=str(uuid4()),
        status=UploadStatus.COMPLETED,
        total_documents=1,
        successful_documents=1
    )
    db_session.add(upload)
    db_session.commit()
    
    return upload


@pytest.fixture
def mock_file_content():
    """Return mock file content for testing."""
    return b"Sample PDF content" * 100


@pytest.fixture
def pdf_file_content():
    """Return mock PDF file content."""
    # Minimal valid PDF structure
    pdf_header = b"%PDF-1.4\n"
    pdf_content = b"stream\n" + b"Test PDF content" + b"\nendstream\n"
    pdf_trailer = b"%%EOF"
    
    return pdf_header + pdf_content + pdf_trailer


@pytest.fixture
def docx_file_content():
    """Return mock DOCX file content."""
    # DOCX is a ZIP archive, minimal valid structure
    from io import BytesIO
    from zipfile import ZipFile
    
    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, 'w') as zip_file:
        zip_file.writestr('[Content_Types].xml', '<?xml version="1.0"?>')
        zip_file.writestr('word/document.xml', '<w:document><w:body><w:p><w:r><w:t>Test content</w:t></w:r></w:p></w:body></w:document>')
    
    return zip_buffer.getvalue()


@pytest.fixture
def sample_chunk(db_session, sample_document):
    """Create a sample chunk in the database."""
    from app.models.chunk import Chunk
    
    chunk = Chunk(
        document_id=sample_document.id,
        content="This is a test chunk of text.",
        chunk_index=0,
        token_count=10,
        start_char=0,
        end_char=28,
        page_number=1,
        embedding_id="emb_test_123"
    )
    db_session.add(chunk)
    db_session.commit()
    
    return chunk


@pytest.fixture
def sample_query(db_session):
    """Create a sample query in the database."""
    from app.models.query import Query
    
    query = Query(
        query_text="What is machine learning?",
        status="completed",
        answer="Machine learning is a subset of AI.",
        processing_time=0.5
    )
    db_session.add(query)
    db_session.commit()
    
    return query


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    from tests.test_mocks import MockPineconeStore
    return MockPineconeStore()


@pytest.fixture
def mock_embedding_service():
    """Create a mock embedding service."""
    from tests.test_mocks import MockEmbeddingProvider
    return MockEmbeddingProvider()


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service."""
    from tests.test_mocks import MockLLMProvider
    return MockLLMProvider()


@pytest.fixture
async def async_mock_file():
    """Create an async mock upload file."""
    file = Mock()
    file.filename = "test.pdf"
    file.read = AsyncMock(return_value=b"Test content")
    file.seek = AsyncMock()
    return file


@pytest.fixture
def create_test_file(temp_dir):
    """Factory fixture for creating test files."""
    def _create_file(filename: str, content: bytes, file_type: str = "pdf"):
        file_path = temp_dir / filename
        file_path.write_bytes(content)
        return file_path
    
    return _create_file


@pytest.fixture
def create_mock_chunks():
    """Factory fixture for creating mock chunks."""
    def _create_chunks(count: int = 5, document_id: str = None):
        from tests.test_mocks import create_mock_chunk
        doc_id = document_id or str(uuid4())
        return [create_mock_chunk(document_id=doc_id, chunk_index=i) for i in range(count)]
    
    return _create_chunks


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    from tests.test_mocks import create_mock_openai_client
    return create_mock_openai_client()


@pytest.fixture
def mock_google_client():
    """Create a mock Google AI client."""
    from tests.test_mocks import create_mock_google_client
    return create_mock_google_client()
