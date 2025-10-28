"""Mocks for external services and dependencies."""

from unittest.mock import MagicMock
from typing import Dict, List, Optional

class MockEmbeddingService:
    """Mock implementation of embedding service."""
    
    async def encode_batch(self, texts: List[str], **kwargs) -> Dict:
        """Mock embedding generation."""
        # Return consistent mock embeddings for testing
        return {
            "embeddings": [[0.1] * 1536 for _ in texts],
            "model": "test-embedding-model",
            "total_tokens": sum(len(text.split()) for text in texts)
        }

class MockLLMService:
    """Mock implementation of LLM service."""
    
    async def initialize(self) -> None:
        """Initialize the service."""
        pass
    
    async def generate(self, prompt: str, **kwargs) -> Dict:
        """Mock text generation."""
        from app.services.llm.base import LLMResponse
        return LLMResponse(
            text="This is a mock response",
            tokens_used=len(prompt.split()),
            model="test-llm-model"
        )
        
    async def generate_with_metadata(self, prompt: str, metadata: Optional[Dict] = None, **kwargs) -> Dict:
        """Mock text generation with metadata."""
        response = await self.generate(prompt, **kwargs)
        response.metadata = metadata or {}
        return response
        
    async def process_batch(self, prompts: List[str], **kwargs) -> List[Dict]:
        """Mock batch text generation."""
        return [await self.generate(prompt, **kwargs) for prompt in prompts]

class MockPineconeService:
    """Mock implementation of Pinecone service."""
    
    def __init__(self):
        self.vectors: Dict = {}
    
    async def upsert(self, vectors: List[Dict], namespace: str):
        """Mock vector upsert."""
        for vector in vectors:
            self.vectors[vector["id"]] = vector
            
    async def query(self, vector: List[float], namespace: str, top_k: int = 5) -> Dict:
        """Mock vector query."""
        return {
            "matches": [
                {
                    "id": "test-id",
                    "score": 0.95,
                    "metadata": {
                        "document_id": "test-doc",
                        "chunk_id": 1,
                        "text": "Test chunk content"
                    }
                }
            ]
        }

class MockDocumentExtractor:
    """Mock implementation of document extractor."""
    
    def extract_text(self, file_path: str) -> str:
        """Mock text extraction."""
        return "This is mock extracted text for testing."
    
    def get_page_count(self, file_path: str) -> int:
        """Mock page count."""
        return 2  # Return consistent page count for testing