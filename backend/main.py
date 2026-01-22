"""
SLMS Backend - FastAPI Application
Main entry point with Chat UI API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api import chat, jobs, health, excel_import, search

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Starting SLMS Backend...")
    logger.info(f"📊 Database: {settings.DATABASE_URL[:50]}...")
    logger.info(f"🤖 AI Provider: {settings.AI_PROVIDER}")
    yield
    logger.info("👋 Shutting down SLMS Backend...")


app = FastAPI(
    title="SLMS Backend",
    description="Short-haul Logistics Management System - Chat UI API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(excel_import.router, prefix="/api/excel", tags=["Excel Import"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(search.router, tags=["Search"])


@app.get("/")
async def root():
    return {
        "message": "SLMS Backend API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Dashboard endpoints
@app.get("/api/dashboard/stats")
async def dashboard_stats():
    """Get dashboard statistics"""
    from app.api.jobs import get_dashboard_stats
    return await get_dashboard_stats()


@app.get("/api/services/{service_type}")
async def services_by_type(service_type: str):
    """Get service-specific data (trucking, warehouse, customs, packing)"""
    from app.api.jobs import get_service_data
    return await get_service_data(service_type)


@app.get("/api/customers")
async def list_customers():
    """Get customers for dropdown in job creation form"""
    from app.services.data_service import get_data_service
    data_service = get_data_service()
    conn = data_service._get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT customer_id, customer_code, short_name, full_name 
            FROM customers 
            WHERE is_active = true
            ORDER BY customer_code
        """)
        customers = [dict(row) for row in cursor.fetchall()]
        return {"customers": customers}
    except Exception as e:
        return {"customers": [], "error": str(e)}


@app.get("/api/vendors")
async def list_vendors():
    """Get vendors for dropdown in assignment form"""
    from app.services.data_service import get_data_service
    data_service = get_data_service()
    conn = data_service._get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT vendor_id, vendor_code, short_name, company_name, vendor_type 
            FROM vendors 
            WHERE is_active = true
            ORDER BY short_name
        """)
        vendors = [dict(row) for row in cursor.fetchall()]
        return {"vendors": vendors}
    except Exception as e:
        return {"vendors": [], "error": str(e)}


@app.get("/api/employees")
async def list_employees():
    """Get employees for dropdown in assignment form"""
    from app.services.data_service import get_data_service
    data_service = get_data_service()
    conn = data_service._get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT employee_id, employee_code, full_name, short_name, department, position 
            FROM employees 
            WHERE is_active = true
            ORDER BY full_name
        """)
        employees = [dict(row) for row in cursor.fetchall()]
        return {"employees": employees}
    except Exception as e:
        return {"employees": [], "error": str(e)}


from pydantic import BaseModel
from typing import Optional

class AssignServiceRequest(BaseModel):
    vendor_id: Optional[int] = None
    employee_id: Optional[int] = None
    status_code: Optional[str] = None

@app.put("/api/services/{svc_id}/assign")
async def assign_service(svc_id: int, request: AssignServiceRequest):
    """Assign vendor or employee to a service"""
    from app.services.data_service import get_data_service
    data_service = get_data_service()
    conn = data_service._get_connection()
    cursor = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if request.vendor_id is not None:
            updates.append("vendor_id = %s")
            params.append(request.vendor_id if request.vendor_id > 0 else None)
        
        if request.employee_id is not None:
            updates.append("employee_id = %s")
            params.append(request.employee_id if request.employee_id > 0 else None)
        
        if request.status_code:
            updates.append("status_code = %s")
            params.append(request.status_code)
        
        if not updates:
            return {"success": False, "message": "No fields to update"}
        
        updates.append("updated_at = NOW()")
        params.append(svc_id)
        
        cursor.execute(f"""
            UPDATE job_services 
            SET {', '.join(updates)}
            WHERE svc_id = %s
        """, params)
        conn.commit()
        
        return {"success": True, "message": "Service updated successfully"}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
