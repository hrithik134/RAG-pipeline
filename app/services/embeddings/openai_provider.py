"""
OpenAI embedding provider implementation.

Uses OpenAI's text-embedding-3-large or text-embedding-3-small models
with automatic batching, retries, and error handling.
"""

import asyncio
import logging
from typing import List, Optional

from openai import AsyncOpenAI, RateLimitError, APIError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.config import settings
from app.services.embeddings.base import EmbeddingProvider, EmbeddingResponse

logger = logging.getLogger(__name__)


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    OpenAI embedding provider using text-embedding-3-* models.
    
    Features:
    - Automatic batching for efficient API usage
    - Exponential backoff retry on rate limits and transient errors
    - Token counting and cost tracking
    - Support for both text-embedding-3-large (3072D) and -small (1536D)
    """
    
    # Model dimensions for reference
    MODEL_DIMENSIONS = {
        "text-embedding-3-large": 3072,
        "text-embedding-3-small": 1536,
        "text-embedding-ada-002": 1536,
    }
    
    # Max tokens per input
    MAX_INPUT_TOKENS = 8191
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        batch_size: int = 64,
        max_retries: int = 5,
        retry_delay: float = 1.0,
    ):
        """
        Initialize OpenAI embedding provider.
        
        Args:
            api_key: OpenAI API key (defaults to settings)
            model: Model name (defaults to settings)
            batch_size: Batch size for API calls
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay in seconds
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_embedding_model
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        if self.model not in self.MODEL_DIMENSIONS:
            logger.warning(
                f"Unknown model {self.model}. Supported models: {list(self.MODEL_DIMENSIONS.keys())}"
            )
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        logger.info(
            f"Initialized OpenAI embedding provider: model={self.model}, "
            f"dimension={self.dimension()}, batch_size={self.batch_size}"
        )
    
    def dimension(self) -> int:
        """Get embedding dimension for the configured model."""
        return self.MODEL_DIMENSIONS.get(self.model, 1536)
    
    def model_name(self) -> str:
        """Get the model name."""
        return self.model
    
    def max_input_length(self) -> int:
        """Get maximum input length in tokens."""
        return self.MAX_INPUT_TOKENS
    
    @retry(
        retry=retry_if_exception_type((RateLimitError, APIError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a single batch of texts with retry logic.
        
        Args:
            texts: List of texts to embed (pre-batched)
            
        Returns:
            List of embedding vectors
            
        Raises:
            RateLimitError: If rate limit exceeded after retries
            APIError: If API error occurs after retries
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts,
                encoding_format="float"
            )
            
            # Extract embeddings in order
            embeddings = [item.embedding for item in response.data]
            
            return embeddings
            
        except RateLimitError as e:
            logger.warning(f"Rate limit hit, will retry: {e}")
            raise
        except APIError as e:
            if e.status_code and e.status_code >= 500:
                logger.warning(f"Server error {e.status_code}, will retry: {e}")
                raise
            else:
                logger.error(f"API error (non-retryable): {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error in embedding: {e}")
            raise
    
    async def embed_texts(
        self,
        texts: List[str],
        batch_size: Optional[int] = None
    ) -> EmbeddingResponse:
        """
        Generate embeddings for a list of texts with automatic batching.
        
        Args:
            texts: List of text strings to embed
            batch_size: Optional batch size override
            
        Returns:
            EmbeddingResult with embeddings and metadata
            
        Raises:
            ValueError: If texts list is empty
            Exception: If embedding generation fails
        """
        if not texts:
            raise ValueError("Cannot embed empty text list")
        
        effective_batch_size = batch_size or self.batch_size
        
        # Truncate texts if needed
        truncated_texts = [
            self.truncate_text(text, self.MAX_INPUT_TOKENS)
            for text in texts
        ]
        
        # Count total tokens for logging
        total_tokens = sum(self.count_tokens(text) for text in truncated_texts)
        
        logger.info(
            f"Embedding {len(texts)} texts ({total_tokens} tokens) "
            f"in batches of {effective_batch_size}"
        )
        
        # Split into batches
        batches = [
            truncated_texts[i:i + effective_batch_size]
            for i in range(0, len(truncated_texts), effective_batch_size)
        ]
        
        # Process batches with controlled concurrency
        all_embeddings = []
        
        for i, batch in enumerate(batches):
            logger.debug(f"Processing batch {i+1}/{len(batches)} ({len(batch)} texts)")
            
            batch_embeddings = await self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings)
            
            # Small delay between batches to avoid rate limits
            if i < len(batches) - 1:
                await asyncio.sleep(0.1)
        
        logger.info(
            f"Successfully embedded {len(all_embeddings)} texts "
            f"({total_tokens} tokens)"
        )
        
        return EmbeddingResponse(
            embeddings=all_embeddings,
            model=self.model,
            total_tokens=total_tokens
        )

