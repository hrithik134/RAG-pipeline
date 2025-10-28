"""Base interfaces for LLM services."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from app.services.types import PromptTemplate


class LLMResponse:
    """Response from LLM service."""
    
    def __init__(
        self,
        text: str,
        tokens_used: int,
        model: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.text = text
        self.tokens_used = tokens_used
        self.model = model
        self.metadata = metadata or {}


class BaseLLMService(ABC):
    """Base class for LLM service implementations."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service."""
        pass
    
    @abstractmethod
    async def generate(
        self,
        prompt: Union[str, PromptTemplate],
        **kwargs: Any
    ) -> LLMResponse:
        """Generate text completion."""
        pass
    
    @abstractmethod
    async def generate_with_metadata(
        self,
        prompt: Union[str, PromptTemplate],
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """Generate text completion with metadata."""
        pass
    
    @abstractmethod
    async def process_batch(
        self,
        prompts: List[Union[str, PromptTemplate]],
        **kwargs: Any
    ) -> List[LLMResponse]:
        """Process a batch of prompts."""
        pass


# Alias for backward compatibility
LLMProvider = BaseLLMService
