# backend/app/db/session.py
"""
Database session management.
Provides get_db dependency for FastAPI.
"""

from typing import Generator
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import settings


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


def get_connection():
    """Get a raw database connection"""
    return psycopg2.connect(
        settings.DATABASE_URL,
        cursor_factory=RealDictCursor
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
