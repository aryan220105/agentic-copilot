"""
LLM Provider System

Provides a pluggable interface for LLM integration with:
- MockLLMProvider: Deterministic template-based responses
- GroqLLMProvider: Real API integration with Groq
"""
from abc import ABC, abstractmethod
from typing import Optional
import time
import json


class LLMProvider(ABC):
    """Base interface for LLM providers."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """Generate a response from the LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: System instructions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the provider name."""
        pass
