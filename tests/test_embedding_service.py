"""Unit tests for embedding service interfaces."""

import pytest
from typing import List

from app.services.embeddings.base import EmbeddingProvider
from app.services.types import EmbeddingResponse
from tests.mocks import MockEmbeddingService


class TestEmbeddingInterface:
    """Test suite for embedding service interface."""

    def test_encode_single(self, mock_embedding_service):
        """Test encoding single text."""
        text = "This is a test document."
        result = pytest.helpers.await_sync(
            mock_embedding_service.encode_batch([text])
        )
        
        assert isinstance(result, dict)
        assert "embeddings" in result
        assert len(result["embeddings"]) == 1
        assert len(result["embeddings"][0]) == 1536  # Standard embedding size

    def test_encode_batch(self, mock_embedding_service):
        """Test encoding multiple texts."""
        texts = [
            "First test document.",
            "Second test document.",
            "Third test document."
        ]
        result = pytest.helpers.await_sync(
            mock_embedding_service.encode_batch(texts)
        )
        
        assert isinstance(result, dict)
        assert len(result["embeddings"]) == len(texts)
        assert all(len(emb) == 1536 for emb in result["embeddings"])

    def test_embedding_metadata(self, mock_embedding_service):
        """Test embedding result metadata."""
        text = "Test document."
        result = pytest.helpers.await_sync(
            mock_embedding_service.encode_batch([text])
        )
        
        assert "model" in result
        assert "total_tokens" in result
        assert isinstance(result["total_tokens"], int)

    def test_batch_size_limit(self, mock_embedding_service):
        """Test handling of large batches."""
        # Create a batch larger than typical limits
        texts = ["Test document."] * 100
        result = pytest.helpers.await_sync(
            mock_embedding_service.encode_batch(texts, batch_size=20)
        )
        
        assert len(result["embeddings"]) == len(texts)

    def test_error_handling(self, mock_embedding_service):
        """Test error handling for invalid inputs."""
        with pytest.raises(ValueError):
            pytest.helpers.await_sync(
                mock_embedding_service.encode_batch([])
            )

        with pytest.raises(ValueError):
            pytest.helpers.await_sync(
                mock_embedding_service.encode_batch([None])
            )

    @pytest.mark.parametrize("text,expected_tokens", [
        ("Short text.", 2),
        ("This is a longer piece of text for testing.", 10),
        ("", 0)
    ])
    def test_token_counting(self, mock_embedding_service, text, expected_tokens):
        """Test token counting for different texts."""
        result = pytest.helpers.await_sync(
            mock_embedding_service.encode_batch([text])
        )
        
        # Simple word-based token count in mock
        assert result["total_tokens"] == len(text.split()) if text else 0