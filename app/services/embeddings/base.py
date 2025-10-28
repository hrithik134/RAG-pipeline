"""
Base interface for embedding providers.

Defines the contract that all embedding providers must implement,
along with helper utilities for text truncation and token counting.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

import tiktoken


@dataclass
class EmbeddingResponse:
    """Response from embedding operation."""
    embeddings: List[List[float]]
    model: str
    total_tokens: int


class EmbeddingProvider(ABC):
    """
    Abstract base class for embedding providers.
    
    All embedding providers must implement this interface to ensure
    consistent behavior across different providers (OpenAI, Vertex, etc.).
    """
    
    @abstractmethod
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
            EmbeddingResponse with embeddings and metadata
            
        Raises:
            Exception: If embedding generation fails
        """
        pass
    
    @abstractmethod
    def dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this provider.
        
        Returns:
            Integer dimension (e.g., 1536, 3072)
        """
        pass
    
    @abstractmethod
    def model_name(self) -> str:
        """
        Get the model name used by this provider.
        
        Returns:
            Model name string
        """
        pass
    
    @abstractmethod
    def max_input_length(self) -> int:
        """
        Get the maximum input length (in tokens) for this provider.
        
        Returns:
            Maximum tokens per input
        """
        pass
    
    def truncate_text(
        self,
        text: str,
        max_tokens: Optional[int] = None,
        encoding_name: str = "cl100k_base"
    ) -> str:
        """
        Truncate text to fit within token limit.
        
        Args:
            text: Text to truncate
            max_tokens: Maximum tokens (defaults to provider's max)
            encoding_name: Tokenizer encoding to use
            
        Returns:
            Truncated text
        """
        if max_tokens is None:
            max_tokens = self.max_input_length()
        
        try:
            encoding = tiktoken.get_encoding(encoding_name)
            tokens = encoding.encode(text)
            
            if len(tokens) <= max_tokens:
                return text
            
            # Truncate and decode
            truncated_tokens = tokens[:max_tokens]
            return encoding.decode(truncated_tokens)
            
        except Exception:
            # Fallback to character-based truncation (rough estimate: 4 chars per token)
            max_chars = max_tokens * 4
            return text[:max_chars]
    
    def count_tokens(
        self,
        text: str,
        encoding_name: str = "cl100k_base"
    ) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count
            encoding_name: Tokenizer encoding to use
            
        Returns:
            Token count
        """
        try:
            encoding = tiktoken.get_encoding(encoding_name)
            return len(encoding.encode(text))
        except Exception:
            # Fallback to rough estimate
            return len(text) // 4
    
    def validate_dimension(self, expected_dim: int) -> None:
        """
        Validate that provider dimension matches expected dimension.
        
        Args:
            expected_dim: Expected dimension
            
        Raises:
            ValueError: If dimensions don't match
        """
        actual_dim = self.dimension()
        if actual_dim != expected_dim:
            raise ValueError(
                f"Dimension mismatch: provider produces {actual_dim}D embeddings "
                f"but index expects {expected_dim}D. "
                f"Please update PINECONE_DIMENSION={actual_dim} or change embedding model."
            )

