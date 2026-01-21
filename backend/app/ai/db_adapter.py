import logging
import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class DatabaseAdapter:
    """
    Adapter to bridge between the async pipeline (which expects async .fetch_all)
    and the synchronous DataService (which uses psycopg2).
    """
    
    def __init__(self, data_service):
        self.data_service = data_service
        self._executor = ThreadPoolExecutor(max_workers=5)
        
    async def fetch_all(self, query: str, values: tuple = None) -> List[Dict[str, Any]]:
        """
        Execute a query and return all results as list of dicts.
        Runs sync DB operation in a thread pool.
        """
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, 
            self._fetch_all_sync, 
            query, 
            values
        )
        
    def _fetch_all_sync(self, query: str, values: tuple = None) -> List[Dict[str, Any]]:
        """Synchronous implementation of fetch_all using psycopg2"""
        conn = None
        cursor = None
        try:
            conn = self.data_service._get_connection()
            cursor = conn.cursor()
            
            if values:
                cursor.execute(query, values)
            else:
                cursor.execute(query)
                
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Database query error: {e}")
            logger.error(f"Query: {query}")
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
                
    async def execute(self, query: str, values: tuple = None) -> None:
        """Execute a query without returning results"""
        await asyncio.get_event_loop().run_in_executor(
            self._executor,
            self._execute_sync,
            query,
            values
        )
        
    def _execute_sync(self, query: str, values: tuple = None) -> None:
        """Synchronous implementation of execute"""
        conn = None
        cursor = None
        try:
            conn = self.data_service._get_connection()
            cursor = conn.cursor()
            
            if values:
                cursor.execute(query, values)
            else:
                cursor.execute(query)
                
            conn.commit()
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database execute error: {e}")
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
