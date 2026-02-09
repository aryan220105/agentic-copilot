"""Backend application configuration."""
from pydantic_settings import BaseSettings
from typing import Literal
import os


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # LLM Configuration
    LLM_MODE: Literal["mock", "groq"] = "mock"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-70b-versatile"
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/copilot.db"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # Sandbox
    SANDBOX_TIMEOUT: int = 2
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
