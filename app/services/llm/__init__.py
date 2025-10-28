"""LLM service providers for RAG generation."""

from .base import BaseLLMService
from .gemini_provider import GeminiLLMService
from app.config import settings


def create_llm_service() -> BaseLLMService:
    """Factory function to create an LLM service."""
    return GeminiLLMService()


def get_llm_service() -> BaseLLMService:
    """Get a singleton instance of the configured LLM service."""
    if not hasattr(get_llm_service, "_instance"):
        get_llm_service._instance = create_llm_service()
    return get_llm_service._instance


# For backwards compatibility
factory = create_llm_service