"""
Google Gemini LLM provider implementation.
"""

import logging
from typing import Optional

import google.generativeai as genai

from app.config import settings
from app.services.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class GoogleProvider(LLMProvider):
    """Google Gemini provider for text generation."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048
    ):
        """
        Initialize Google Gemini provider.
        
        Args:
            api_key: Google API key (uses settings if not provided)
            model: Model name (uses settings if not provided)
            temperature: Default temperature
            max_tokens: Default max tokens
        """
        self.api_key = api_key or settings.google_api_key
        self.model_name = model or settings.google_model
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens
        
        if not self.api_key:
            raise ValueError(
                "Google API key is required. Set GOOGLE_API_KEY environment variable. "
                "Get your key at: https://aistudio.google.com/app/apikey"
            )
        
        # Configure genai
        genai.configure(api_key=self.api_key)
        
        # Remove 'models/' prefix if present for GenerativeModel
        model_name_for_api = self.model_name.replace('models/', '') if self.model_name.startswith('models/') else self.model_name
        
        # Initialize the model (don't generate content yet!)
        self.model = genai.GenerativeModel(model_name_for_api)
        
        logger.info(f"Initialized Google Gemini provider: model={self.model_name} (API: {model_name_for_api})")
    
    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text response using Google Gemini.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        temp = temperature if temperature is not None else self.default_temperature
        tokens = max_tokens if max_tokens is not None else self.default_max_tokens
        
        try:
            logger.debug(f"Generating response with Gemini (temp={temp}, max_tokens={tokens})")
            
            generation_config = genai.GenerationConfig(
                temperature=temp,
                max_output_tokens=tokens
            )
            
            # Set safety settings to be less restrictive for technical content
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Check if response was blocked
            if not response.candidates:
                logger.error("Response was blocked - no candidates returned")
                raise ValueError("Response was blocked by safety filters")
            
            # Check finish reason
            finish_reason = response.candidates[0].finish_reason
            if finish_reason != 1:  # 1 = STOP (normal completion)
                logger.warning(f"Response finished with reason: {finish_reason}")
                # Try to get partial text if available
                if response.candidates[0].content.parts:
                    generated_text = response.candidates[0].content.parts[0].text
                    logger.info(f"Retrieved partial response ({len(generated_text)} chars)")
                    return generated_text
                else:
                    raise ValueError(f"Response blocked with finish_reason: {finish_reason}")
            
            generated_text = response.text
            
            logger.debug(f"Generated {len(generated_text)} characters")
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating with Google Gemini: {e}")
            raise
    
    def get_model_name(self) -> str:
        """Get the model name."""
        return self.model_name