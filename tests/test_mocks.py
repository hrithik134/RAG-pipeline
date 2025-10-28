"""
Reusable mock factories and configurations for testing.

This module provides mock implementations of external services
and shared test utilities.
"""

from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock
from uuid import uuid4


class MockPineconeStore:
    """Mock implementation of Pinecone vector store."""
    
    def __init__(self):
        """Initialize mock Pinecone store with in-memory storage."""
        self.vectors = {}
        self.namespaces = {}
    
    def upsert(self, vectors: List[tuple], namespace: str = "default") -> Dict[str, Any]:
        """Mock upsert operation."""
        if namespace not in self.vectors:
            self.vectors[namespace] = []
        
        for vector_id, values, metadata in vectors:
            self.vectors[namespace].append({
                "id": vector_id,
                "values": values,
                "metadata": metadata
            })
        
        return {
            "status": "success",
            "upserted_count": len(vectors)
        }
    
    def query(
        self,
        vector: List[float],
        top_k: int = 5,
        namespace: str = "default",
        filter: Dict = None,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """Mock query operation returning fake results."""
        vectors_in_ns = self.vectors.get(namespace, [])
        
        # Return top_k results (or all if fewer available)
        results = vectors_in_ns[:top_k]
        
        matches = []
        for i, vec in enumerate(results):
            match = {
                "id": vec["id"],
                "score": 0.95 - (i * 0.05),  # Decreasing scores
                "values": vec["values"] if include_metadata else None,
            }
            if include_metadata and "metadata" in vec:
                match["metadata"] = vec["metadata"]
            matches.append(match)
        
        return {
            "matches": matches,
            "namespace": namespace
        }
    
    def delete(self, ids: List[str] = None, namespace: str = "default", delete_all: bool = False) -> Dict[str, Any]:
        """Mock delete operation."""
        if delete_all:
            self.vectors[namespace] = []
            return {"status": "success", "deleted_count": "all"}
        
        if ids and namespace in self.vectors:
            original_count = len(self.vectors[namespace])
            self.vectors[namespace] = [
                v for v in self.vectors[namespace] if v["id"] not in ids
            ]
            deleted_count = original_count - len(self.vectors[namespace])
            return {"status": "success", "deleted_count": deleted_count}
        
        return {"status": "success", "deleted_count": 0}
    
    def describe_index_stats(self) -> Dict[str, Any]:
        """Mock index stats."""
        total_count = sum(len(vectors) for vectors in self.vectors.values())
        return {
            "dimension": 768,
            "index_fullness": 0.1,
            "total_vector_count": total_count,
            "namespaces": {
                ns: {"vector_count": len(vectors)}
                for ns, vectors in self.vectors.items()
            }
        }


class MockEmbeddingProvider:
    """Mock implementation of embedding provider."""
    
    def __init__(self, dimension: int = 768):
        """Initialize mock embedding provider."""
        self.dimension = dimension
        self.call_count = 0
    
    def embed_text(self, text: str) -> List[float]:
        """Return fake embedding vector."""
        self.call_count += 1
        # Return deterministic vector based on text length for testing
        base_value = len(text) / 1000.0
        return [base_value + (i * 0.001) for i in range(self.dimension)]
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Return fake batch embeddings."""
        return [self.embed_text(text) for text in texts]
    
    async def aembed_text(self, text: str) -> List[float]:
        """Async version of embed_text."""
        return self.embed_text(text)
    
    async def aembed_batch(self, texts: List[str]) -> List[List[float]]:
        """Async version of embed_batch."""
        return self.embed_batch(texts)
    
    def get_embedding_dimension(self) -> int:
        """Return embedding dimension."""
        return self.dimension


class MockLLMProvider:
    """Mock implementation of LLM provider."""
    
    def __init__(self):
        """Initialize mock LLM provider."""
        self.call_count = 0
        self.last_prompt = None
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Return fake LLM response."""
        self.call_count += 1
        self.last_prompt = prompt
        
        # Generate a mock response based on prompt
        if "question" in prompt.lower():
            return "This is a mocked answer to your question. It provides relevant information based on the context provided."
        elif "summarize" in prompt.lower():
            return "This is a summary of the provided content."
        else:
            return f"Mocked response for prompt: {prompt[:50]}..."
    
    async def agenerate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Async version of generate."""
        return self.generate(prompt, max_tokens, temperature, **kwargs)
    
    def generate_with_citations(
        self,
        prompt: str,
        context_chunks: List[Dict],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response with citations."""
        self.call_count += 1
        return {
            "answer": "Mocked answer with citations.",
            "citations": [
                {
                    "chunk_id": chunk.get("id", "chunk_1"),
                    "relevance_score": 0.9
                }
                for chunk in context_chunks[:3]
            ]
        }


class MockOpenAIClient:
    """Mock implementation of OpenAI client."""
    
    def __init__(self):
        """Initialize mock OpenAI client."""
        self.embeddings = MockOpenAIEmbeddings()
        self.chat = MockOpenAIChat()


class MockOpenAIEmbeddings:
    """Mock OpenAI embeddings."""
    
    def create(self, input: str | List[str], model: str = "text-embedding-ada-002") -> Any:
        """Mock embedding creation."""
        if isinstance(input, str):
            input = [input]
        
        data = []
        for i, text in enumerate(input):
            data.append({
                "object": "embedding",
                "index": i,
                "embedding": [0.1] * 1536  # OpenAI embedding dimension
            })
        
        return MockEmbeddingResponse(data)


class MockEmbeddingResponse:
    """Mock embedding response."""
    
    def __init__(self, data: List[Dict]):
        self.data = data


class MockOpenAIChat:
    """Mock OpenAI chat completions."""
    
    def completions_create(
        self,
        model: str = "gpt-4",
        messages: List[Dict] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> Any:
        """Mock chat completion."""
        return MockChatCompletion(
            content="This is a mocked GPT response to your query.",
            model=model
        )


class MockChatCompletion:
    """Mock chat completion response."""
    
    def __init__(self, content: str, model: str):
        self.choices = [MockChoice(content)]
        self.model = model
        self.usage = {"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50}


class MockChoice:
    """Mock choice in completion."""
    
    def __init__(self, content: str):
        self.message = MockMessage(content)
        self.finish_reason = "stop"


class MockMessage:
    """Mock message in choice."""
    
    def __init__(self, content: str):
        self.content = content
        self.role = "assistant"


class MockGoogleAIClient:
    """Mock implementation of Google AI client."""
    
    def __init__(self):
        """Initialize mock Google AI client."""
        self.call_count = 0
    
    def generate_content(self, prompt: str, **kwargs) -> Any:
        """Mock content generation."""
        self.call_count += 1
        return MockGoogleResponse(
            text="This is a mocked response from Google's Gemini model."
        )
    
    def embed_content(self, content: str, **kwargs) -> Any:
        """Mock embedding generation."""
        return MockGoogleEmbeddingResponse(
            embedding=[0.1] * 768  # Google embedding dimension
        )


class MockGoogleResponse:
    """Mock Google AI response."""
    
    def __init__(self, text: str):
        self.text = text
        self.candidates = [{"content": {"parts": [{"text": text}]}}]


class MockGoogleEmbeddingResponse:
    """Mock Google AI embedding response."""
    
    def __init__(self, embedding: List[float]):
        self.embedding = {"values": embedding}


# Factory functions for creating mocks


def create_mock_pinecone_client() -> Mock:
    """Create a mock Pinecone client."""
    mock_client = Mock()
    mock_store = MockPineconeStore()
    mock_index = Mock()
    
    # Wire up the mock
    mock_index.upsert = mock_store.upsert
    mock_index.query = mock_store.query
    mock_index.delete = mock_store.delete
    mock_index.describe_index_stats = mock_store.describe_index_stats
    
    mock_client.Index.return_value = mock_index
    
    return mock_client


def create_mock_embedding_provider(dimension: int = 768) -> MockEmbeddingProvider:
    """Create a mock embedding provider."""
    return MockEmbeddingProvider(dimension=dimension)


def create_mock_llm_provider() -> MockLLMProvider:
    """Create a mock LLM provider."""
    return MockLLMProvider()


def create_mock_openai_client() -> MockOpenAIClient:
    """Create a mock OpenAI client."""
    return MockOpenAIClient()


def create_mock_google_client() -> MockGoogleAIClient:
    """Create a mock Google AI client."""
    return MockGoogleAIClient()


def create_mock_file_content(content: str = "Test content", file_type: str = "pdf") -> bytes:
    """Create mock file content."""
    if file_type == "pdf":
        return f"%PDF-1.4\n{content}\n%%EOF".encode()
    elif file_type == "txt":
        return content.encode('utf-8')
    elif file_type == "docx":
        # Minimal DOCX structure
        from io import BytesIO
        from zipfile import ZipFile
        
        zip_buffer = BytesIO()
        with ZipFile(zip_buffer, 'w') as zip_file:
            zip_file.writestr('[Content_Types].xml', '<?xml version="1.0"?>')
            zip_file.writestr(
                'word/document.xml',
                f'<w:document><w:body><w:p><w:r><w:t>{content}</w:t></w:r></w:p></w:body></w:document>'
            )
        return zip_buffer.getvalue()
    else:
        return content.encode()


def create_mock_upload_file(filename: str = "test.pdf", content: bytes = None) -> Mock:
    """Create a mock UploadFile."""
    from fastapi import UploadFile
    
    if content is None:
        content = b"Test file content"
    
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = filename
    mock_file.read = AsyncMock(return_value=content)
    mock_file.seek = AsyncMock()
    mock_file.file = Mock()
    
    return mock_file


def create_mock_document(
    doc_id: str = None,
    filename: str = "test.pdf",
    status: str = "completed",
    chunks: int = 5
) -> Dict[str, Any]:
    """Create a mock document dictionary."""
    return {
        "id": doc_id or str(uuid4()),
        "filename": filename,
        "file_type": "pdf",
        "file_size": 1024,
        "file_hash": "abc123",
        "status": status,
        "total_chunks": chunks,
        "total_pages": 3,
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00"
    }


def create_mock_chunk(
    chunk_id: str = None,
    document_id: str = None,
    content: str = "Test chunk content",
    chunk_index: int = 0
) -> Dict[str, Any]:
    """Create a mock chunk dictionary."""
    return {
        "id": chunk_id or str(uuid4()),
        "document_id": document_id or str(uuid4()),
        "content": content,
        "chunk_index": chunk_index,
        "token_count": 10,
        "start_char": 0,
        "end_char": len(content),
        "page_number": 1,
        "embedding_id": f"emb_{chunk_index}"
    }


def create_mock_query_result(
    query: str = "test query",
    answer: str = "test answer",
    chunks: int = 3
) -> Dict[str, Any]:
    """Create a mock query result."""
    return {
        "query": query,
        "answer": answer,
        "chunks": [
            {
                "content": f"Chunk {i} content",
                "document_id": str(uuid4()),
                "similarity_score": 0.9 - (i * 0.1)
            }
            for i in range(chunks)
        ],
        "processing_time": 0.5
    }


# Pytest fixtures that can be imported


def pytest_configure():
    """Configure pytest with custom markers."""
    import pytest
    
    pytest.mock_pinecone = create_mock_pinecone_client
    pytest.mock_embeddings = create_mock_embedding_provider
    pytest.mock_llm = create_mock_llm_provider
    pytest.mock_openai = create_mock_openai_client
    pytest.mock_google = create_mock_google_client

