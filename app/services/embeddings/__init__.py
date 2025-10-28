"""
Embedding providers for generating vector embeddings from text.

This package provides a pluggable interface for different embedding providers
(OpenAI, Vertex AI, etc.) with automatic batching, retries, and error handling.
"""

from typing import Optional

from app.services.embeddings.base import EmbeddingProvider, EmbeddingResponse
from app.services.embeddings.gemini_provider import GeminiEmbeddingProvider
from app.config import settings

__all__ = [
    "EmbeddingProvider",
    "EmbeddingResponse",
    "GeminiEmbeddingProvider",
    "factory",
    "get_embedding_service",
]


def create_embedding_service() -> EmbeddingProvider:
    """Create embedding service instance."""
    return GeminiEmbeddingProvider()


# Cache instance
_instance: Optional[EmbeddingProvider] = None


def get_embedding_service() -> EmbeddingProvider:
    """Get singleton embedding service instance."""
    global _instance
    if _instance is None:
        _instance = create_embedding_service()
    return _instance


# For backwards compatibility
factory = create_embedding_service
