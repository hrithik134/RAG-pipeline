"""Google Gemini LLM service provider."""

import logging
from typing import Any, Dict, List, Optional, Union

import google.generativeai as genai

from app.config import settings
from app.services.llm.base import BaseLLMService, LLMResponse
from app.services.types import PromptTemplate

logger = logging.getLogger(__name__)


class GeminiLLMService(BaseLLMService):
    """Google Gemini language model service."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048
    ):
        """Initialize Gemini connection."""
        self.api_key = api_key or settings.google_api_key
        self.model = model or settings.google_model  # e.g. "gemini-2.5-pro"
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens
        self.initialized = False
        self.client = None
        
    async def initialize(self) -> None:
        """Initialize the service if needed."""
        if not self.initialized:
            if not self.api_key:
                raise ValueError(
                    "Google API key is required. Set GOOGLE_API_KEY environment variable."
                )
            genai.configure(api_key=self.api_key)
            self.model_client = genai.GenerativeModel(self.model)
            self.initialized = True
            logger.info(f"Initialized Gemini provider: model={self.model}")
            
    async def generate(
        self,
        prompt: Union[str, PromptTemplate],
        **kwargs: Any
    ) -> LLMResponse:
        """Generate text completion using Gemini."""
        if not self.initialized:
            await self.initialize()
            
        # Convert template to string if needed
        if isinstance(prompt, PromptTemplate):
            prompt = prompt.format(**kwargs)
            
        # Get parameters
        temp = kwargs.get('temperature', self.default_temperature)
        tokens = kwargs.get('max_tokens', self.default_max_tokens)
        
        try:
            logger.debug(f"Generating response with Gemini (temp={temp}, max_tokens={tokens})")
            
            response = await self.model_client.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temp,
                    max_output_tokens=tokens,
                )
            )
            
            return LLMResponse(
                text=response.text,
                tokens_used=len(response.text.split()),  # Approximation since Gemini doesn't return token count
                model=self.model
            )
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise RuntimeError(f"Gemini API error: {str(e)}")
            
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
    
    def get_model_name(self) -> str:
        """Get the model name."""
        return self.model