"""
Groq LLM Provider

Real API integration with Groq for production use.
Includes retry with exponential backoff and timeout protection.
"""
import httpx
import time
import json
from typing import Optional
from app.llm.provider import LLMProvider
from app.config import settings


class GroqLLMProvider(LLMProvider):
    """Groq API LLM provider."""
    
    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self.max_retries = 3
        self.timeout = 30.0
        
    def get_name(self) -> str:
        return "groq"
    
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """Generate response using Groq API with retry logic."""
        print(f"[LLM] Groq generating (prompt length: {len(prompt)})")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not configured")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        self.BASE_URL,
                        headers=headers,
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return data["choices"][0]["message"]["content"]
                    elif response.status_code == 429:
                        # Rate limited - exponential backoff
                        wait_time = (2 ** attempt) + 1
                        time.sleep(wait_time)
                        continue
                    else:
                        response.raise_for_status()
                        
            except httpx.TimeoutException as e:
                last_error = f"Timeout after {self.timeout}s"
                wait_time = (2 ** attempt) + 1
                time.sleep(wait_time)
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP error: {e.response.status_code}"
                if e.response.status_code >= 500:
                    wait_time = (2 ** attempt) + 1
                    time.sleep(wait_time)
                else:
                    raise
            except Exception as e:
                last_error = str(e)
                raise
        
        raise RuntimeError(f"Failed after {self.max_retries} retries: {last_error}")
    
    def generate_with_log(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        agent_name: str = "unknown"
    ) -> tuple[str, dict]:
        """Generate and return response with metadata for logging."""
        start_time = time.time()
        
        response = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        metadata = {
            "agent_name": agent_name,
            "model": self.model,
            "latency_ms": latency_ms,
            "prompt_length": len(prompt),
            "response_length": len(response)
        }
        
        return response, metadata
