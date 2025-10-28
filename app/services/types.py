"""Common type definitions for the application."""

from typing import Dict, List, Any, Union


class PromptTemplate:
    """Template for LLM prompts."""
    
    def __init__(self, template: str):
        self.template = template
        
    def format(self, **kwargs: Any) -> str:
        """Format template with provided values."""
        return self.template.format(**kwargs)
        
    def __str__(self) -> str:
        return self.template


class EmbeddingResponse:
    """Response from embedding operation."""
    
    def __init__(
        self,
        embeddings: List[List[float]],
        model: str,
        total_tokens: int
    ):
        self.embeddings = embeddings
        self.model = model
        self.total_tokens = total_tokens