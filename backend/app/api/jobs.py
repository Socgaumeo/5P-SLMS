"""
Jobs API - Job management endpoints
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import date, time, datetime
import logging
import traceback
import json

from app.services.data_service import get_data_service
from app.ai.utils.smart_parser import parse_date, parse_time
from app.services.message_service import get_message_service
from app.db.supabase_client import get_supabase

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
        client = get_supabase()
        result = client.table('jobs').select(
            'job_id, job_no, customer_id, status_code'
        ).eq('job_no', job_number).limit(1).execute()

        if result.data:
            row = result.data[0]
            return {
                "success": True,
                "job_id": row["job_id"],
                "id": row["job_id"],
                "job_number": row["job_no"],
                "customer_id": row["customer_id"],
                "status": row["status_code"]
            }
        else:
            return {"success": False, "message": f"Job '{job_number}' not found"}
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
        
        # Parse booking date (smart parser handles multiple formats: dd.mm.yyyy, yyyy-mm-dd, etc.)
        booking_date_str = entities.get('booking_date') or enriched.get('booking_date')
        if booking_date_str:
            parsed = parse_date(booking_date_str)
            booking_date = parsed if parsed else date.today()
        else:
            booking_date = date.today()

        # Parse pickup time (smart parser handles: 11:00, 11h00, 11 giờ 30, etc.)
        pickup_time_str = entities.get('pickup_time') or enriched.get('pickup_time')
        pickup_time = parse_time(pickup_time_str) if pickup_time_str else None
        
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
            client = get_supabase()
            result = client.table('customers').select('customer_id').eq(
                'customer_code', customer_code
            ).eq('is_active', True).limit(1).execute()

            if result.data:
                customer_id = result.data[0]['customer_id']
                logger.info(f"Resolved customer '{customer_code}' -> ID {customer_id}")
        
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
    try:
        client = get_supabase()
        # Use RPC for complex join query or fetch separately
        # Fetch jobs with customer info
        result = client.table('jobs').select(
            'job_id, job_no, status_code, etd, created_at, customer_id, '
            'customers(customer_code, short_name)'
        ).order('created_at', desc=True).limit(limit).execute()

        jobs = []
        for row in result.data:
            customer = row.get('customers') or {}
            jobs.append({
                'job_id': row['job_id'],
                'job_no': row['job_no'],
                'status_code': row['status_code'],
                'etd': row['etd'],
                'created_at': row['created_at'],
                'customer_code': customer.get('customer_code'),
                'customer_name': customer.get('short_name')
            })

        # Get service types for each job
        if jobs:
            job_ids = [j['job_id'] for j in jobs]
            svc_result = client.table('job_services').select(
                'job_id, service_type_code'
            ).in_('job_id', job_ids).execute()

            svc_map = {}
            for svc in svc_result.data:
                if svc['job_id'] not in svc_map:
                    svc_map[svc['job_id']] = svc['service_type_code']

            for job in jobs:
                job['service_type'] = svc_map.get(job['job_id'])

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
    try:
        client = get_supabase()

        # Get job info with customer details
        job_result = client.table('jobs').select(
            '*, customers(short_name, customer_code, company_name)'
        ).eq('job_id', job_id).limit(1).execute()

        if not job_result.data:
            raise HTTPException(404, f"Job {job_id} not found")

        job_row = job_result.data[0]
        customer = job_row.pop('customers', {}) or {}
        job = {
            **job_row,
            'customer_name': customer.get('short_name'),
            'customer_code': customer.get('customer_code'),
            'customer_full_name': customer.get('company_name'),
            'status_display': job_row.get('status_code')
        }

        # Get all services with vendor/employee details
        svc_result = client.table('job_services').select(
            '*, vendors(short_name, company_name), employees(full_name)'
        ).eq('job_id', job_id).order('svc_id').execute()

        services = []
        for row in svc_result.data:
            vendor = row.pop('vendors', {}) or {}
            employee = row.pop('employees', {}) or {}
            svc = {
                **row,
                'vendor_name': vendor.get('short_name'),
                'vendor_full_name': vendor.get('company_name'),
                'employee_name': employee.get('full_name'),
                'service_type_name': row.get('service_type_code')
            }

            # Parse vendor_text_input for vehicle info
            if svc.get('vendor_text_input'):
                try:
                    vehicle_data = svc['vendor_text_input']
                    if isinstance(vehicle_data, str):
                        vehicle_data = json.loads(vehicle_data)

                    if isinstance(vehicle_data, dict):
                        svc['license_plate'] = vehicle_data.get('license_plate')
                        svc['driver_name'] = vehicle_data.get('driver_name')
                        svc['driver_phone'] = vehicle_data.get('driver_phone')
                        svc['driver_id_card'] = vehicle_data.get('driver_id_card')

                        # Only show vehicle info as vendor name if NO vendor_id assigned
                        if not svc.get('vendor_id') and svc.get('license_plate'):
                            svc['vendor_name'] = f"{svc['license_plate']}"
                            if svc.get('driver_name'):
                                svc['vendor_name'] += f" - {svc['driver_name']}"
                except Exception as e:
                    logger.error(f"Error parsing vendor_text_input for svc {svc.get('svc_id')}: {e}")

            # Parse service_details JSONB for invoice/quantity/cargo info
            if svc.get('service_details'):
                try:
                    details = svc['service_details']
                    if isinstance(details, str):
                        details = json.loads(details)

                    if isinstance(details, dict):
                        # Extract invoice_numbers
                        inv = details.get('invoice_numbers')
                        if inv and not svc.get('invoice_numbers'):
                            if isinstance(inv, list):
                                svc['invoice_numbers'] = ', '.join(str(i) for i in inv)
                            else:
                                svc['invoice_numbers'] = inv

                        # Extract package quantity and unit
                        if details.get('package_quantity') and not svc.get('package_quantity'):
                            svc['package_quantity'] = details['package_quantity']
                        if details.get('package_unit') and not svc.get('package_unit'):
                            svc['package_unit'] = details['package_unit']

                        # Extract cargo_type
                        if details.get('cargo_type') and not svc.get('cargo_type'):
                            svc['cargo_type'] = details['cargo_type']
                except Exception as e:
                    logger.error(f"Error parsing service_details for svc {svc.get('svc_id')}: {e}")

            services.append(svc)

        # Get job costs if available
        costs = []
        try:
            costs_result = client.table('job_costs').select(
                '*, vendors(short_name)'
            ).eq('job_id', job_id).order('cost_id').execute()

            for row in costs_result.data:
                vendor = row.pop('vendors', {}) or {}
                costs.append({
                    **row,
                    'vendor_name': vendor.get('short_name')
                })
        except Exception:
            pass  # job_costs table might not exist yet

        return {
            "job": job,
            "services": services,
            "costs": costs
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
    try:
        client = get_supabase()

        # Priority 1: Job number
        if job_no:
            result = client.table('jobs').select(
                '*, customers(short_name)'
            ).ilike('job_no', f'%{job_no}%').limit(1).execute()

            if result.data:
                job = result.data[0]
                customer = job.pop('customers', {}) or {}
                job['customer_name'] = customer.get('short_name')
                return {"found": True, "job": job}

        # Priority 2: Invoice number - need to search in job_services
        if invoice:
            svc_result = client.table('job_services').select(
                'job_id'
            ).ilike('invoice_numbers', f'%{invoice}%').limit(1).execute()

            if svc_result.data:
                job_id = svc_result.data[0]['job_id']
                result = client.table('jobs').select(
                    '*, customers(short_name)'
                ).eq('job_id', job_id).limit(1).execute()

                if result.data:
                    job = result.data[0]
                    customer = job.pop('customers', {}) or {}
                    job['customer_name'] = customer.get('short_name')
                    return {"found": True, "job": job}

        # Priority 3: B/L or AWB
        if bl_awb:
            svc_result = client.table('job_services').select(
                'job_id'
            ).ilike('bl_awb_no', f'%{bl_awb}%').limit(1).execute()

            if svc_result.data:
                job_id = svc_result.data[0]['job_id']
                result = client.table('jobs').select(
                    '*, customers(short_name)'
                ).eq('job_id', job_id).limit(1).execute()

                if result.data:
                    job = result.data[0]
                    customer = job.pop('customers', {}) or {}
                    job['customer_name'] = customer.get('short_name')
                    return {"found": True, "job": job}

        # Priority 4: Customer + date
        if customer_code and date:
            # First find customer
            cust_result = client.table('customers').select(
                'customer_id'
            ).ilike('customer_code', f'%{customer_code}%').limit(1).execute()

            if cust_result.data:
                cust_id = cust_result.data[0]['customer_id']
                result = client.table('jobs').select(
                    '*, customers(short_name)'
                ).eq('customer_id', cust_id).eq('etd', date).order(
                    'created_at', desc=True
                ).limit(1).execute()

                if result.data:
                    job = result.data[0]
                    customer = job.pop('customers', {}) or {}
                    job['customer_name'] = customer.get('short_name')
                    return {"found": True, "job": job}

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

    try:
        client = get_supabase()

        # Find the job first
        job_id = None
        job_no = entities.get("job_number")
        invoice_ref = entities.get("invoice_ref")
        bl_awb_ref = entities.get("bl_awb_ref")

        if job_no:
            result = client.table('jobs').select(
                'job_id, job_no'
            ).ilike('job_no', f'%{job_no}%').limit(1).execute()

            if result.data:
                job_id = result.data[0]["job_id"]
                job_no = result.data[0]["job_no"]

        if not job_id and invoice_ref:
            svc_result = client.table('job_services').select(
                'job_id'
            ).ilike('invoice_numbers', f'%{invoice_ref}%').limit(1).execute()

            if svc_result.data:
                job_id = svc_result.data[0]["job_id"]
                job_result = client.table('jobs').select('job_no').eq('job_id', job_id).limit(1).execute()
                if job_result.data:
                    job_no = job_result.data[0]["job_no"]

        if not job_id and bl_awb_ref:
            svc_result = client.table('job_services').select(
                'job_id'
            ).ilike('bl_awb_no', f'%{bl_awb_ref}%').limit(1).execute()

            if svc_result.data:
                job_id = svc_result.data[0]["job_id"]
                job_result = client.table('jobs').select('job_no').eq('job_id', job_id).limit(1).execute()
                if job_result.data:
                    job_no = job_result.data[0]["job_no"]

        if not job_id:
            return {"success": False, "message": "Không tìm thấy job. Vui lòng cung cấp job_number, invoice hoặc B/L."}

        # Update status if provided
        new_status = entities.get("new_status")
        if new_status:
            valid_statuses = ["PENDING", "CONFIRMED", "DISPATCHED", "IN_TRANSIT", "DELIVERED", "COMPLETED", "CANCELLED"]
            if new_status.upper() in valid_statuses:
                client.table('jobs').update({
                    'status_code': new_status.upper(),
                    'updated_at': datetime.now().isoformat()
                }).eq('job_id', job_id).execute()
                logger.info(f"Updated job {job_no} status to {new_status}")

        # Update job_services fields
        svc_updates = {}

        if entities.get("update_pickup_time"):
            svc_updates['scheduled_time'] = entities["update_pickup_time"]

        if entities.get("update_delivery_address"):
            svc_updates['dest_address'] = entities["update_delivery_address"]

        if entities.get("update_special_requirements"):
            svc_updates['special_requirements'] = entities["update_special_requirements"]

        # Vehicle info update
        if entities.get("license_plate") or entities.get("driver_name"):
            vendor_text = json.dumps({
                'license_plate': entities.get('license_plate', ''),
                'driver_name': entities.get('driver_name', ''),
                'driver_phone': entities.get('driver_phone', '')
            })
            svc_updates['vendor_text_input'] = vendor_text

        if svc_updates:
            svc_updates['updated_at'] = datetime.now().isoformat()
            client.table('job_services').update(svc_updates).eq('job_id', job_id).execute()

        # Handle update_notes separately (append to special_requirements)
        if entities.get("update_notes"):
            # Get current special_requirements
            current = client.table('job_services').select(
                'svc_id, special_requirements'
            ).eq('job_id', job_id).execute()

            for svc in current.data:
                current_req = svc.get('special_requirements') or ''
                new_req = f"{current_req} {entities['update_notes']}".strip()
                client.table('job_services').update({
                    'special_requirements': new_req,
                    'updated_at': datetime.now().isoformat()
                }).eq('svc_id', svc['svc_id']).execute()

        return {
            "success": True,
            "job_id": job_id,
            "job_number": job_no,
            "message": f"Đã cập nhật job {job_no} thành công!"
        }

    except Exception as e:
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
    try:
        client = get_supabase()
        today = date.today().isoformat()

        # Jobs today - count jobs created today
        jobs_result = client.table('jobs').select(
            'job_id', count='exact'
        ).gte('created_at', f'{today}T00:00:00').execute()
        jobs_today = jobs_result.count or 0

        # Active trucking
        trucking_result = client.table('job_services').select(
            'svc_id', count='exact'
        ).in_('service_type_code', ['TRUCKING_SHORT', 'TRUCKING_LONG']).not_.in_(
            'status_code', ['COMPLETED', 'CANCELLED']
        ).execute()
        trucking_active = trucking_result.count or 0

        # In storage (warehouse)
        warehouse_result = client.table('job_services').select(
            'svc_id', count='exact'
        ).in_('service_type_code', ['WHS_STORAGE', 'WHS_HANDLE']).not_.in_(
            'status_code', ['COMPLETED', 'CANCELLED']
        ).execute()
        warehouse_count = warehouse_result.count or 0

        # Status counts for chart - fetch all and group in Python
        status_result = client.table('job_services').select('status_code').execute()
        status_counts = {}
        for row in status_result.data:
            status = row.get('status_code') or 'PENDING'
            status_counts[status] = status_counts.get(status, 0) + 1

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
    service_type_codes = {
        "trucking": ['TRUCKING_SHORT', 'TRUCKING_LONG'],
        "warehouse": ['WHS_STORAGE', 'WHS_HANDLE'],
        "customs": ['CUS_IMPORT', 'CUS_EXPORT', 'CUS_TRANSIT'],
        "packing": ['SVC_PACK', 'SVC_SHRINK_WRAP', 'SVC_VACUUM', 'SVC_LASHING', 'SVC_FUMIGATION']
    }

    codes = service_type_codes.get(service_type)
    if not codes:
        return {"services": [], "error": f"Unknown service type: {service_type}"}

    try:
        client = get_supabase()

        # Query job_services with related data
        result = client.table('job_services').select(
            '*, jobs(job_no, customer_id, customers(customer_code, short_name, company_name)), '
            'vendors(short_name), employees(full_name)'
        ).in_('service_type_code', codes).order(
            'scheduled_date', desc=True, nullsfirst=False
        ).limit(50).execute()

        services = []
        for row in result.data:
            job = row.pop('jobs', {}) or {}
            vendor = row.pop('vendors', {}) or {}
            employee = row.pop('employees', {}) or {}
            customer = job.pop('customers', {}) or {} if job else {}

            # Determine assignment type
            if row.get('vendor_id'):
                assignment_type = 'VENDOR'
                assigned_to = vendor.get('short_name')
            elif row.get('employee_id'):
                assignment_type = 'EMPLOYEE'
                assigned_to = employee.get('full_name')
            else:
                assignment_type = 'UNASSIGNED'
                assigned_to = None

            svc = {
                **row,
                'job_no': job.get('job_no'),
                'customer_code': customer.get('customer_code'),
                'customer': customer.get('short_name') or customer.get('company_name'),
                'vendor_name': vendor.get('short_name'),
                'employee_name': employee.get('full_name'),
                'assignment_type': assignment_type,
                'assigned_to': assigned_to
            }

            # Parse vehicle info for trucking services
            if service_type == "trucking" and svc.get('vendor_text_input'):
                try:
                    vehicle_data = svc['vendor_text_input']
                    if isinstance(vehicle_data, str):
                        vehicle_data = json.loads(vehicle_data)

                    if isinstance(vehicle_data, dict):
                        svc['license_plate'] = vehicle_data.get('license_plate')
                        svc['driver_name'] = vehicle_data.get('driver_name')

                        # Update assigned_to if no vendor assigned
                        if not svc.get('assigned_to') and svc.get('license_plate'):
                            info = f"{svc['license_plate']}"
                            if svc.get('driver_name'):
                                info += f" - {svc['driver_name']}"

                            svc['assigned_to'] = info
                            svc['assignment_type'] = 'VENDOR'

                except Exception as e:
                    logger.error(f"Error parsing vendor_text_input: {e}")

            services.append(svc)

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
    Returns Excel file with structured fields (extracted from JSON) for payment reconciliation
    """
    from fastapi.responses import FileResponse
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    import tempfile

    if service_type not in ["trucking", "warehouse", "customs", "packing"]:
        raise HTTPException(400, f"Unknown service type: {service_type}")

    service_type_codes = {
        "trucking": ['TRUCKING_SHORT', 'TRUCKING_LONG'],
        "warehouse": ['WHS_STORAGE', 'WHS_HANDLE'],
        "customs": ['CUS_IMPORT', 'CUS_EXPORT', 'CUS_TRANSIT'],
        "packing": ['SVC_PACK', 'SVC_SHRINK_WRAP', 'SVC_VACUUM', 'SVC_LASHING', 'SVC_FUMIGATION']
    }

    try:
        client = get_supabase()

        # Build query with Supabase SDK
        query = client.table('job_services').select(
            '*, jobs(job_no, customer_id, customers(customer_code, short_name)), vendors(short_name, company_name)'
        ).in_('service_type_code', service_type_codes[service_type])

        # Apply filters
        if vendor_id:
            query = query.eq('vendor_id', vendor_id)

        if month:
            # Filter by month (YYYY-MM format)
            year, mon = month.split('-')
            start_date = f"{year}-{mon}-01"
            # Calculate end of month
            import calendar
            last_day = calendar.monthrange(int(year), int(mon))[1]
            end_date = f"{year}-{mon}-{last_day}"
            query = query.gte('scheduled_date', start_date).lte('scheduled_date', end_date)
        else:
            if from_date:
                query = query.gte('scheduled_date', from_date)
            if to_date:
                query = query.lte('scheduled_date', to_date)

        query = query.order('scheduled_date', desc=True)
        result = query.execute()

        # Filter by customer_id in Python (since it's in the joined table)
        raw_data = result.data
        if customer_id:
            raw_data = [r for r in raw_data if r.get('jobs', {}).get('customer_id') == customer_id]

        if not raw_data:
            raise HTTPException(404, "Không có dữ liệu để xuất")

        # Transform data based on service type
        services = []
        for row in raw_data:
            job = row.get('jobs') or {}
            vendor = row.get('vendors') or {}
            customer = job.get('customers') or {}

            # Parse JSON fields
            service_details = row.get('service_details') or {}
            if isinstance(service_details, str):
                try:
                    service_details = json.loads(service_details)
                except:
                    service_details = {}

            vendor_text = row.get('vendor_text_input') or {}
            if isinstance(vendor_text, str):
                try:
                    vendor_text = json.loads(vendor_text)
                except:
                    vendor_text = {}

            if service_type == "trucking":
                svc = {
                    'job_no': job.get('job_no'),
                    'customer_code': customer.get('customer_code'),
                    'customer_name': customer.get('short_name'),
                    'ngay_thuc_hien': row.get('scheduled_date'),
                    'gio_lay_hang': row.get('scheduled_time'),
                    'diem_di': row.get('origin_address'),
                    'diem_den': row.get('dest_address'),
                    'loai_hang': row.get('cargo_type'),
                    'so_kien': service_details.get('package_quantity') or row.get('package_quantity'),
                    'don_vi': service_details.get('package_unit') or row.get('package_unit'),
                    'trong_luong_kg': row.get('weight_kg'),
                    'invoice': service_details.get('invoice_numbers') or row.get('invoice_numbers'),
                    'bien_so_xe': vendor_text.get('license_plate') if isinstance(vendor_text, dict) else None,
                    'ten_tai_xe': vendor_text.get('driver_name') if isinstance(vendor_text, dict) else None,
                    'sdt_tai_xe': vendor_text.get('driver_phone') if isinstance(vendor_text, dict) else None,
                    'cccd_tai_xe': vendor_text.get('driver_id_card') if isinstance(vendor_text, dict) else None,
                    'nha_van_chuyen': vendor.get('short_name'),
                    'ten_cong_ty_vc': vendor.get('company_name'),
                    'trang_thai': row.get('status_code'),
                    'ngay_tao': row.get('created_at'),
                    'ngay_cap_nhat': row.get('updated_at')
                }
            elif service_type == "warehouse":
                svc = {
                    'job_no': job.get('job_no'),
                    'customer_code': customer.get('customer_code'),
                    'customer_name': customer.get('short_name'),
                    'scheduled_date': row.get('scheduled_date'),
                    'ngay_bat_dau': row.get('storage_start_date'),
                    'ngay_ket_thuc': row.get('storage_end_date'),
                    'loai_hang': row.get('cargo_type'),
                    'so_kien': row.get('package_quantity'),
                    'don_vi': row.get('package_unit'),
                    'trong_luong_kg': row.get('weight_kg'),
                    'dai_cm': row.get('dimension_length_cm'),
                    'rong_cm': row.get('dimension_width_cm'),
                    'cao_cm': row.get('dimension_height_cm'),
                    'yeu_cau_dac_biet': row.get('special_requirements'),
                    'nha_cung_cap': vendor.get('short_name'),
                    'trang_thai': row.get('status_code'),
                    'ngay_tao': row.get('created_at')
                }
            elif service_type == "customs":
                svc = {
                    'job_no': job.get('job_no'),
                    'customer_code': customer.get('customer_code'),
                    'customer_name': customer.get('short_name'),
                    'scheduled_date': row.get('scheduled_date'),
                    'so_to_khai': row.get('declaration_no'),
                    'ngay_to_khai': row.get('declaration_datetime'),
                    'loai_hinh': row.get('loai_hinh'),
                    'loai_hai_quan': row.get('customs_type'),
                    'cua_khau': row.get('customs_port'),
                    'nguoi_mua': row.get('buyer_name'),
                    'nguoi_ban': row.get('seller_name'),
                    'hs_code': row.get('hs_code'),
                    'so_van_don': row.get('bl_awb_no'),
                    'so_co': row.get('co_no'),
                    'nha_cung_cap': vendor.get('short_name'),
                    'trang_thai': row.get('status_code'),
                    'ngay_tao': row.get('created_at')
                }
            else:  # packing
                svc = {
                    'job_no': job.get('job_no'),
                    'customer_code': customer.get('customer_code'),
                    'customer_name': customer.get('short_name'),
                    'scheduled_date': row.get('scheduled_date'),
                    'loai_dong_goi': row.get('packing_type'),
                    'so_mat_hang': row.get('items_count'),
                    'so_kien_xuat': row.get('packages_output'),
                    'dai_truoc_cm': row.get('before_length_cm'),
                    'rong_truoc_cm': row.get('before_width_cm'),
                    'cao_truoc_cm': row.get('before_height_cm'),
                    'dai_sau_cm': row.get('after_length_cm'),
                    'rong_sau_cm': row.get('after_width_cm'),
                    'cao_sau_cm': row.get('after_height_cm'),
                    'co_shrink_wrap': row.get('shrink_wrap'),
                    'co_hut_chan_khong': row.get('vacuum_pack'),
                    'co_chong_buoc': row.get('lashing'),
                    'co_xong_khu_trung': row.get('fumigation'),
                    'nha_cung_cap': vendor.get('short_name'),
                    'trang_thai': row.get('status_code'),
                    'ngay_tao': row.get('created_at')
                }

            services.append(svc)

        # Create Excel workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"{service_type.capitalize()} Export"

        # Styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
        header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # Get column names from first row
        columns = list(services[0].keys()) if services else []

        # Vietnamese header mapping for better readability
        vn_headers = {
            'job_no': 'Mã Job',
            'customer_code': 'Mã KH',
            'customer_name': 'Tên KH',
            'ngay_thuc_hien': 'Ngày TH',
            'gio_lay_hang': 'Giờ lấy',
            'diem_di': 'Điểm đi',
            'diem_den': 'Điểm đến',
            'loai_hang': 'Loại hàng',
            'so_kien': 'Số kiện',
            'don_vi': 'Đơn vị',
            'trong_luong_kg': 'KL (kg)',
            'invoice': 'Invoice',
            'bien_so_xe': 'Biển số xe',
            'ten_tai_xe': 'Tài xế',
            'sdt_tai_xe': 'SĐT tài xế',
            'cccd_tai_xe': 'CCCD',
            'nha_van_chuyen': 'NVC',
            'ten_cong_ty_vc': 'Công ty VC',
            'trang_thai': 'Trạng thái',
            'ngay_tao': 'Ngày tạo',
            'ngay_cap_nhat': 'Cập nhật'
        }

        # Write headers
        for col_idx, col_name in enumerate(columns, 1):
            header_text = vn_headers.get(col_name, col_name.replace('_', ' ').title())
            cell = ws.cell(row=1, column=col_idx, value=header_text)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align
            cell.border = thin_border

        # Write data
        for row_idx, row in enumerate(services, 2):
            for col_idx, col_name in enumerate(columns, 1):
                value = row.get(col_name)
                # Convert special types
                if isinstance(value, (date, datetime)):
                    value = value.strftime('%Y-%m-%d') if hasattr(value, 'strftime') else str(value)
                elif isinstance(value, time):
                    value = value.strftime('%H:%M') if hasattr(value, 'strftime') else str(value)
                # Parse JSON array for invoice_numbers
                elif col_name == 'invoice' and value:
                    if isinstance(value, list):
                        value = ', '.join(str(i) for i in value)
                    elif isinstance(value, str) and value.startswith('['):
                        try:
                            inv_list = json.loads(value)
                            value = ', '.join(str(i) for i in inv_list)
                        except:
                            pass

                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = thin_border

        # Auto-adjust column widths
        for col_idx, col_name in enumerate(columns, 1):
            max_length = len(vn_headers.get(col_name, col_name))
            for row in services[:50]:  # Check first 50 rows
                val = row.get(col_name)
                if val:
                    max_length = max(max_length, min(len(str(val)), 40))
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = min(max_length + 2, 50)

        # Freeze header row
        ws.freeze_panes = 'A2'

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
        logger.error(traceback.format_exc())
        raise HTTPException(500, f"Export error: {str(e)}")
