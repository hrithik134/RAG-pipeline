"""OpenAI LLM service provider."""

import logging
from typing import Any, Dict, List, Optional, Union

from openai import AsyncOpenAI

from app.config import settings
from app.services.llm.base import BaseLLMService, LLMResponse
from app.services.types import PromptTemplate

logger = logging.getLogger(__name__)


class OpenAILLMService(BaseLLMService):
    """OpenAI language model service."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048
    ):
        """Initialize OpenAI connection."""
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens
        self.initialized = False
        self.client = None
        
    async def initialize(self) -> None:
        """Initialize the service if needed."""
        if not self.initialized:
            if not self.api_key:
                raise ValueError(
                    "OpenAI API key is required. Set OPENAI_API_KEY environment variable."
                )
            self.client = AsyncOpenAI(api_key=self.api_key)
            self.initialized = True
            logger.info(f"Initialized OpenAI provider: model={self.model}")
            
    async def generate(
        self,
        prompt: Union[str, PromptTemplate],
        **kwargs: Any
    ) -> LLMResponse:
        """Generate text completion using OpenAI."""
        if not self.initialized:
            await self.initialize()
            
        # Convert template to string if needed
        if isinstance(prompt, PromptTemplate):
            prompt = prompt.format(**kwargs)
            
        # Get parameters
        temp = kwargs.get('temperature', self.default_temperature)
        tokens = kwargs.get('max_tokens', self.default_max_tokens)
        
        try:
            logger.debug(f"Generating response with OpenAI (temp={temp}, max_tokens={tokens})")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temp,
                max_tokens=tokens
            )
            
            return LLMResponse(
                text=response.choices[0].message.content,
                tokens_used=response.usage.total_tokens,
                model=response.model
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise RuntimeError(f"OpenAI API error: {str(e)}")
            
    async def generate_with_metadata(
        self,
        prompt: Union[str, PromptTemplate],
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """Generate text completion with metadata."""
        response = await self.generate(prompt, **kwargs)
        response.metadata = metadata or {}
        return response
        
    async def process_batch(
        self,
        prompts: List[Union[str, PromptTemplate]],
        **kwargs: Any
    ) -> List[LLMResponse]:
        """Process a batch of prompts."""
        responses = []
        for prompt in prompts:
            response = await self.generate(prompt, **kwargs)
            responses.append(response)
        return responses

