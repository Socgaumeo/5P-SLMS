# backend/app/db/supabase_adapter.py
"""
Supabase adapter for async database operations.
Wraps Supabase client to provide async-compatible interface for ContextLoader.
"""

from typing import List, Dict, Any
from .supabase_client import get_supabase


class SupabaseAdapter:
    """
    Adapter to make Supabase client compatible with ContextLoader's async interface.
    Maps SQL-like queries to Supabase PostgREST API calls.
    """

    def __init__(self):
        self.client = get_supabase()

    async def fetch_all(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a SQL-like query and return results.
        Maps common queries to Supabase table operations.
        """
        query_lower = query.lower().strip()

        # Parse the query to determine table and filters
        if "from customers" in query_lower:
            return await self._fetch_customers(query_lower)
        elif "from master_routes" in query_lower:
            return await self._fetch_routes(query_lower)
        elif "from master_vehicle_types" in query_lower:
            return await self._fetch_vehicle_types(query_lower)
        elif "from vendors" in query_lower:
            return await self._fetch_vendors(query_lower)
        elif "from jobs" in query_lower:
            return await self._fetch_jobs(query_lower)
        else:
            return []

    async def _fetch_customers(self, query: str) -> List[Dict]:
        """Fetch customers for context"""
        try:
            result = self.client.table('customers').select(
                'customer_id, customer_code, short_name, company_name'
            ).eq('is_active', True).order('short_name').limit(100).execute()
            return result.data or []
        except Exception as e:
            import logging
            logging.error(f"[SupabaseAdapter] Error fetching customers: {e}")
            return []

    async def _fetch_routes(self, query: str) -> List[Dict]:
        """Fetch routes for context"""
        try:
            result = self.client.table('master_routes').select(
                'route_id, route_code, origin, destination, distance_km'
            ).eq('is_active', True).order('route_code').limit(50).execute()
            return result.data or []
        except Exception as e:
            import logging
            logging.error(f"[SupabaseAdapter] Error fetching routes: {e}")
            return []

    async def _fetch_vehicle_types(self, query: str) -> List[Dict]:
        """Fetch vehicle types for context"""
        try:
            result = self.client.table('master_vehicle_types').select(
                'type_code, name_vi'
            ).eq('is_active', True).order('type_code').execute()
            return result.data or []
        except Exception as e:
            import logging
            logging.error(f"[SupabaseAdapter] Error fetching vehicle types: {e}")
            return []

    async def _fetch_vendors(self, query: str) -> List[Dict]:
        """Fetch vendors for context"""
        try:
            result = self.client.table('vendors').select(
                'vendor_id, vendor_code, short_name'
            ).eq('is_active', True).order('short_name').limit(50).execute()
            return result.data or []
        except Exception as e:
            import logging
            logging.error(f"[SupabaseAdapter] Error fetching vendors: {e}")
            return []

    async def _fetch_jobs(self, query: str) -> List[Dict]:
        """Fetch jobs for context based on query filters"""
        try:
            # Determine status filter from query
            if "pending" in query or "confirmed" in query:
                statuses = ['PENDING', 'CONFIRMED']
            elif "in_transit" in query or "dispatched" in query:
                statuses = ['PENDING', 'CONFIRMED', 'DISPATCHED', 'IN_TRANSIT']
            else:
                statuses = ['PENDING', 'CONFIRMED', 'DISPATCHED', 'IN_TRANSIT']

            result = self.client.table('jobs').select(
                'job_id, job_no, status_code, created_at, '
                'customers(customer_code, short_name)'
            ).in_('status_code', statuses).order(
                'created_at', desc=True
            ).limit(50).execute()

            # Flatten nested customer data
            jobs = []
            for job in result.data or []:
                customer = job.pop('customers', {}) or {}
                job['customer'] = customer.get('short_name') or customer.get('customer_code')
                job['customer_code'] = customer.get('customer_code')
                jobs.append(job)

            return jobs
        except Exception as e:
            import logging
            logging.error(f"[SupabaseAdapter] Error fetching jobs: {e}")
            return []


# Singleton instance
_adapter: SupabaseAdapter | None = None


def get_supabase_adapter() -> SupabaseAdapter:
    """Get singleton SupabaseAdapter instance"""
    global _adapter
    if _adapter is None:
        _adapter = SupabaseAdapter()
    return _adapter
