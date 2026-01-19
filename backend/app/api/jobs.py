"""
Jobs API - Job management endpoints
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import date, time, datetime
import logging
import traceback

from app.services.data_service import get_data_service
from app.services.message_service import get_message_service

logger = logging.getLogger(__name__)
router = APIRouter()


# Models

class JobCreateFromChatRequest(BaseModel):
    """Request from Chat UI with AI-extracted entities"""
    entities: Dict[str, Any]
    enriched_data: Optional[Dict[str, Any]] = None


class JobCreateRequest(BaseModel):
    customer_id: int
    booking_date: date
    pickup_time: Optional[time] = None
    route_id: Optional[int] = None
    vehicle_type: str
    vendor_id: Optional[int] = None
    invoice_numbers: Optional[str] = None
    cargo_type: Optional[str] = None
    package_info: Optional[str] = None
    cost_amount: Optional[float] = None
    revenue_amount: Optional[float] = None
    pickup_address: Optional[str] = None
    delivery_address: Optional[str] = None


class VehicleAssignRequest(BaseModel):
    license_plate: str
    driver_name: str
    driver_phone: Optional[str] = None
    driver_id_card: Optional[str] = None


class JobResponse(BaseModel):
    success: bool = True
    job_id: Optional[int] = None
    job_number: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None


# Endpoints

@router.post("/create", response_model=JobResponse)
async def create_job(request: JobCreateFromChatRequest):
    """
    Create new job from Chat UI with AI-extracted entities
    """
    try:
        data_service = get_data_service()
        
        entities = request.entities
        enriched = request.enriched_data or {}
        
        logger.info(f"Creating job from entities: {entities}")
        
        # Parse booking date
        booking_date_str = entities.get('booking_date') or enriched.get('booking_date')
        if booking_date_str:
            if isinstance(booking_date_str, str):
                booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
            else:
                booking_date = booking_date_str
        else:
            booking_date = date.today()
        
        # Parse pickup time
        pickup_time_str = entities.get('pickup_time') or enriched.get('pickup_time')
        pickup_time = None
        if pickup_time_str:
            try:
                if ':' in pickup_time_str:
                    parts = pickup_time_str.split(':')
                    pickup_time = time(int(parts[0]), int(parts[1]))
            except:
                pass
        
        # Handle invoice numbers
        inv_nums = entities.get('invoice_numbers') or enriched.get('invoice_numbers')
        if isinstance(inv_nums, list):
            invoice_numbers = ', '.join(inv_nums)
        else:
            invoice_numbers = inv_nums
        
        # Validate customer_id exists
        customer_id = enriched.get('customer_id')
        if not customer_id:
            return JobResponse(
                success=False,
                message=f"Không tìm thấy khách hàng '{entities.get('customer_code')}' trong DB. Vui lòng chọn khách hàng đúng."
            )
        
        # Build job data with structured cargo fields
        job_data = {
            'customer_id': customer_id,
            'booking_date': booking_date,
            'pickup_time': pickup_time,
            'route_id': enriched.get('route_id'),
            'vehicle_type': entities.get('vehicle_type') or enriched.get('vehicle_type') or '1.25T',
            'vendor_id': enriched.get('vendor_id'),
            'invoice_numbers': invoice_numbers,
            'customer_code': entities.get('customer_code') or enriched.get('customer_code'),
            
            # Service type - check services array first, then service_type
            'services': entities.get('services') or [],  # Array of services from AI
            'service_type_code': (entities.get('services') or [None])[0] or entities.get('service_type') or enriched.get('service_type') or 'TRUCKING_SHORT',
            
            # Structured cargo data (single item)
            'cargo_type': entities.get('cargo_type') or enriched.get('cargo_type'),
            'package_quantity': entities.get('package_quantity'),
            'package_unit': entities.get('package_unit'),
            'weight_kg': entities.get('weight_kg'),
            'dimension_length_cm': entities.get('dimension_length_cm'),
            'dimension_width_cm': entities.get('dimension_width_cm'),
            'dimension_height_cm': entities.get('dimension_height_cm'),
            
            # Multi-item cargo (from Excel/multiple lines)
            'cargo_items': entities.get('cargo_items', []),
            
            # Totals (for multi-item)
            'total_packages': entities.get('total_packages'),
            'total_weight_kg': entities.get('total_weight_kg'),
            'total_cbm': entities.get('total_cbm'),
            
            # Addresses
            'pickup_address': entities.get('pickup_address') or enriched.get('pickup_address'),
            'delivery_address': entities.get('delivery_address') or entities.get('delivery_details') or enriched.get('delivery_address'),
            
            # Special requirements
            'special_requirements': entities.get('special_requirements') or enriched.get('special_requirements'),
            
            # Warehouse-specific
            'storage_start_date': entities.get('storage_start_date'),
            'storage_end_date': entities.get('storage_end_date'),
            
            # Customs-specific
            'declaration_no': entities.get('declaration_no'),
            'declaration_datetime': entities.get('declaration_datetime'),
            'loai_hinh': entities.get('loai_hinh'),
            'customs_type': entities.get('customs_type'),
            'customs_port': entities.get('customs_port'),
            'buyer_name': entities.get('buyer_name'),
            'seller_name': entities.get('seller_name'),
            'hs_code': entities.get('hs_code'),
            'bl_awb_no': entities.get('bl_awb_no'),
            'co_no': entities.get('co_no'),
            
            # Packing-specific
            'packing_type': entities.get('packing_type'),
            'items_count': entities.get('items_count'),
            'packages_output': entities.get('packages_output'),
            'before_length_cm': entities.get('before_length_cm'),
            'before_width_cm': entities.get('before_width_cm'),
            'before_height_cm': entities.get('before_height_cm'),
            'after_length_cm': entities.get('after_length_cm'),
            'after_width_cm': entities.get('after_width_cm'),
            'after_height_cm': entities.get('after_height_cm'),
            'shrink_wrap': entities.get('shrink_wrap'),
            'vacuum_pack': entities.get('vacuum_pack'),
            'lashing': entities.get('lashing'),
            'fumigation': entities.get('fumigation'),
            
            # Multi-item packing
            'packing_items': entities.get('packing_items', []),
            'total_weight_kg': entities.get('total_weight_kg'),
            
            # Vendor
            'vendor_code': entities.get('vendor_code'),
        }
        
        logger.info(f"Job data to create: {job_data}")
        
        # Create job in database
        job = await data_service.create_job(job_data, user_id=1)
        
        logger.info(f"Job created: {job}")
        
        return JobResponse(
            success=True,
            job_id=job.get("id"),
            job_number=job.get("job_number"),
            status="PENDING",
            message="Job đã được tạo thành công!"
        )
        
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        logger.error(traceback.format_exc())
        return JobResponse(
            success=False,
            message=f"Lỗi tạo job: {str(e)}"
        )


@router.post("/{job_id}/assign-vehicle", response_model=JobResponse)
async def assign_vehicle(job_id: int, request: VehicleAssignRequest):
    """
    Assign vehicle to job and generate customer confirmation message
    """
    try:
        data_service = get_data_service()
        
        # Check job exists
        job_data = await data_service.get_job(job_id)
        if not job_data:
            raise HTTPException(404, f"Job {job_id} not found")
        
        # Assign vehicle
        await data_service.assign_vehicle(job_id, request.model_dump(), user_id=1)
        
        # Get updated job
        job_data = await data_service.get_job(job_id)
        
        return JobResponse(
            success=True,
            job_id=job_id,
            job_number=job_data.get("job_number"),
            status="DISPATCHED",
            message="Đã gán xe thành công!"
        )
    except Exception as e:
        logger.error(f"Error assigning vehicle: {e}")
        return JobResponse(
            success=False,
            message=f"Lỗi gán xe: {str(e)}"
        )


@router.post("/{job_id}/complete", response_model=JobResponse)
async def complete_job(job_id: int, delivery_time: Optional[datetime] = None):
    """
    Mark job as completed
    """
    data_service = get_data_service()
    
    # Check job exists
    job_data = await data_service.get_job(job_id)
    if not job_data:
        raise HTTPException(404, f"Job {job_id} not found")
    
    # TODO: Update job status to COMPLETED
    
    return JobResponse(
        success=True,
        job_id=job_id,
        job_number=job_data.get("job_number"),
        status="COMPLETED",
        message="Job đã hoàn thành!"
    )


# NOTE: This route MUST be defined BEFORE /{job_id} to avoid path matching conflict
@router.get("/recent")
async def get_recent_jobs(limit: int = 10):
    """
    Get recent jobs for dashboard
    """
    data_service = get_data_service()
    conn = data_service._get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                j.job_id, j.job_no, j.status_code, j.etd, j.created_at,
                c.customer_code, c.short_name as customer_name,
                js.service_type_code as service_type
            FROM jobs j
            JOIN customers c ON j.customer_id = c.customer_id
            LEFT JOIN job_services js ON j.job_id = js.job_id
            ORDER BY j.created_at DESC
            LIMIT %s
        """, (limit,))
        
        jobs = [dict(row) for row in cursor.fetchall()]
        return {"jobs": jobs}
        
    except Exception as e:
        logger.error(f"Error fetching recent jobs: {e}")
        return {"jobs": []}


@router.get("/{job_id}")
async def get_job(job_id: int):
    """
    Get job details
    """
    data_service = get_data_service()
    job = await data_service.get_job(job_id)
    
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    
    return job


@router.get("/{job_id}/details")
async def get_job_details(job_id: int):
    """
    Get job with all services for detail modal
    """
    data_service = get_data_service()
    conn = data_service._get_connection()
    cursor = conn.cursor()
    
    try:
        # Get job info
        cursor.execute("""
            SELECT j.*, c.short_name as customer_name, c.customer_code
            FROM jobs j
            JOIN customers c ON j.customer_id = c.customer_id
            WHERE j.job_id = %s
        """, (job_id,))
        job = cursor.fetchone()
        
        if not job:
            raise HTTPException(404, f"Job {job_id} not found")
        
        # Get all services for this job
        cursor.execute("""
            SELECT * FROM job_services WHERE job_id = %s ORDER BY svc_id
        """, (job_id,))
        services = [dict(row) for row in cursor.fetchall()]
        
        return {
            "job": dict(job),
            "services": services
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job details: {e}")
        raise HTTPException(500, str(e))


@router.get("/pending/list")
async def list_pending_jobs():
    """
    List pending jobs (waiting for vehicle assignment)
    """
    data_service = get_data_service()
    # TODO: Implement
    return {"jobs": []}


@router.get("/find")
async def find_job(
    job_no: Optional[str] = None,
    invoice: Optional[str] = None,
    bl_awb: Optional[str] = None,
    customer_code: Optional[str] = None,
    date: Optional[str] = None
):
    """
    Find job by job_no, invoice, B/L, or customer+date
    """
    data_service = get_data_service()
    conn = data_service._get_connection()
    cursor = conn.cursor()
    
    try:
        # Priority 1: Job number
        if job_no:
            cursor.execute("""
                SELECT j.*, c.short_name as customer_name
                FROM jobs j
                JOIN customers c ON j.customer_id = c.customer_id
                WHERE j.job_no ILIKE %s
                LIMIT 1
            """, (f"%{job_no}%",))
            job = cursor.fetchone()
            if job:
                return {"found": True, "job": dict(job)}
        
        # Priority 2: Invoice number
        if invoice:
            cursor.execute("""
                SELECT j.*, c.short_name as customer_name
                FROM jobs j
                JOIN customers c ON j.customer_id = c.customer_id
                JOIN job_services js ON js.job_id = j.job_id
                WHERE js.invoice_numbers ILIKE %s
                ORDER BY j.created_at DESC
                LIMIT 1
            """, (f"%{invoice}%",))
            job = cursor.fetchone()
            if job:
                return {"found": True, "job": dict(job)}
        
        # Priority 3: B/L or AWB
        if bl_awb:
            cursor.execute("""
                SELECT j.*, c.short_name as customer_name
                FROM jobs j
                JOIN customers c ON j.customer_id = c.customer_id
                JOIN job_services js ON js.job_id = j.job_id
                WHERE js.bl_awb_no ILIKE %s
                ORDER BY j.created_at DESC
                LIMIT 1
            """, (f"%{bl_awb}%",))
            job = cursor.fetchone()
            if job:
                return {"found": True, "job": dict(job)}
        
        # Priority 4: Customer + date
        if customer_code and date:
            cursor.execute("""
                SELECT j.*, c.short_name as customer_name
                FROM jobs j
                JOIN customers c ON j.customer_id = c.customer_id
                WHERE c.customer_code ILIKE %s AND j.etd = %s
                ORDER BY j.created_at DESC
                LIMIT 1
            """, (f"%{customer_code}%", date))
            job = cursor.fetchone()
            if job:
                return {"found": True, "job": dict(job)}
        
        return {"found": False, "message": "Job not found"}
    except Exception as e:
        logger.error(f"Error finding job: {e}")
        return {"found": False, "message": str(e)}


@router.post("/update")
async def update_job_info(request: Request):
    """
    Update job info and/or status
    """
    data = await request.json()
    entities = data.get("entities", {})
    
    data_service = get_data_service()
    conn = data_service._get_connection()
    cursor = conn.cursor()
    
    try:
        # Find the job first
        job_id = None
        job_no = entities.get("job_number")
        invoice_ref = entities.get("invoice_ref")
        bl_awb_ref = entities.get("bl_awb_ref")
        
        if job_no:
            cursor.execute("SELECT job_id, job_no FROM jobs WHERE job_no ILIKE %s", (f"%{job_no}%",))
            result = cursor.fetchone()
            if result:
                job_id = result["job_id"]
                job_no = result["job_no"]
        
        if not job_id and invoice_ref:
            cursor.execute("""
                SELECT j.job_id, j.job_no FROM jobs j
                JOIN job_services js ON js.job_id = j.job_id
                WHERE js.invoice_numbers ILIKE %s
                LIMIT 1
            """, (f"%{invoice_ref}%",))
            result = cursor.fetchone()
            if result:
                job_id = result["job_id"]
                job_no = result["job_no"]
        
        if not job_id and bl_awb_ref:
            cursor.execute("""
                SELECT j.job_id, j.job_no FROM jobs j
                JOIN job_services js ON js.job_id = j.job_id
                WHERE js.bl_awb_no ILIKE %s
                LIMIT 1
            """, (f"%{bl_awb_ref}%",))
            result = cursor.fetchone()
            if result:
                job_id = result["job_id"]
                job_no = result["job_no"]
        
        if not job_id:
            return {"success": False, "message": "Không tìm thấy job. Vui lòng cung cấp job_number, invoice hoặc B/L."}
        
        # Update status if provided
        new_status = entities.get("new_status")
        if new_status:
            valid_statuses = ["PENDING", "CONFIRMED", "DISPATCHED", "IN_TRANSIT", "DELIVERED", "COMPLETED", "CANCELLED"]
            if new_status.upper() in valid_statuses:
                cursor.execute("UPDATE jobs SET status_code = %s, updated_at = NOW() WHERE job_id = %s", 
                              (new_status.upper(), job_id))
                logger.info(f"Updated job {job_no} status to {new_status}")
        
        # Update job_services fields
        updates = []
        params = []
        
        if entities.get("update_pickup_time"):
            updates.append("scheduled_time = %s")
            params.append(entities["update_pickup_time"])
        
        if entities.get("update_delivery_address"):
            updates.append("dest_address = %s")
            params.append(entities["update_delivery_address"])
        
        if entities.get("update_special_requirements"):
            updates.append("special_requirements = %s")
            params.append(entities["update_special_requirements"])
        
        if entities.get("update_notes"):
            updates.append("special_requirements = COALESCE(special_requirements, '') || ' ' || %s")
            params.append(entities["update_notes"])
        
        # Vehicle info update
        if entities.get("license_plate") or entities.get("driver_name"):
            vendor_text = f"BKS: {entities.get('license_plate', '')} / {entities.get('driver_name', '')} / {entities.get('driver_phone', '')}"
            updates.append("vendor_text_input = %s")
            params.append(vendor_text)
        
        if updates:
            params.append(job_id)
            cursor.execute(f"""
                UPDATE job_services 
                SET {', '.join(updates)}, updated_at = NOW()
                WHERE job_id = %s
            """, params)
        
        conn.commit()
        
        return {
            "success": True,
            "job_id": job_id,
            "job_number": job_no,
            "message": f"Đã cập nhật job {job_no} thành công!"
        }
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating job: {e}")
        return {"success": False, "message": str(e)}


# ========================================
# DASHBOARD ENDPOINTS
# ========================================

# Dashboard stats endpoint - mounted at /api/dashboard/stats in main.py
async def get_dashboard_stats():
    """
    Get dashboard statistics
    """
    data_service = get_data_service()
    conn = data_service._get_connection()
    cursor = conn.cursor()
    
    try:
        # Jobs today
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM jobs 
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        jobs_today = cursor.fetchone()['cnt']
        
        # Active trucking
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM job_services 
            WHERE service_type_code IN ('TRUCKING_SHORT', 'TRUCKING_LONG')
            AND status_code NOT IN ('COMPLETED', 'CANCELLED')
        """)
        trucking_active = cursor.fetchone()['cnt']
        
        # In storage
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM job_services 
            WHERE service_type_code IN ('WHS_STORAGE', 'WHS_HANDLE')
            AND status_code NOT IN ('COMPLETED', 'CANCELLED')
        """)
        warehouse_count = cursor.fetchone()['cnt']
        
        # Status counts for chart - REAL DATA
        cursor.execute("""
            SELECT COALESCE(status_code, 'PENDING') as status, COUNT(*) as cnt 
            FROM job_services 
            GROUP BY status_code
            ORDER BY cnt DESC
        """)
        status_counts = {}
        for row in cursor.fetchall():
            status_counts[row['status']] = row['cnt']
        
        # Revenue MTD (placeholder for now)
        revenue_mtd = "1.2B"
        
        return {
            "jobs_today": jobs_today,
            "trucking": trucking_active,
            "warehouse": warehouse_count,
            "revenue": revenue_mtd,
            "status_counts": status_counts
        }
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return {
            "jobs_today": 0,
            "trucking": 0,
            "warehouse": 0,
            "revenue": "0",
            "status_counts": {}
        }


# Service-specific endpoints - mounted at /api/services/{type} in main.py
async def get_service_data(service_type: str):
    """
    Get service-specific data from views
    """
    data_service = get_data_service()
    conn = data_service._get_connection()
    cursor = conn.cursor()
    
    view_mapping = {
        "trucking": "v_trucking_services",
        "warehouse": "v_warehouse_services",
        "customs": "v_customs_services",
        "packing": "v_packing_services"
    }
    
    view_name = view_mapping.get(service_type)
    if not view_name:
        return {"services": [], "error": f"Unknown service type: {service_type}"}
    
    try:
        cursor.execute(f"SELECT * FROM {view_name} ORDER BY scheduled_date DESC NULLS LAST LIMIT 50")
        services = [dict(row) for row in cursor.fetchall()]
        return {"services": services}
        
    except Exception as e:
        logger.error(f"Error fetching {service_type} services: {e}")
        return {"services": [], "error": str(e)}

