"""Google embedding service provider."""

import logging
from typing import List, Optional

import google.generativeai as genai

from app.config import settings
from app.services.embeddings.base import EmbeddingProvider, EmbeddingResponse

logger = logging.getLogger(__name__)


class GoogleEmbeddingProvider(EmbeddingProvider):
    """Google embeddings provider."""
    
    def __init__(self):
        """Initialize Google embeddings."""
        self.api_key = settings.google_api_key
        self.model = settings.google_embedding_model
        self.initialized = False
        
    async def initialize(self) -> None:
        """Initialize if needed."""
        if not self.initialized:
            if not self.api_key:
                raise ValueError(
                    "Google API key required. Set GOOGLE_API_KEY env variable."
                )
            genai.configure(api_key=self.api_key)
            self.initialized = True
            logger.info(f"Initialized Google embeddings: model={self.model}")
    
    async def embed_texts(
        self,
        texts: List[str],
        batch_size: Optional[int] = None
    ) -> EmbeddingResponse:
        """Generate embeddings for texts."""
        if not self.initialized:
            await self.initialize()
            
        try:
            # Handle batching
            if batch_size:
                batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
            else:
                batches = [texts]
                
            all_embeddings = []
            total_tokens = 0
            
            # Process each batch
            for batch in batches:
                embeddings = []
                for text in batch:
                    # Generate embedding using Google's API
                    response = await genai.embed_content_async(
                        text,
                        model=self.model,
                        task_type="retrieval_document"
                    )
                    embeddings.append(response.embedding)
                    total_tokens += len(text.split())  # Approximate
                    
                all_embeddings.extend(embeddings)
            
            return EmbeddingResponse(
                embeddings=all_embeddings,
                model=self.model,
                total_tokens=total_tokens
            )
            
        except Exception as e:
            logger.error(f"Google embedding error: {str(e)}")
            raise RuntimeError(f"Google embedding error: {str(e)}")