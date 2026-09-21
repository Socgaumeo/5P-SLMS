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


def _project_ref(dsn: str) -> str:
    """
    Lấy project ref của Supabase từ DSN, bất kể DSN đang ở dạng nào:
      - trực tiếp:   postgresql://postgres:<pw>@db.<ref>.supabase.co:5432/postgres
      - qua pooler:  postgresql://postgres.<ref>:<pw>@aws-N-<region>.pooler.supabase.com:6543/postgres
    """
    if not dsn:
        return ''
    m = re.search(r'db\.([a-z0-9]{16,})\.supabase\.co', dsn)      # dạng trực tiếp
    if m:
        return m.group(1)
    m = re.search(r'://postgres\.([a-z0-9]{16,})[:@]', dsn)        # dạng pooler
    if m:
        return m.group(1)
    return ''


def _pooler_url(dsn: str) -> str:
    """
    Dựng lại DSN trỏ vào Supabase pooler IPv4 đang hoạt động.

    Bao phủ CẢ HAI kiểu DSN hỏng đã gặp:
      1. `db.<ref>.supabase.co` — host trực tiếp, từ 2024 Supabase bỏ IPv4 nên CHỈ còn
         bản ghi IPv6; host chạy backend không có IPv6 thì không gọi tới được.
      2. `aws-0-<region>.pooler.supabase.com` — pooler thế hệ cũ, đã ngừng phục vụ;
         DNS vẫn giải ra IPv4 nhưng kết nối bị từ chối.

    Cả hai đều làm psycopg2.connect() fail ngay ở dependency get_db → TOÀN BỘ endpoint
    raw SQL trả 500 (sự cố 21/09/2026: /api/search/{jobs,customers,vendors,drivers} chết
    sạch, trong khi endpoint đi qua Supabase REST vẫn chạy nên nhìn như "chỉ search hỏng").

    Trả '' nếu không nhận ra là DSN Supabase (khi đó cứ để lỗi gốc nổi lên).
    """
    ref = _project_ref(dsn)
    if not ref:
        return ''
    pw = ''
    m = re.search(r'://[^:/@]+:([^@]+)@', dsn)
    if m:
        pw = m.group(1)
    dbname = (dsn.rsplit('/', 1)[-1].split('?')[0] or 'postgres')
    return (f'postgresql://postgres.{ref}:{pw}@'
            f'{POOLER_HOST}:{POOLER_PORT}/{dbname}')


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
        # đã trỏ đúng pooler hiện hành rồi mà vẫn lỗi -> lỗi thật, đừng thử lại vô ích
        if not fallback or fallback == settings.DATABASE_URL:
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
