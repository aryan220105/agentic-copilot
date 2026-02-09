"""
LLM Provider Factory

Creates the appropriate LLM provider based on configuration.
"""
from typing import Optional
from app.llm.provider import LLMProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.groq_provider import GroqLLMProvider
from app.config import settings


_provider_instance: Optional[LLMProvider] = None


def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider (singleton)."""
    global _provider_instance
    
    if _provider_instance is None:
        if settings.LLM_MODE == "groq":
            _provider_instance = GroqLLMProvider()
        else:
            _provider_instance = MockLLMProvider()
    
    return _provider_instance


def reset_provider():
    """Reset the provider instance (for testing)."""
    global _provider_instance
    _provider_instance = None


__all__ = [
    "LLMProvider",
    "MockLLMProvider", 
    "GroqLLMProvider",
    "get_llm_provider",
    "reset_provider"
]
