# backend/app/db/session.py
"""
Database session management.
Provides get_db dependency for FastAPI.
"""

from typing import Generator
from contextlib import contextmanager
import logging
import os
import re
import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import settings

logger = logging.getLogger(__name__)

# Supabase connection pooler (IPv4) — dùng khi host trực tiếp chỉ có IPv6.
# Có thể override bằng biến môi trường nếu Supabase đổi region/endpoint.
POOLER_HOST = os.getenv("SUPABASE_POOLER_HOST", "aws-1-ap-southeast-1.pooler.supabase.com")
POOLER_PORT = os.getenv("SUPABASE_POOLER_PORT", "6543")
CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))


class DatabaseSession:
    """Simple database session wrapper for raw SQL queries"""
    
    def __init__(self, connection):
        self.conn = connection
        self.cursor = connection.cursor(cursor_factory=RealDictCursor)
    
    def execute(self, query: str, params=None):
        self.cursor.execute(query, params)
        return self.cursor
    
    def fetchall(self):
        return self.cursor.fetchall()
    
    def fetchone(self):
        return self.cursor.fetchone()
    
    def commit(self):
        self.conn.commit()
    
    def rollback(self):
        self.conn.rollback()
    
    def close(self):
        self.cursor.close()
        self.conn.close()


def _pooler_url(direct_url: str) -> str:
    """
    Chuyển DSN kết nối trực tiếp (db.<ref>.supabase.co:5432) sang Supabase pooler
    (aws-1-ap-southeast-1.pooler.supabase.com:6543, user postgres.<ref>).

    Lý do: từ 2024 Supabase bỏ IPv4 cho host trực tiếp — `db.<ref>.supabase.co`
    CHỈ còn bản ghi IPv6. Host chạy backend (Railway/VPS) không có IPv6 thì
    psycopg2.connect() fail ngay ở dependency get_db, khiến TOÀN BỘ endpoint
    dùng raw SQL trả 500 (sự cố 21/09/2026: /api/search/* chết sạch trong khi
    các endpoint đi qua Supabase REST vẫn chạy).
    """
    m = re.search(r'db\.([a-z0-9]+)\.supabase\.co', direct_url or '')
    if not m:
        return ''
    ref = m.group(1)
    url = direct_url.replace(
        f'db.{ref}.supabase.co',
        f'{POOLER_HOST}'
    ).replace(':5432', f':{POOLER_PORT}')
    # user 'postgres' -> 'postgres.<ref>' (yêu cầu của pooler)
    url = re.sub(r'://postgres(?=:)', f'://postgres.{ref}', url)
    return url


def get_connection():
    """
    Get a raw database connection.

    Thử DATABASE_URL trước; nếu không kết nối được (thường do host chỉ có IPv6)
    thì tự chuyển sang Supabase pooler IPv4 thay vì để cả API sập.
    """
    try:
        return psycopg2.connect(
            settings.DATABASE_URL,
            cursor_factory=RealDictCursor,
            connect_timeout=CONNECT_TIMEOUT,
        )
    except psycopg2.OperationalError as e:
        fallback = _pooler_url(settings.DATABASE_URL)
        if not fallback:
            raise
        logger.warning(
            "Kết nối DB trực tiếp thất bại (%s) — chuyển sang pooler IPv4 %s:%s. "
            "Nên sửa hẳn biến DATABASE_URL sang chuỗi pooler để khỏi tốn 1 lần thử mỗi request.",
            str(e).strip()[:120], POOLER_HOST, POOLER_PORT,
        )
        return psycopg2.connect(
            fallback,
            cursor_factory=RealDictCursor,
            connect_timeout=CONNECT_TIMEOUT,
        )


def get_db() -> Generator[DatabaseSession, None, None]:
    """
    FastAPI dependency that yields a database session.
    Automatically closes connection after request.
    """
    conn = get_connection()
    session = DatabaseSession(conn)
    try:
        yield session
    finally:
        session.close()


@contextmanager
def get_db_context():
    """Context manager for database session (for non-FastAPI usage)"""
    conn = get_connection()
    session = DatabaseSession(conn)
    try:
        yield session
    finally:
        session.close()
