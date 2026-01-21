"""
SLMS AI Pipeline - Stage 3: Context Loader
==========================================

Load relevant context from database based on intent.

Context includes:
- Customers list (for CREATE_BOOKING)
- Pending jobs (for ASSIGN_VEHICLE)
- Active jobs (for UPDATE_STATUS)
- Routes, vehicle types, etc.
"""

from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class ContextLoader:
    """
    Load relevant context from database for entity extraction
    """
    
    def __init__(self, db_session):
        """
        Initialize with database session
        
        Args:
            db_session: Async database session
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
            if intent == "create_booking":
                context.update(await self._load_booking_context())
            
            elif intent == "assign_vehicle":
                context.update(await self._load_vehicle_context())
            
            elif intent == "update_status":
                context.update(await self._load_status_context())
            
            elif intent == "query_info":
                context.update(await self._load_query_context())
            
            # Always load common data
            context.update(await self._load_common_context())
            
            logger.info(f"Loaded context for intent '{intent}': {list(context.keys())}")
            
        except Exception as e:
            logger.error(f"Failed to load context: {str(e)}")
            context["error"] = str(e)
        
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
                    full_name,
                    COALESCE(aliases, '[]')::text as aliases
                FROM customers 
                WHERE is_active = true
                ORDER BY short_name
                LIMIT 100
            """)
            context["customers"] = [dict(c) for c in customers]
            logger.debug(f"Loaded {len(customers)} customers")
        except Exception as e:
            logger.error(f"Failed to load customers: {e}")
            context["customers"] = []
        
        # Load routes
        try:
            routes = await self.db.fetch_all("""
                SELECT 
                    route_id,
                    route_code,
                    origin_name,
                    destination_name,
                    distance_km
                FROM routes 
                WHERE is_active = true
                ORDER BY route_code
                LIMIT 50
            """)
            context["routes"] = [dict(r) for r in routes]
        except Exception as e:
            logger.error(f"Failed to load routes: {e}")
            context["routes"] = []
        
        # Load vehicle types
        try:
            vehicle_types = await self.db.fetch_all("""
                SELECT DISTINCT vehicle_type, description
                FROM master_vehicle_types 
                WHERE is_active = true
                ORDER BY sort_order
            """)
            context["vehicle_types"] = [v["vehicle_type"] for v in vehicle_types]
        except Exception as e:
            logger.error(f"Failed to load vehicle types: {e}")
            context["vehicle_types"] = ["1.25T", "2.5T", "5T", "10T", "15T", "20T", "CONT20", "CONT40"]
        
        # Load vendors (for assignment suggestion)
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
            context["vendors"] = [dict(v) for v in vendors]
        except Exception as e:
            logger.error(f"Failed to load vendors: {e}")
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
                    j.booking_date,
                    j.pickup_time,
                    j.vehicle_type,
                    j.origin_address,
                    j.dest_address,
                    v.short_name as vendor
                FROM jobs j
                JOIN customers c ON j.customer_id = c.customer_id
                LEFT JOIN vendors v ON j.vendor_id = v.vendor_id
                WHERE j.status IN ('PENDING', 'CONFIRMED')
                  AND (j.license_plate IS NULL OR j.license_plate = '')
                ORDER BY j.booking_date, j.pickup_time
                LIMIT 20
            """)
            context["pending_jobs"] = [dict(j) for j in pending_jobs]
            logger.debug(f"Loaded {len(pending_jobs)} pending jobs")
        except Exception as e:
            logger.error(f"Failed to load pending jobs: {e}")
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
                ORDER BY MAX(created_at) DESC
                LIMIT 30
            """)
            context["recent_drivers"] = [dict(d) for d in drivers]
        except Exception as e:
            logger.error(f"Failed to load drivers: {e}")
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
                    j.status,
                    j.booking_date,
                    j.pickup_time,
                    j.license_plate,
                    j.driver_name
                FROM jobs j
                JOIN customers c ON j.customer_id = c.customer_id
                WHERE j.status IN ('PENDING', 'CONFIRMED', 'DISPATCHED', 'IN_TRANSIT')
                ORDER BY j.booking_date DESC, j.pickup_time DESC
                LIMIT 50
            """)
            context["active_jobs"] = [dict(j) for j in active_jobs]
            logger.debug(f"Loaded {len(active_jobs)} active jobs")
        except Exception as e:
            logger.error(f"Failed to load active jobs: {e}")
            context["active_jobs"] = []
        
        # Load valid status transitions
        context["valid_statuses"] = [
            "PENDING",
            "CONFIRMED", 
            "DISPATCHED",
            "IN_TRANSIT",
            "DELIVERED",
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
                    j.status,
                    j.booking_date,
                    j.total_cost,
                    j.total_revenue
                FROM jobs j
                JOIN customers c ON j.customer_id = c.customer_id
                ORDER BY j.created_at DESC
                LIMIT 20
            """)
            context["recent_jobs"] = [dict(j) for j in recent_jobs]
        except Exception as e:
            logger.error(f"Failed to load recent jobs: {e}")
            context["recent_jobs"] = []
        
        return context
    
    async def _load_common_context(self) -> Dict:
        """Load common context data"""
        
        context = {}
        
        # Current date info
        from datetime import datetime, timedelta
        
        now = datetime.now()
        context["current_date"] = now.strftime("%Y-%m-%d")
        context["current_time"] = now.strftime("%H:%M")
        context["tomorrow"] = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        
        return context


# ══════════════════════════════════════════════════════════════════════════════
# CONTEXT FORMATTERS (for prompts)
# ══════════════════════════════════════════════════════════════════════════════

def format_customers_for_prompt(customers: List[Dict], max_items: int = 20) -> str:
    """Format customer list for inclusion in prompt"""
    
    if not customers:
        return "Không có dữ liệu khách hàng"
    
    lines = []
    for c in customers[:max_items]:
        code = c.get("customer_code", "")
        name = c.get("short_name", "")
        lines.append(f"- {code}: {name}")
    
    return "\n".join(lines)


def format_jobs_for_prompt(jobs: List[Dict], max_items: int = 10) -> str:
    """Format job list for inclusion in prompt"""
    
    if not jobs:
        return "Không có job nào"
    
    lines = []
    for j in jobs[:max_items]:
        job_no = j.get("job_no", "")
        customer = j.get("customer", "")
        date = j.get("booking_date", "")
        time = j.get("pickup_time", "")
        vehicle = j.get("vehicle_type", "")
        status = j.get("status", "")
        
        line = f"- {job_no}: {customer}"
        if date:
            line += f" - {date}"
        if time:
            line += f" {time}"
        if vehicle:
            line += f" - {vehicle}"
        if status:
            line += f" [{status}]"
        
        lines.append(line)
    
    return "\n".join(lines)


def format_vehicle_types_for_prompt(types: List[str]) -> str:
    """Format vehicle types for inclusion in prompt"""
    
    if not types:
        return "1.25T, 2.5T, 5T, 10T, 15T, 20T, CONT20, CONT40"
    
    return ", ".join(types)
