# backend/app/db/supabase_client.py
"""
Supabase client for database operations.
Provides both sync and async clients.
"""

from supabase import create_client, Client
from app.core.config import settings


# Singleton Supabase client
_supabase_client: Client | None = None


def get_supabase() -> Client:
    """
    Get Supabase client instance (singleton pattern).
    Uses service_role key for full database access.
    """
    global _supabase_client

    if _supabase_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment"
            )

        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )

    return _supabase_client


def get_supabase_anon() -> Client:
    """
    Get Supabase client with anon key (for public/RLS-restricted access).
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment"
        )

    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY
    )


# Convenience alias
supabase = get_supabase
