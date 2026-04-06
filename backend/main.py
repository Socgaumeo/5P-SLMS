"""
SLMS Backend - FastAPI Application
Main entry point with Chat UI API
"""

import re

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api.dependencies import get_current_user, require_manager_or_admin
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.rate_limiter import limiter
from app.api import chat, jobs, health, excel_import, search, admin, auth, users, audit, rate_file_upload
from app.api.exports import meiko_customer_export_template as meiko_export
from app.api.exports import customer_export_template_registry as customer_exports
import importlib
telegram_webhook = importlib.import_module("app.api.telegram-webhook-handler")
document_crud = importlib.import_module("app.api.document-crud-endpoints")
debit_endpoints = importlib.import_module("app.api.debit-template-and-generation-endpoints")

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

# CORS - origins configured via ALLOWED_ORIGINS env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# GZip compression for API responses
app.add_middleware(GZipMiddleware, minimum_size=500)

# Rate limiting (default 100/min, login 5/min via decorator)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Routers
app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(excel_import.router, prefix="/api/excel", tags=["Excel Import"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(search.router, tags=["Search"])
app.include_router(admin.router, tags=["Admin"])
app.include_router(auth.router, tags=["Auth"])
app.include_router(users.router, tags=["Users"])
app.include_router(audit.router, tags=["Audit"])
app.include_router(meiko_export.router, prefix="/api/jobs", tags=["MEIKO Export"])
app.include_router(customer_exports.router, prefix="/api/exports", tags=["Customer Exports"])
app.include_router(rate_file_upload.router, tags=["Rate File Upload"])
app.include_router(telegram_webhook.router, tags=["Telegram Webhook"])
app.include_router(document_crud.router, tags=["Documents"])
app.include_router(debit_endpoints.router, tags=["Debit Templates"])


@app.get("/")
async def root():
    return {
        "message": "SLMS Backend API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Dashboard endpoints
@app.get("/api/dashboard/stats")
async def dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    from app.api.jobs import get_dashboard_stats
    return await get_dashboard_stats()


@app.get("/api/services/{service_type}")
async def services_by_type(service_type: str, current_user: dict = Depends(get_current_user)):
    """Get service-specific data (trucking, warehouse, customs, packing)"""
    from app.api.jobs import get_service_data
    return await get_service_data(service_type)


@app.get("/api/customers")
async def list_customers(current_user: dict = Depends(get_current_user)):
    """Get customers for dropdown in job creation form"""
    try:
        from app.db.supabase_client import get_supabase
        client = get_supabase()
        result = client.table('customers').select(
            'customer_id, customer_code, short_name, company_name'
        ).eq('is_active', True).order('customer_code').execute()

        customers = [
            {
                "customer_id": c["customer_id"],
                "customer_code": c["customer_code"],
                "short_name": c["short_name"],
                "full_name": c["company_name"]
            }
            for c in (result.data or [])
        ]
        return {"customers": customers}
    except Exception as e:
        logger.error(f"List customers error: {e}")
        return {"customers": [], "error": str(e)}


@app.get("/api/vendors")
async def list_vendors(current_user: dict = Depends(get_current_user)):
    """Get vendors for dropdown in assignment form"""
    try:
        from app.db.supabase_client import get_supabase
        client = get_supabase()
        result = client.table('vendors').select(
            'vendor_id, vendor_code, short_name, company_name, vendor_type'
        ).eq('is_active', True).order('short_name').execute()
        return {"vendors": result.data or []}
    except Exception as e:
        return {"vendors": [], "error": str(e)}


# Search endpoints for chat UI
@app.get("/api/search/customers")
async def search_customers_api(q: str = "", current_user: dict = Depends(get_current_user)):
    """Search customers by keyword for chat UI"""
    q = re.sub(r'[,.()*;\'""]', '', q).strip()[:100]
    try:
        from app.db.supabase_client import get_supabase
        client = get_supabase()

        if q and len(q) >= 1:
            # Use or_ with proper PostgREST filter syntax
            search_filter = f"customer_code.ilike.%{q}%,short_name.ilike.%{q}%,company_name.ilike.%{q}%"
            result = client.table('customers').select(
                'customer_id, customer_code, short_name, company_name'
            ).or_(search_filter).limit(20).execute()
        else:
            result = client.table('customers').select(
                'customer_id, customer_code, short_name, company_name'
            ).eq('is_active', True).order('short_name').limit(20).execute()

        return {
            "results": [
                {"id": c["customer_id"], "code": c["customer_code"], "name": c["short_name"] or c["company_name"]}
                for c in (result.data or [])
            ]
        }
    except Exception as e:
        logger.error(f"Search customers error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"results": [], "error": str(e)}


@app.get("/api/search/vendors")
async def search_vendors_api(q: str = "", current_user: dict = Depends(get_current_user)):
    """Search vendors by keyword for chat UI"""
    q = re.sub(r'[,.()*;\'""]', '', q).strip()[:100]
    try:
        from app.db.supabase_client import get_supabase
        client = get_supabase()

        if q and len(q) >= 1:
            search_filter = f"vendor_code.ilike.%{q}%,short_name.ilike.%{q}%,company_name.ilike.%{q}%"
            result = client.table('vendors').select(
                'vendor_id, vendor_code, short_name, company_name'
            ).or_(search_filter).limit(20).execute()
        else:
            result = client.table('vendors').select(
                'vendor_id, vendor_code, short_name, company_name'
            ).eq('is_active', True).order('short_name').limit(20).execute()

        return {
            "results": [
                {"id": v["vendor_id"], "code": v["vendor_code"], "name": v["short_name"] or v["company_name"]}
                for v in (result.data or [])
            ]
        }
    except Exception as e:
        logger.error(f"Search vendors error: {e}")
        return {"results": [], "error": str(e)}


@app.get("/api/employees")
async def list_employees(current_user: dict = Depends(get_current_user)):
    """Get employees for dropdown in assignment form"""
    try:
        from app.db.supabase_client import get_supabase
        client = get_supabase()
        result = client.table('employees').select(
            'employee_id, employee_code, full_name, short_name, department, position'
        ).eq('is_active', True).order('full_name').execute()
        return {"employees": result.data or []}
    except Exception as e:
        logger.error(f"List employees error: {e}")
        return {"employees": [], "error": str(e)}


from pydantic import BaseModel
from typing import Optional

class AssignServiceRequest(BaseModel):
    vendor_id: Optional[int] = None
    employee_id: Optional[int] = None
    status_code: Optional[str] = None
    license_plate: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None


@app.put("/api/services/{svc_id}/assign")
async def assign_service(svc_id: int, request: AssignServiceRequest, current_user: dict = Depends(get_current_user)):
    """Assign vendor/employee and vehicle info to a service"""
    try:
        from app.db.supabase_client import get_supabase
        from datetime import datetime
        client = get_supabase()

        now = datetime.now().isoformat()

        # Build update data
        update_data = {"updated_at": now}
        has_vehicle_assignment = False

        if request.vendor_id is not None:
            update_data["vendor_id"] = request.vendor_id if request.vendor_id > 0 else None

        if request.employee_id is not None:
            update_data["employee_id"] = request.employee_id if request.employee_id > 0 else None

        if request.status_code:
            update_data["status_code"] = request.status_code

        if request.license_plate is not None:
            update_data["license_plate"] = request.license_plate or None
            if request.license_plate:
                has_vehicle_assignment = True

        if request.driver_name is not None:
            update_data["driver_name"] = request.driver_name or None

        if request.driver_phone is not None:
            update_data["driver_phone"] = request.driver_phone or None

        if len(update_data) <= 1:  # Only updated_at
            return {"success": False, "message": "No fields to update"}

        # Auto-update status to DISPATCHED when vehicle is assigned
        if has_vehicle_assignment and "status_code" not in update_data:
            update_data["status_code"] = "DISPATCHED"

        result = client.table("job_services").update(update_data).eq("svc_id", svc_id).execute()

        if not result.data:
            return {"success": False, "message": "Service not found"}

        # Get job_id from the service and sync job status
        service = result.data[0]
        job_id = service.get("job_id")

        if job_id and update_data.get("status_code"):
            # Update job status to match service status
            client.table("jobs").update({
                "status_code": update_data["status_code"],
                "updated_at": now
            }).eq("job_id", job_id).execute()

        return {"success": True, "message": "Service updated", "service": service}

    except Exception as e:
        logger.error(f"Assign service error: {e}")
        return {"success": False, "message": str(e)}


class UpdateServiceStatusRequest(BaseModel):
    status_code: str


@app.put("/api/services/{svc_id}/status")
async def update_service_status(svc_id: int, request: UpdateServiceStatusRequest, current_user: dict = Depends(get_current_user)):
    """Update status of individual service"""
    try:
        from app.db.supabase_client import get_supabase
        from datetime import datetime
        client = get_supabase()

        # Valid statuses for all service types
        valid_statuses = [
            'PENDING', 'CONFIRMED', 'DISPATCHED', 'IN_TRANSIT',
            'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED',
            'WHS_RECEIVED', 'WHS_PROCESSING', 'WHS_RELEASED',
            'CUS_SUBMITTED', 'CUS_PROCESSING', 'CUS_APPROVED'
        ]

        new_status = request.status_code.upper()
        if new_status not in valid_statuses:
            return {"success": False, "message": f"Trạng thái '{new_status}' không hợp lệ"}

        # Verify service exists
        svc_result = client.table('job_services').select('svc_id, job_id').eq('svc_id', svc_id).limit(1).execute()
        if not svc_result.data:
            return {"success": False, "message": f"Service {svc_id} not found"}

        # Update service status
        now = datetime.now().isoformat()
        client.table('job_services').update({
            'status_code': new_status,
            'updated_at': now
        }).eq('svc_id', svc_id).execute()

        # Sync job status with service status
        job_id = svc_result.data[0].get('job_id')
        if job_id:
            client.table('jobs').update({
                'status_code': new_status,
                'updated_at': now
            }).eq('job_id', job_id).execute()
            logger.info(f"Synced job {job_id} status to {new_status}")

        logger.info(f"Updated service {svc_id} status to {new_status}")
        return {"success": True, "status_code": new_status}

    except Exception as e:
        logger.error(f"Error updating service status: {e}")
        return {"success": False, "message": str(e)}


@app.delete("/api/services/{svc_id}")
async def delete_service(svc_id: int, current_user: dict = Depends(require_manager_or_admin)):
    """Delete a service from job"""
    try:
        from app.db.supabase_client import get_supabase
        client = get_supabase()

        # Verify service exists and get job_id
        svc_result = client.table('job_services').select('svc_id, job_id').eq('svc_id', svc_id).limit(1).execute()
        if not svc_result.data:
            return {"success": False, "message": f"Service {svc_id} not found"}

        svc = svc_result.data[0]
        job_id = svc['job_id']

        # Check if this is the last service
        services_result = client.table('job_services').select('svc_id').eq('job_id', job_id).execute()
        if len(services_result.data) <= 1:
            return {"success": False, "message": "Không thể xóa dịch vụ cuối cùng của job"}

        # Delete the service
        client.table('job_services').delete().eq('svc_id', svc_id).execute()

        logger.info(f"Deleted service {svc_id} from job {job_id}")
        return {"success": True, "message": "Đã xóa dịch vụ"}

    except Exception as e:
        logger.error(f"Error deleting service: {e}")
        return {"success": False, "message": str(e)}


class UpdateServiceNotesRequest(BaseModel):
    notes: str


@app.put("/api/services/{svc_id}/notes")
async def update_service_notes(svc_id: int, request: UpdateServiceNotesRequest, current_user: dict = Depends(get_current_user)):
    """Update notes/special requirements for a service"""
    try:
        from app.db.supabase_client import get_supabase
        from datetime import datetime
        client = get_supabase()

        # Update service notes
        result = client.table('job_services').update({
            'special_requirements': request.notes,
            'updated_at': datetime.now().isoformat()
        }).eq('svc_id', svc_id).execute()

        if not result.data:
            return {"success": False, "message": f"Service {svc_id} not found"}

        logger.info(f"Updated notes for service {svc_id}")
        return {"success": True, "message": "Đã lưu ghi chú"}

    except Exception as e:
        logger.error(f"Error updating service notes: {e}")
        return {"success": False, "message": str(e)}


class UpdateJobStatusRequest(BaseModel):
    status_code: str


@app.put("/api/jobs/{job_id}/status")
async def update_job_status(job_id: int, request: UpdateJobStatusRequest, current_user: dict = Depends(get_current_user)):
    """Update job status (also updates all services status)"""
    try:
        from app.db.supabase_client import get_supabase
        from datetime import datetime
        client = get_supabase()

        valid_statuses = ["PENDING", "DISPATCHED", "IN_TRANSIT", "COMPLETED", "CANCELLED"]
        if request.status_code.upper() not in valid_statuses:
            return {"success": False, "message": f"Invalid status. Valid: {valid_statuses}"}

        new_status = request.status_code.upper()
        now = datetime.now().isoformat()

        # Update job status
        job_result = client.table("jobs").update({
            "status_code": new_status,
            "updated_at": now
        }).eq("job_id", job_id).execute()

        if not job_result.data:
            return {"success": False, "message": "Job not found"}

        # Also update all services to same status
        client.table("job_services").update({
            "status_code": new_status,
            "updated_at": now
        }).eq("job_id", job_id).execute()

        return {"success": True, "message": f"Job updated to {new_status}", "job": job_result.data[0]}

    except Exception as e:
        logger.error(f"Update job status error: {e}")
        return {"success": False, "message": str(e)}


@app.delete("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: int, current_user: dict = Depends(require_manager_or_admin)):
    """Cancel a job (set status to CANCELLED)"""
    try:
        from app.db.supabase_client import get_supabase
        from datetime import datetime
        client = get_supabase()

        now = datetime.now().isoformat()

        # Update job status to CANCELLED
        job_result = client.table("jobs").update({
            "status_code": "CANCELLED",
            "updated_at": now
        }).eq("job_id", job_id).execute()

        if not job_result.data:
            return {"success": False, "message": "Job not found"}

        # Also cancel all services
        client.table("job_services").update({
            "status_code": "CANCELLED",
            "updated_at": now
        }).eq("job_id", job_id).execute()

        return {"success": True, "message": "Job cancelled", "job": job_result.data[0]}

    except Exception as e:
        logger.error(f"Cancel job error: {e}")
        return {"success": False, "message": str(e)}
