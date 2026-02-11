# -*- coding: utf-8 -*-
"""
SLMS AI Pipeline - Stage 3: Context Loader (FIXED VERSION)
==========================================================

Load relevant context from database based on intent.

FIXES:
- Fixed UTF-8 encoding issues
- Better error handling
- More detailed logging
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ContextLoader:
    """
    Load relevant context from database for entity extraction
    """
    
    def __init__(self, db_session):
        """
        Initialize with database session
        
        Args:
            db_session: Async database session (or DatabaseAdapter)
        """
        self.db = db_session
    
    async def load(
        self,
        intent: str,
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Load context based on intent
        
        Args:
            intent: Classified intent
            user_context: Optional user-provided context
            
        Returns:
            Dict with relevant context data
        """
        
        context = {
            "user_context": user_context or {},
            "intent": intent,
        }
        
        try:
            logger.info(f"[ContextLoader] Loading context for intent: {intent}")
            
            if intent == "create_booking":
                context.update(await self._load_booking_context())
            
            elif intent == "assign_vehicle":
                context.update(await self._load_vehicle_context())
            
            elif intent == "update_status":
                context.update(await self._load_status_context())
            
            elif intent == "query_info":
                context.update(await self._load_query_context())
            
            # Always load common data
            context.update(self._load_common_context())
            
            logger.info(f"[ContextLoader] Loaded keys: {list(context.keys())}")
            
        except Exception as e:
            logger.error(f"[ContextLoader] Failed to load context: {str(e)}", exc_info=True)
            context["error"] = str(e)
            # Ensure we always have common context even on error
            context.update(self._load_common_context())
        
        return context
    
    async def _load_booking_context(self) -> Dict:
        """Load context for booking creation"""
        
        context = {}
        
        # Load active customers
        try:
            customers = await self.db.fetch_all("""
                SELECT 
                    customer_id,
                    customer_code,
                    short_name,
                    company_name
                FROM customers 
                WHERE is_active = true
                ORDER BY short_name
                LIMIT 100
            """)
            context["customers"] = [dict(c) for c in customers] if customers else []
            logger.debug(f"[ContextLoader] Loaded {len(context['customers'])} customers")
        except Exception as e:
            logger.error(f"[ContextLoader] Failed to load customers: {e}")
            context["customers"] = []
        
        # Load routes
        try:
            routes = await self.db.fetch_all("""
                SELECT 
                    route_id,
                    route_code,
                    origin,
                    destination,
                    distance_km
                FROM master_routes 
                WHERE is_active = true
                ORDER BY route_code
                LIMIT 50
            """)
            context["routes"] = [dict(r) for r in routes] if routes else []
        except Exception as e:
            logger.error(f"[ContextLoader] Failed to load routes: {e}")
            context["routes"] = []
        
        # Load vehicle types
        try:
            vehicle_types = await self.db.fetch_all("""
                SELECT type_code, name_vi
                FROM master_vehicle_types 
                WHERE is_active = true
                ORDER BY type_code
            """)
            context["vehicle_types"] = [v["type_code"] for v in vehicle_types] if vehicle_types else []
        except Exception as e:
            logger.error(f"[ContextLoader] Failed to load vehicle types: {e}")
            context["vehicle_types"] = []
        
        # Fallback default vehicle types
        if not context["vehicle_types"]:
            context["vehicle_types"] = ["1.25T", "2.5T", "5T", "10T", "15T", "20T", "CONT20", "CONT40"]
        
        # Load vendors
        try:
            vendors = await self.db.fetch_all("""
                SELECT 
                    vendor_id,
                    vendor_code,
                    short_name
                FROM vendors 
                WHERE is_active = true
                ORDER BY short_name
                LIMIT 50
            """)
            context["vendors"] = [dict(v) for v in vendors] if vendors else []
        except Exception as e:
            logger.error(f"[ContextLoader] Failed to load vendors: {e}")
            context["vendors"] = []
        
        return context
    
    async def _load_vehicle_context(self) -> Dict:
        """Load context for vehicle assignment"""
        
        context = {}
        
        # Load pending jobs waiting for vehicle
        try:
            pending_jobs = await self.db.fetch_all("""
                SELECT 
                    j.job_id,
                    j.job_no,
                    c.short_name as customer,
                    c.customer_code,
                    js.scheduled_date as booking_date,
                    js.scheduled_time as pickup_time,
                    js.origin_address,
                    js.dest_address,
                    v.short_name as vendor
                FROM jobs j
                JOIN customers c ON j.customer_id = c.customer_id
                LEFT JOIN job_services js ON j.job_id = js.job_id
                LEFT JOIN vendors v ON js.vendor_id = v.vendor_id
                WHERE j.status_code IN ('PENDING', 'CONFIRMED')
                  AND js.vehicle_id IS NULL
                ORDER BY js.scheduled_date, js.scheduled_time
                LIMIT 20
            """)
            context["pending_jobs"] = [dict(j) for j in pending_jobs] if pending_jobs else []
            logger.debug(f"[ContextLoader] Loaded {len(context['pending_jobs'])} pending jobs")
        except Exception as e:
            logger.error(f"[ContextLoader] Failed to load pending jobs: {e}")
            context["pending_jobs"] = []
        
        # Load recent drivers (for matching)
        try:
            drivers = await self.db.fetch_all("""
                SELECT DISTINCT 
                    driver_name,
                    driver_phone,
                    license_plate
                FROM jobs
                WHERE driver_name IS NOT NULL
                  AND created_at > NOW() - INTERVAL '30 days'
                LIMIT 30
            """)
            context["recent_drivers"] = [dict(d) for d in drivers] if drivers else []
        except Exception as e:
            logger.error(f"[ContextLoader] Failed to load drivers: {e}")
            context["recent_drivers"] = []
        
        return context
    
    async def _load_status_context(self) -> Dict:
        """Load context for status updates"""
        
        context = {}
        
        # Load active jobs
        try:
            active_jobs = await self.db.fetch_all("""
                SELECT 
                    j.job_id,
                    j.job_no,
                    c.short_name as customer,
                    c.customer_code,
                    j.status_code as status,
                    js.scheduled_date as booking_date,
                    js.scheduled_time as pickup_time,
                    js.vendor_text_input
                FROM jobs j
                JOIN customers c ON j.customer_id = c.customer_id
                LEFT JOIN job_services js ON j.job_id = js.job_id
                WHERE j.status_code IN ('PENDING', 'CONFIRMED', 'DISPATCHED', 'IN_TRANSIT')
                ORDER BY js.scheduled_date DESC, js.scheduled_time DESC
                LIMIT 50
            """)
            context["active_jobs"] = [dict(j) for j in active_jobs] if active_jobs else []
            logger.debug(f"[ContextLoader] Loaded {len(context['active_jobs'])} active jobs")
        except Exception as e:
            logger.error(f"[ContextLoader] Failed to load active jobs: {e}")
            context["active_jobs"] = []
        
        # Load valid status transitions
        context["valid_statuses"] = [
            "PENDING",
            "CONFIRMED",
            "DISPATCHED",
            "IN_TRANSIT",
            "COMPLETED",
            "CANCELLED"
        ]
        
        return context
    
    async def _load_query_context(self) -> Dict:
        """Load context for queries"""
        
        context = {}
        
        # Load recent jobs for reference
        try:
            recent_jobs = await self.db.fetch_all("""
                SELECT 
                    j.job_id,
                    j.job_no,
                    c.short_name as customer,
                    j.status_code as status,
                    j.etd as booking_date,
                    j.total_cost,
                    j.total_revenue
                FROM jobs j
                JOIN customers c ON j.customer_id = c.customer_id
                ORDER BY j.created_at DESC
                LIMIT 20
            """)
            context["recent_jobs"] = [dict(j) for j in recent_jobs] if recent_jobs else []
        except Exception as e:
            logger.error(f"[ContextLoader] Failed to load recent jobs: {e}")
            context["recent_jobs"] = []
        
        # Load customers for query matching (include company_name for AI matching)
        try:
            customers = await self.db.fetch_all("""
                SELECT customer_id, customer_code, short_name, company_name
                FROM customers
                WHERE is_active = true
                ORDER BY short_name
                LIMIT 50
            """)
            context["customers"] = [dict(c) for c in customers] if customers else []
        except Exception as e:
            logger.error(f"[ContextLoader] Failed to load customers for query: {e}")
            context["customers"] = []
        
        return context
    
    def _load_common_context(self) -> Dict:
        """Load common context data (no DB needed)"""
        
        now = datetime.now()
        
        return {
            "current_date": now.strftime("%Y-%m-%d"),
            "current_time": now.strftime("%H:%M"),
            "tomorrow": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
            "day_after_tomorrow": (now + timedelta(days=2)).strftime("%Y-%m-%d"),
        }


# ══════════════════════════════════════════════════════════════════════════════
# CONTEXT FORMATTERS (for prompts) - FIXED UTF-8
# ══════════════════════════════════════════════════════════════════════════════

def format_customers_for_prompt(customers: List[Dict], max_items: int = 20) -> str:
    """Format customer list for inclusion in prompt"""
    
    if not customers:
        return "Không có dữ liệu khách hàng"
    
    lines = []
    for c in customers[:max_items]:
        code = c.get("customer_code", "")
        name = c.get("short_name", "")
        if code:
            lines.append(f"- {code}: {name}")
    
    if not lines:
        return "Không có dữ liệu khách hàng"
    
    return "\n".join(lines)


def format_jobs_for_prompt(jobs: List[Dict], max_items: int = 10) -> str:
    """Format job list for inclusion in prompt"""
    
    if not jobs:
        return "Không có job nào"
    
    lines = []
    for j in jobs[:max_items]:
        job_no = j.get("job_no", "")
        customer = j.get("customer", "") or j.get("customer_code", "")
        date = j.get("booking_date", "")
        time_val = j.get("pickup_time", "")
        vehicle = j.get("vehicle_type", "")
        status = j.get("status", "")
        
        # Format date if it's a datetime object
        if hasattr(date, 'strftime'):
            date = date.strftime("%d/%m")
        elif date:
            date = str(date)[:10]
        
        # Format time
        if hasattr(time_val, 'strftime'):
            time_val = time_val.strftime("%H:%M")
        elif time_val:
            time_val = str(time_val)[:5]
        
        line = f"- {job_no}: {customer}"
        if date:
            line += f" - {date}"
        if time_val:
            line += f" {time_val}"
        if vehicle:
            line += f" - {vehicle}"
        if status:
            line += f" [{status}]"
        
        lines.append(line)
    
    if not lines:
        return "Không có job nào"
    
    return "\n".join(lines)


def format_vehicle_types_for_prompt(types: List[str]) -> str:
    """Format vehicle types for inclusion in prompt"""
    
    if not types:
        return "1.25T, 2.5T, 5T, 10T, 15T, 20T, CONT20, CONT40"
    
    return ", ".join(types)
