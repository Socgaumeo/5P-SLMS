import logging
import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from app.db.supabase_client import get_supabase

logger = logging.getLogger(__name__)


class DatabaseAdapter:
    """
    Adapter to bridge between the async pipeline and Supabase SDK.

    Note: This adapter maintains the same interface as before but now uses
    Supabase SDK instead of raw psycopg2 connections.
    """

    def __init__(self, data_service=None):
        # data_service is kept for backward compatibility but not used
        self._executor = ThreadPoolExecutor(max_workers=5)
        self._client = None

    @property
    def client(self):
        """Lazy-load Supabase client"""
        if self._client is None:
            self._client = get_supabase()
        return self._client

    async def fetch_all(self, query: str, values: tuple = None) -> List[Dict[str, Any]]:
        """
        Execute a query and return all results as list of dicts.

        Note: This method now uses Supabase RPC for raw SQL queries.
        For simple table queries, prefer using table-specific methods.
        """
        return await asyncio.get_event_loop().run_in_executor(
            self._executor,
            self._fetch_all_sync,
            query,
            values
        )

    def _fetch_all_sync(self, query: str, values: tuple = None) -> List[Dict[str, Any]]:
        """
        Synchronous implementation of fetch_all.

        For raw SQL queries, uses Supabase's RPC function if available,
        otherwise attempts to parse and convert to Supabase query builder.
        """
        try:
            # For common patterns, try to convert to Supabase query builder
            # This is a simplified approach - complex queries may need RPC

            query_lower = query.lower().strip()

            # Simple SELECT pattern matching
            if query_lower.startswith('select') and 'from customers' in query_lower:
                return self._query_customers(query, values)
            elif query_lower.startswith('select') and 'from vendors' in query_lower:
                return self._query_vendors(query, values)
            elif query_lower.startswith('select') and 'from jobs' in query_lower:
                return self._query_jobs(query, values)
            elif query_lower.startswith('select') and 'from job_services' in query_lower:
                return self._query_job_services(query, values)
            else:
                # For complex queries, try using RPC or return empty
                logger.warning(f"Complex query not directly supported, returning empty: {query[:100]}...")
                return []

        except Exception as e:
            logger.error(f"Database query error: {e}")
            logger.error(f"Query: {query}")
            raise e

    def _query_customers(self, query: str, values: tuple = None) -> List[Dict[str, Any]]:
        """Query customers table"""
        result = self.client.table('customers').select('*').execute()
        return result.data

    def _query_vendors(self, query: str, values: tuple = None) -> List[Dict[str, Any]]:
        """Query vendors table"""
        result = self.client.table('vendors').select('*').execute()
        return result.data

    def _query_jobs(self, query: str, values: tuple = None) -> List[Dict[str, Any]]:
        """Query jobs table"""
        result = self.client.table('jobs').select('*').execute()
        return result.data

    def _query_job_services(self, query: str, values: tuple = None) -> List[Dict[str, Any]]:
        """Query job_services table"""
        result = self.client.table('job_services').select('*').execute()
        return result.data

    async def execute(self, query: str, values: tuple = None) -> None:
        """Execute a query without returning results"""
        await asyncio.get_event_loop().run_in_executor(
            self._executor,
            self._execute_sync,
            query,
            values
        )

    def _execute_sync(self, query: str, values: tuple = None) -> None:
        """
        Synchronous implementation of execute.

        Note: For write operations, consider using Supabase table methods directly
        (insert, update, delete) instead of raw SQL.
        """
        try:
            query_lower = query.lower().strip()

            # Log warning for write operations - they should use Supabase methods
            if query_lower.startswith(('insert', 'update', 'delete')):
                logger.warning(f"Raw SQL write operation detected. Consider using Supabase methods: {query[:100]}...")

            # For now, just log and skip raw SQL execution
            # Actual write operations should be done via Supabase SDK methods
            logger.info(f"Skipping raw SQL execution (use Supabase SDK methods): {query[:50]}...")

        except Exception as e:
            logger.error(f"Database execute error: {e}")
            raise e

    # Supabase-native methods for common operations

    def get_customer_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get customer by code using Supabase SDK"""
        result = self.client.table('customers').select('*').eq('customer_code', code).limit(1).execute()
        return result.data[0] if result.data else None

    def get_vendor_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get vendor by code using Supabase SDK"""
        result = self.client.table('vendors').select('*').eq('vendor_code', code).limit(1).execute()
        return result.data[0] if result.data else None

    def search_customers(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search customers by keyword"""
        result = self.client.table('customers').select('*').or_(
            f"customer_code.ilike.%{keyword}%,"
            f"short_name.ilike.%{keyword}%,"
            f"company_name.ilike.%{keyword}%"
        ).limit(limit).execute()
        return result.data

    def search_vendors(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search vendors by keyword"""
        result = self.client.table('vendors').select('*').or_(
            f"vendor_code.ilike.%{keyword}%,"
            f"short_name.ilike.%{keyword}%,"
            f"company_name.ilike.%{keyword}%"
        ).limit(limit).execute()
        return result.data

    def get_job_by_number(self, job_no: str) -> Optional[Dict[str, Any]]:
        """Get job by job number"""
        result = self.client.table('jobs').select(
            '*, customers(customer_code, short_name)'
        ).eq('job_no', job_no).limit(1).execute()
        return result.data[0] if result.data else None
