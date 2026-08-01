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
    GEMINI_MODEL: str = "gemini-2.0-flash"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"

    # AI Conversation Mode
    AI_CONVERSATION_MODE: str = "unified"

    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_DOC_BOT_TOKEN: Optional[str] = None  # Alias used in .env
    TELEGRAM_NOTIFY_BOT_TOKEN: Optional[str] = None  # Bot Sen — riêng cho notify công nợ
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = None  # X-Telegram-Bot-Api-Secret-Token

    @model_validator(mode='after')
    def resolve_telegram_token(self):
        """Support both TELEGRAM_BOT_TOKEN and TELEGRAM_DOC_BOT_TOKEN env vars"""
        if not self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_DOC_BOT_TOKEN:
            self.TELEGRAM_BOT_TOKEN = self.TELEGRAM_DOC_BOT_TOKEN
        return self
    # SMTP (notify kế toán qua email) — optional
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None

    # Resend email API (HTTPS — dùng thay SMTP vì Railway chặn cổng SMTP)
    RESEND_API_KEY: Optional[str] = None
    EMAIL_FROM: Optional[str] = None

    # URL frontend (dùng cho link reset mật khẩu)
    FRONTEND_URL: str = "https://5p-slms.vercel.app"

    # Token bot Telegram DÀNH RIÊNG gửi link reset mật khẩu (bot Sen fivepvietnam_bot).
    # Tách khỏi TELEGRAM_BOT_TOKEN (bot download tài liệu) để không đụng luồng khác.
    RESET_TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_NOTIFY_BOT_TOKEN: Optional[str] = None

    # Gmail API (HTTPS — gửi TỪ chính Gmail công ty, không cần domain riêng)
    GMAIL_CLIENT_ID: Optional[str] = None
    GMAIL_CLIENT_SECRET: Optional[str] = None
    GMAIL_REFRESH_TOKEN: Optional[str] = None
    GMAIL_SENDER: Optional[str] = None

    TELEGRAM_ALLOWED_CHAT_IDS: str = ""  # Comma-separated chat IDs (whitelist)
    TELEGRAM_STORAGE_CHAT_ID: Optional[str] = None  # Private chat/channel for web upload storage

    # Google Drive Configuration
    GDRIVE_ENABLED: bool = False
    GDRIVE_REFRESH_TOKEN: Optional[str] = None
    GDRIVE_CLIENT_ID: Optional[str] = None
    GDRIVE_CLIENT_SECRET: Optional[str] = None
    GDRIVE_ROOT_FOLDER_ID: Optional[str] = None  # Auto-created if not set

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
