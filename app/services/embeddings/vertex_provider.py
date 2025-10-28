"""
Google AI (Vertex) embedding provider implementation.

Uses Google's text-embedding-004 model for generating embeddings.
"""

import logging
from typing import List, Optional

import google.generativeai as genai

from app.config import settings
from app.services.embeddings.base import EmbeddingProvider, EmbeddingResponse

logger = logging.getLogger(__name__)


class VertexEmbeddingProvider(EmbeddingProvider):
    """
    Google AI embedding provider using text-embedding-004 model.
    
    Features:
    - 768-dimensional embeddings
    - Batch processing
    - Automatic text truncation
    """
    
    MODEL_DIMENSIONS = {
        "models/text-embedding-004": 768,
        "models/embedding-001": 768,
    }
    
    MAX_INPUT_TOKENS = 2048
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "models/text-embedding-004",
        batch_size: int = 64,
    ):
        """
        Initialize Google AI embedding provider.
        
        Args:
            api_key: Google API key (defaults to settings)
            model: Model name
            batch_size: Batch size for API calls
        """
        self.api_key = api_key or settings.google_api_key
        self.model = model
        self.batch_size = batch_size
        
        if not self.api_key:
            raise ValueError(
                "Google API key is required. Set GOOGLE_API_KEY environment variable. "
                "Get your key at: https://aistudio.google.com/app/apikey"
            )
        
        # Configure Google AI
        genai.configure(api_key=self.api_key)
        
        logger.info(
            f"Initialized Google AI embedding provider: model={self.model}, "
            f"dimension={self.dimension()}, batch_size={self.batch_size}"
        )
    
    def dimension(self) -> int:
        """Get embedding dimension for the configured model."""
        return self.MODEL_DIMENSIONS.get(self.model, 768)
    
    def model_name(self) -> str:
        """Get the model name."""
        return self.model
    
    def max_input_length(self) -> int:
        """Get maximum input length in tokens."""
        return self.MAX_INPUT_TOKENS
    
    async def embed_texts(
        self,
        texts: List[str],
        batch_size: Optional[int] = None
    ) -> EmbeddingResponse:
        """
        Generate embeddings for a list of texts.
        
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
            f"with Google AI"
        )
        
        # Generate embeddings
        all_embeddings = []
        
        try:
            for i, text in enumerate(truncated_texts):
                logger.debug(f"Embedding text {i+1}/{len(truncated_texts)}")
                
                result = genai.embed_content(
                    model=self.model,
                    content=text,
                    task_type="retrieval_document"
                )
                
                all_embeddings.append(result['embedding'])
            
            logger.info(
                f"Successfully embedded {len(all_embeddings)} texts "
                f"({total_tokens} tokens)"
            )
            
            return EmbeddingResponse(
                embeddings=all_embeddings,
                model=self.model,
                total_tokens=total_tokens
            )
            
        except Exception as e:
            logger.error(f"Error generating embeddings with Google AI: {e}")
            raise