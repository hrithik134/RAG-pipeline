"""
Unit tests for embedding providers.

Tests the embedding provider interface, OpenAI provider implementation,
and helper utilities.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.embeddings.base import EmbeddingProvider, EmbeddingResponse
from app.services.embeddings.openai_provider import OpenAIEmbeddingProvider


class TestEmbeddingProviderBase:
    """Test base embedding provider utilities."""
    
    def test_truncate_text(self):
        """Test text truncation to token limit."""
        provider = OpenAIEmbeddingProvider(api_key="test-key")
        
        # Short text should not be truncated
        short_text = "Hello world"
        result = provider.truncate_text(short_text, max_tokens=100)
        assert result == short_text
        
        # Long text should be truncated
        long_text = "word " * 10000  # Very long text
        result = provider.truncate_text(long_text, max_tokens=100)
        assert len(result) < len(long_text)
    
    def test_count_tokens(self):
        """Test token counting."""
        provider = OpenAIEmbeddingProvider(api_key="test-key")
        
        text = "Hello world, this is a test."
        token_count = provider.count_tokens(text)
        
        assert isinstance(token_count, int)
        assert token_count > 0
        assert token_count < len(text)  # Tokens should be fewer than characters
    
    def test_validate_dimension_match(self):
        """Test dimension validation passes when dimensions match."""
        provider = OpenAIEmbeddingProvider(api_key="test-key", model="text-embedding-3-large")
        
        # Should not raise for matching dimension
        provider.validate_dimension(3072)
    
    def test_validate_dimension_mismatch(self):
        """Test dimension validation fails when dimensions don't match."""
        provider = OpenAIEmbeddingProvider(api_key="test-key", model="text-embedding-3-large")
        
        # Should raise for mismatched dimension
        with pytest.raises(ValueError, match="Dimension mismatch"):
            provider.validate_dimension(1536)


class TestOpenAIEmbeddingProvider:
    """Test OpenAI embedding provider."""
    
    def test_initialization(self):
        """Test provider initialization."""
        provider = OpenAIEmbeddingProvider(
            api_key="test-key",
            model="text-embedding-3-large",
            batch_size=32
        )
        
        assert provider.api_key == "test-key"
        assert provider.model == "text-embedding-3-large"
        assert provider.batch_size == 32
        assert provider.dimension() == 3072
        assert provider.model_name() == "text-embedding-3-large"
        assert provider.max_input_length() == 8191
    
    def test_initialization_no_api_key(self):
        """Test initialization fails without API key."""
        with patch("app.services.embeddings.openai_provider.settings") as mock_settings:
            mock_settings.openai_api_key = ""
            
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                OpenAIEmbeddingProvider()
    
    def test_model_dimensions(self):
        """Test dimension mapping for different models."""
        # text-embedding-3-large
        provider_large = OpenAIEmbeddingProvider(
            api_key="test-key",
            model="text-embedding-3-large"
        )
        assert provider_large.dimension() == 3072
        
        # text-embedding-3-small
        provider_small = OpenAIEmbeddingProvider(
            api_key="test-key",
            model="text-embedding-3-small"
        )
        assert provider_small.dimension() == 1536
        
        # text-embedding-ada-002
        provider_ada = OpenAIEmbeddingProvider(
            api_key="test-key",
            model="text-embedding-ada-002"
        )
        assert provider_ada.dimension() == 1536
    
    @pytest.mark.asyncio
    async def test_embed_texts_success(self):
        """Test successful embedding generation."""
        provider = OpenAIEmbeddingProvider(api_key="test-key", batch_size=2)
        
        # Mock the OpenAI client
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1] * 3072),
            MagicMock(embedding=[0.2] * 3072),
            MagicMock(embedding=[0.3] * 3072),
        ]
        
        with patch.object(provider.client.embeddings, "create", new=AsyncMock(return_value=mock_response)):
            texts = ["text1", "text2", "text3"]
            result = await provider.embed_texts(texts)
            
            assert isinstance(result, EmbeddingResult)
            assert len(result.embeddings) == 3
            assert result.model == "text-embedding-3-large"
            assert result.dimension == 3072
            assert result.total_tokens > 0
            
            # Check embedding values
            assert result.embeddings[0] == [0.1] * 3072
            assert result.embeddings[1] == [0.2] * 3072
            assert result.embeddings[2] == [0.3] * 3072
    
    @pytest.mark.asyncio
    async def test_embed_texts_empty_list(self):
        """Test embedding with empty text list raises error."""
        provider = OpenAIEmbeddingProvider(api_key="test-key")
        
        with pytest.raises(ValueError, match="Cannot embed empty text list"):
            await provider.embed_texts([])
    
    @pytest.mark.asyncio
    async def test_embed_texts_batching(self):
        """Test that texts are batched correctly."""
        provider = OpenAIEmbeddingProvider(api_key="test-key", batch_size=2)
        
        # Mock the OpenAI client to track batch sizes
        call_count = 0
        batch_sizes = []
        
        async def mock_create(model, input, encoding_format):
            nonlocal call_count, batch_sizes
            call_count += 1
            batch_sizes.append(len(input))
            
            # Return mock embeddings
            return MagicMock(
                data=[MagicMock(embedding=[0.1] * 3072) for _ in input]
            )
        
        with patch.object(provider.client.embeddings, "create", new=mock_create):
            texts = ["text1", "text2", "text3", "text4", "text5"]
            result = await provider.embed_texts(texts)
            
            # Should make 3 calls: [2, 2, 1]
            assert call_count == 3
            assert batch_sizes == [2, 2, 1]
            assert len(result.embeddings) == 5
    
    @pytest.mark.asyncio
    async def test_embed_texts_truncation(self):
        """Test that long texts are truncated."""
        provider = OpenAIEmbeddingProvider(api_key="test-key")
        
        # Create a very long text
        long_text = "word " * 10000
        
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 3072)]
        
        with patch.object(provider.client.embeddings, "create", new=AsyncMock(return_value=mock_response)) as mock_create:
            result = await provider.embed_texts([long_text])
            
            # Check that the text passed to API was truncated
            call_args = mock_create.call_args
            input_text = call_args.kwargs["input"][0]
            assert len(input_text) < len(long_text)


class TestEmbeddingResponse:
    """Test EmbeddingResponse dataclass."""
    
    def test_embedding_response_creation(self):
        """Test creating an EmbeddingResponse."""
        result = EmbeddingResponse(
            embeddings=[[0.1, 0.2], [0.3, 0.4]],
            model="test-model",
            total_tokens=100,
            dimension=2
        )
        
        assert len(result.embeddings) == 2
        assert result.model == "test-model"
        assert result.total_tokens == 100
        assert result.dimension == 2

