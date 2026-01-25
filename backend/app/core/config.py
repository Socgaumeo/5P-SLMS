"""
Application Configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    # Database (Supabase PostgreSQL)
    DATABASE_URL: str = "postgresql://postgres:%5B%21%40kHanh0112%5D@db.vpmsytbbsxmtdicnkytv.supabase.co:5432/postgres"

    # Supabase Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None

    # AI Configuration
    AI_PROVIDER: str = "gemini"  # gemini or deepseek
    GOOGLE_GEMINI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None

    # AI Model Settings
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # Application
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    
    class Config:
        # Load .env from parent directory (project root)
        env_file = Path(__file__).parent.parent.parent.parent / ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()
