"""Google Gemini embedding service provider."""

import logging
from typing import Dict, List

import google.generativeai as genai

from app.config import settings
from app.services.embeddings.base import EmbeddingProvider, EmbeddingResponse

logger = logging.getLogger(__name__)


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Gemini embeddings provider."""
    
    def __init__(self):
        """Initialize Gemini embeddings."""
        self.api_key = settings.google_api_key
        self.model = settings.gemini_embedding_model  # e.g. "embedding-001"
        self.initialized = False
        
    async def initialize(self) -> None:
        """Initialize if needed."""
        if not self.initialized:
            if not self.api_key:
                raise ValueError(
                    "Google API key required. Set GOOGLE_API_KEY env variable."
                )
            genai.configure(api_key=self.api_key)
            self.model_client = genai.GenerativeModel(self.model)
            self.initialized = True
            logger.info(f"Initialized Gemini embeddings: model={self.model}")
    
    async def encode_batch(self, texts: List[str], **kwargs) -> Dict:
        """Generate embeddings for batch of texts."""
        if not self.initialized:
            await self.initialize()
            
        try:
            # Generate embeddings using Gemini
            response = await self.model_client.embed_content_async(
                texts,
                task_type="retrieval_document" 
            )
            
            return EmbeddingResponse(
                embeddings=response.embedding,
                model=self.model,
                total_tokens=sum(len(text.split()) for text in texts)  # Approximation
            )
            
        except Exception as e:
            logger.error(f"Gemini embedding error: {str(e)}")
            raise RuntimeError(f"Gemini embedding error: {str(e)}")