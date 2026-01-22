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
    vendor_name: Optional[str] = None


class JobResponse(BaseModel):
    success: bool = True
    job_id: Optional[int] = None
    job_number: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    enriched_data: Optional[Dict[str, Any]] = None

# Endpoints

@router.get("/by-number/{job_number}")
async def get_job_by_number(job_number: str):
    """
    Get job by job_number (e.g., TRK-2201-0002)
    """
    try:
        data_service = get_data_service()
        conn = data_service._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT job_id, job_no, customer_id, status_code
                FROM jobs 
                WHERE job_no = %s
                LIMIT 1
            """, (job_number,))
            result = cursor.fetchone()
            if result:
                return {
                    "success": True,
                    "job_id": result["job_id"],
                    "id": result["job_id"],
                    "job_number": result["job_no"],
                    "customer_id": result["customer_id"],
                    "status": result["status_code"]
                }
            else:
                return {"success": False, "message": f"Job '{job_number}' not found"}
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        logger.error(f"Error looking up job: {e}")
        return {"success": False, "message": str(e)}

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
        
        # Handle invoice numbers - AI may return 'invoices' or 'invoice_numbers'
        inv_nums = (entities.get('invoice_numbers') or entities.get('invoices') or 
                   enriched.get('invoice_numbers') or enriched.get('invoices'))
        if isinstance(inv_nums, list):
            invoice_numbers = ', '.join(str(i) for i in inv_nums)
        else:
            invoice_numbers = inv_nums
        
        # Resolve customer_id from customer_code if not provided
        customer_id = enriched.get('customer_id')
        customer_code = entities.get('customer_code') or enriched.get('customer_code')
        
        if not customer_id and customer_code:
            # Look up customer by code
            conn = data_service._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT customer_id FROM customers 
                    WHERE customer_code = %s AND is_active = true
                    LIMIT 1
                """, (customer_code,))
                result = cursor.fetchone()
                if result:
                    customer_id = result['customer_id']
                    logger.info(f"Resolved customer '{customer_code}' -> ID {customer_id}")
            finally:
                cursor.close()
                conn.close()
        
        if not customer_id:
            return JobResponse(
                success=False,
                message=f"Không tìm thấy khách hàng '{customer_code}' trong DB. Vui lòng chọn khách hàng đúng."
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
        await data_service.assign_vehicle(job_id, request.dict(), user_id=1)
        
        # Get updated job with full details for frontend template
        # Re-using get_job_details logic to fetch everything needed for the message
        details = await get_job_details(job_id)
        job_info = details["job"]
        services = details["services"]
        
        # Get first service for time/address details (or aggregate if multiple)
        first_service = services[0] if services else {}
        
        # Map fields to match what frontend expects in enriched_data
        enriched = {
            "customer_code": job_info.get("customer_code"),
            "customer_name": job_info.get("customer_name"),
            "booking_date": str(first_service.get("scheduled_date") or job_info.get("etd") or ""),
            "scheduled_date": str(first_service.get("scheduled_date") or job_info.get("etd") or ""),
            "pickup_date": str(first_service.get("scheduled_date") or job_info.get("etd") or ""),
            "pickup_time": str(first_service.get("scheduled_time") or ""),
            "pickup_address": first_service.get("origin_address"),
            "delivery_address": first_service.get("dest_address"),
            "vehicle_type": request.model_dump().get("vehicle_type"),
            "invoice_numbers": [], # Will be populated below
            "cargo_type": "", # Will be populated below
            # Include vehicle info we just assigned
            "license_plate": request.license_plate,
            "driver_name": request.driver_name,
            "driver_phone": request.driver_phone,
            "vendor_name": request.vendor_name 
        }

        # Extract cargo items and invoices from services
        all_cargo_items = []
        invoices = []
        package_quantity = 0
        package_unit = "kiện"
        cargo_descriptions = set()
        dimensions = None
        
        if services:
            for svc in services:
                service_details = svc.get("service_details")
                
                # Parse service_details if it's a string
                if isinstance(service_details, str):
                    try:
                        import json
                        service_details = json.loads(service_details)
                    except:
                        service_details = {}
                
                # Extract invoices from service_details JSONB first
                if isinstance(service_details, dict):
                    if service_details.get("invoice_numbers"):
                        inv_list = service_details["invoice_numbers"]
                        if isinstance(inv_list, str):
                            invoices.extend([i.strip() for i in inv_list.split(",")])
                        elif isinstance(inv_list, list):
                            invoices.extend(inv_list)
                    
                    # Extract cargo items
                    if service_details.get("cargo_items"):
                        all_cargo_items.extend(service_details["cargo_items"])
                    
                    # Aggregate package quantities
                    if service_details.get("package_quantity"):
                        package_quantity += service_details["package_quantity"]
                    
                    if service_details.get("package_unit"):
                        package_unit = service_details["package_unit"]
                    
                    # Collect cargo descriptions
                    if service_details.get("cargo_type"):
                        cargo_descriptions.add(service_details["cargo_type"])
                    
                    # Dimensions
                    if service_details.get("dimension_length_cm"):
                        dimensions = {
                            "length": service_details.get("dimension_length_cm"),
                            "width": service_details.get("dimension_width_cm"),
                            "height": service_details.get("dimension_height_cm")
                        }
                
                # FALLBACK: If service_details is empty, read from columns (for old jobs)
                if not invoices and svc.get("invoice_numbers"):
                    inv_col = svc["invoice_numbers"]
                    if isinstance(inv_col, str):
                        invoices.extend([i.strip() for i in inv_col.split(",") if i.strip()])
                    elif isinstance(inv_col, list):
                        invoices.extend(inv_col)
                
                # FALLBACK: Get addresses from columns if not in enriched yet
                if not enriched.get("pickup_address") and svc.get("origin_address"):
                    enriched["pickup_address"] = svc["origin_address"]
                if not enriched.get("delivery_address") and svc.get("dest_address"):
                    enriched["delivery_address"] = svc["dest_address"]
        
        enriched["invoice_numbers"] = invoices
        enriched["cargo_items"] = all_cargo_items
        enriched["package_quantity"] = package_quantity
        enriched["package_unit"] = package_unit
        
        # If we have cargo items, use their details
        if all_cargo_items:
            # Extract invoices from cargo_items  
            for item in all_cargo_items:
                if item.get("invoice_no") and item["invoice_no"] not in invoices:
                    invoices.append(item["invoice_no"])
            enriched["invoice_numbers"] = invoices  # Update with cargo item invoices
            
            cargo_desc = ", ".join(set(item.get("description", "") for item in all_cargo_items if item.get("description")))
            enriched["cargo_type"] = cargo_desc or list(cargo_descriptions)[0] if cargo_descriptions else ""
        elif cargo_descriptions:
            enriched["cargo_type"] = ", ".join(cargo_descriptions)
        
        if dimensions:
            enriched["dimensions"] = dimensions
        
        # Important: The frontend checks `msg.entities.cargo_items` OR `msg.enriched_data`.
        # We should put cargo info in enriched_data.
        
        return JobResponse(
            success=True,
            job_id=job_id,
            job_number=job_data.get("job_number"),
            status="DISPATCHED",
            message="Đã gán xe thành công!",
            enriched_data=enriched
        )
    except Exception as e:
        logger.error(f"Error assigning vehicle: {e}")
        logger.error(traceback.format_exc())
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
    Returns complete job info with vendor/employee names
    """
    data_service = get_data_service()
    conn = data_service._get_connection()
    cursor = conn.cursor()
    
    try:
        # Get job info with customer details
        cursor.execute("""
            SELECT j.*, 
                   c.short_name as customer_name, 
                   c.customer_code,
                   c.company_name as customer_full_name,
                   j.status_code as status_display
            FROM jobs j
            LEFT JOIN customers c ON j.customer_id = c.customer_id
            WHERE j.job_id = %s
        """, (job_id,))
        job = cursor.fetchone()

        
        if not job:
            raise HTTPException(404, f"Job {job_id} not found")
        
        # Get all services with vendor/employee details
        cursor.execute("""
            SELECT js.*,
                   v.short_name as vendor_name,
                   v.company_name as vendor_full_name,
                   e.full_name as employee_name,
                   js.service_type_code as service_type_name
            FROM job_services js
            LEFT JOIN vendors v ON js.vendor_id = v.vendor_id
            LEFT JOIN employees e ON js.employee_id = e.employee_id
            WHERE js.job_id = %s 
            ORDER BY js.svc_id
        """, (job_id,))
        services = [dict(row) for row in cursor.fetchall()]
        
        # Parse vendor_text_input for vehicle info
        import json # Added import for json
        for svc in services:
            if svc.get('vendor_text_input'):
                try:
                    vehicle_data = svc['vendor_text_input']
                    if isinstance(vehicle_data, str):
                        vehicle_data = json.loads(vehicle_data)
                    
                    if isinstance(vehicle_data, dict):
                        svc['license_plate'] = vehicle_data.get('license_plate')
                        svc['driver_name'] = vehicle_data.get('driver_name')
                        svc['driver_phone'] = vehicle_data.get('driver_phone')
                        
                        # Only show vehicle info as vendor name if NO vendor_id assigned
                        if not svc.get('vendor_id') and svc.get('license_plate'):
                             svc['vendor_name'] = f"{svc['license_plate']}"
                             if svc.get('driver_name'):
                                 svc['vendor_name'] += f" - {svc['driver_name']}"
                except Exception as e:
                    logger.error(f"Error parsing vendor_text_input for svc {svc.get('svc_id')}: {e}")

        
        # Get job costs if available
        costs = []
        try:
            cursor.execute("""
                SELECT jc.*,
                       v.short_name as vendor_name
                FROM job_costs jc
                LEFT JOIN vendors v ON jc.vendor_id = v.vendor_id
                WHERE jc.job_id = %s
                ORDER BY jc.cost_id
            """, (job_id,))
            costs = [dict(row) for row in cursor.fetchall()]
        except Exception:
            pass  # job_costs table might not exist yet
        
        return {
            "job": dict(job),
            "services": services,
            "costs": costs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job details: {e}")
        raise HTTPException(500, str(e))
    finally:
        cursor.close()
        conn.close()



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
        if service_type == "trucking":
            # For trucking, use direct query to ensure LEFT JOINs and include vendor_text_input
            cursor.execute("""
                SELECT 
                    js.*,
                    j.job_no,
                    c.customer_code,
                    COALESCE(c.short_name, c.company_name) as customer,
                    js.vendor_text_input,
                    v.short_name as vendor_name,
                    e.full_name as employee_name,
                    CASE 
                        WHEN js.vendor_id IS NOT NULL THEN 'VENDOR'
                        WHEN js.employee_id IS NOT NULL THEN 'EMPLOYEE'
                        ELSE 'UNASSIGNED'
                    END as assignment_type,
                    COALESCE(v.short_name, e.full_name) as assigned_to
                FROM job_services js
                JOIN jobs j ON js.job_id = j.job_id
                LEFT JOIN customers c ON j.customer_id = c.customer_id
                LEFT JOIN vendors v ON js.vendor_id = v.vendor_id
                LEFT JOIN employees e ON js.employee_id = e.employee_id
                WHERE js.service_type_code IN ('TRUCKING_SHORT', 'TRUCKING_LONG')
                ORDER BY js.scheduled_date DESC NULLS LAST
                LIMIT 50
            """)
        else:
            # For others, use existing views
            cursor.execute(f"SELECT * FROM {view_name} ORDER BY scheduled_date DESC NULLS LAST LIMIT 50")
            
        services = [dict(row) for row in cursor.fetchall()]
        
        # Parse vehicle info for trucking services
        if service_type == "trucking":
             import json
             for svc in services:
                # Check if vendor_text_input exists
                if svc.get('vendor_text_input'):
                    try:
                        vehicle_data = svc['vendor_text_input']
                        if isinstance(vehicle_data, str):
                            vehicle_data = json.loads(vehicle_data)
                        
                        if isinstance(vehicle_data, dict):
                            svc['license_plate'] = vehicle_data.get('license_plate')
                            svc['driver_name'] = vehicle_data.get('driver_name')
                            
                            # Update vendor_name/assigned_to if key fields missing 
                            # (checking both vendor_name and assigned_to to cover view/query differences)
                            if not svc.get('assigned_to') and svc.get('license_plate'):
                                info = f"{svc['license_plate']}"
                                if svc.get('driver_name'):
                                    info += f" - {svc['driver_name']}"
                                
                                svc['assigned_to'] = info
                                svc['assignment_type'] = 'VENDOR' # Show as vendor assignment
                                
                    except Exception as e:
                        logger.error(f"Error parsing vendor_text_input: {e}")
        
        return {"services": services}
        
    except Exception as e:
        logger.error(f"Error fetching {service_type} services: {e}")
        return {"services": [], "error": str(e)}


# ========================================
# EXCEL EXPORT ENDPOINT
# ========================================

@router.get("/export/{service_type}")
async def export_services_excel(
    service_type: str,
    customer_id: Optional[int] = None,
    vendor_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    month: Optional[str] = None  # Format: 2026-01
):
    """
    Export services to Excel with filters
    Returns Excel file download
    """
    from fastapi.responses import FileResponse
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from io import BytesIO
    import tempfile
    import os
    
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
        raise HTTPException(400, f"Unknown service type: {service_type}")
    
    try:
        # Build query with filters
        query = f"SELECT * FROM {view_name} WHERE 1=1"
        params = []
        
        if customer_id:
            query += " AND customer_id = %s"
            params.append(customer_id)
        
        if vendor_id:
            query += " AND vendor_id = %s"
            params.append(vendor_id)
        
        if month:
            # month format: 2026-01
            query += " AND TO_CHAR(scheduled_date, 'YYYY-MM') = %s"
            params.append(month)
        else:
            if from_date:
                query += " AND scheduled_date >= %s"
                params.append(from_date)
            if to_date:
                query += " AND scheduled_date <= %s"
                params.append(to_date)
        
        query += " ORDER BY scheduled_date DESC"
        
        cursor.execute(query, params)
        services = cursor.fetchall()
        
        if not services:
            raise HTTPException(404, "Không có dữ liệu để xuất")
        
        # Create Excel workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"{service_type.capitalize()} Services"
        
        # Styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
        header_align = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Get column names from first row
        columns = list(services[0].keys()) if services else []
        
        # Write headers
        for col_idx, col_name in enumerate(columns, 1):
            cell = ws.cell(row=1, column=col_idx, value=col_name)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align
            cell.border = thin_border
        
        # Write data
        for row_idx, row in enumerate(services, 2):
            for col_idx, col_name in enumerate(columns, 1):
                value = row[col_name]
                # Convert special types
                if isinstance(value, (date, datetime)):
                    value = value.strftime('%Y-%m-%d')
                elif isinstance(value, time):
                    value = value.strftime('%H:%M')
                
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = thin_border
        
        # Auto-adjust column widths
        for col_idx, col_name in enumerate(columns, 1):
            max_length = len(str(col_name))
            for row in services[:50]:  # Check first 50 rows
                val = row.get(col_name)
                if val:
                    max_length = max(max_length, len(str(val)))
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = min(max_length + 2, 50)
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        wb.save(temp_file.name)
        temp_file.close()
        
        # Generate filename
        filename = f"{service_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return FileResponse(
            path=temp_file.name,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            background=None  # Cleanup handled by FileResponse
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting {service_type} services: {e}")
        raise HTTPException(500, f"Export error: {str(e)}")
    finally:
        cursor.close()
        conn.close()
