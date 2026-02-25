"""
Application Configuration
All secrets must be set via environment variables or .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    # Database - MUST be set via env var or .env
    DATABASE_URL: str = ""

    # Supabase Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None

    # AI Configuration
    AI_PROVIDER: str = "deepseek"  # gemini, deepseek, or anthropic
    GOOGLE_GEMINI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # AI Model Settings
    GEMINI_MODEL: str = "gemini-1.5-flash"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"

    # AI Conversation Mode
    AI_CONVERSATION_MODE: str = "unified"

    # Application
    DEBUG: bool = False
    SECRET_KEY: str = ""
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:5174"

    # JWT Authentication
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    @model_validator(mode='after')
    def load_deepseek_key_fallback(self):
        """Handle case-insensitive env variable for DeepSeek"""
        if not self.DEEPSEEK_API_KEY:
            self.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_api_key")
        return self

    @model_validator(mode='after')
    def validate_required_secrets(self):
        """Ensure critical secrets are set when not in debug mode"""
        if not self.DEBUG:
            missing = []
            if not self.DATABASE_URL:
                missing.append("DATABASE_URL")
            if not self.SECRET_KEY:
                missing.append("SECRET_KEY")
            if not self.JWT_SECRET_KEY:
                missing.append("JWT_SECRET_KEY")
            if missing:
                raise ValueError(
                    f"Missing required env vars for production: {', '.join(missing)}"
                )
        return self

    class Config:
        env_file = Path(__file__).parent.parent.parent.parent / ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()
