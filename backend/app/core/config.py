"""
Application Configuration
"""

from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    # Database (Supabase PostgreSQL via Connection Pooler)
    DATABASE_URL: str = "postgresql://postgres.vpmsytbbsxmtdicnkytv:%21%40kHanh0112@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

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
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"  # claude-sonnet-4, claude-opus-4-5

    # AI Conversation Mode
    # "classic" = Rule-based detection + separate prompts (old approach)
    # "unified" = Single AI-driven conversational prompt (new approach)
    AI_CONVERSATION_MODE: str = "unified"

    # Application
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-here-change-in-production"

    # JWT Authentication
    JWT_SECRET_KEY: str = "5p-slms-jwt-secret-key-change-in-production-2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    @model_validator(mode='after')
    def load_deepseek_key_fallback(self):
        """Handle case-insensitive env variable for DeepSeek"""
        if not self.DEEPSEEK_API_KEY:
            self.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_api_key")
        return self

    class Config:
        # Load .env from parent directory (project root)
        env_file = Path(__file__).parent.parent.parent.parent / ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()
