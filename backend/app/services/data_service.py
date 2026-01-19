"""
Data Service - Database lookups and enrichment
"""

import logging
from typing import Optional, Dict, Any
from datetime import date
import json
import traceback
import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import settings

logger = logging.getLogger(__name__)


class DataService:
    """Service for database operations and data enrichment"""
    
    def __init__(self):
        self.db_url = settings.DATABASE_URL
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
    
    async def enrich_entities(
        self,
        intent: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrich extracted entities with database lookups
        """
        enriched = dict(entities)
        
        try:
            if intent == "CREATE_JOB":
                enriched = await self._enrich_create_job(entities)
            elif intent == "UPDATE_JOB":
                enriched = await self._enrich_update_job(entities)
            elif intent == "ASSIGN_VEHICLE":
                enriched = await self._enrich_assign_vehicle(entities)
        except Exception as e:
            logger.error(f"Enrichment error: {e}")
            enriched["enrichment_error"] = str(e)
        
        return enriched
    
    async def _enrich_create_job(self, entities: Dict) -> Dict:
        """Enrich CREATE_JOB entities"""
        enriched = dict(entities)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Lookup customer
            customer_code = entities.get("customer_code")
            enriched["customer_matched"] = False  # Track if customer was found
            
            if customer_code:
                cursor.execute("""
                    SELECT customer_id, customer_code, company_name, short_name
                    FROM customers 
                    WHERE customer_code ILIKE %s OR short_name ILIKE %s OR company_name ILIKE %s
                    LIMIT 1
                """, (f"%{customer_code}%", f"%{customer_code}%", f"%{customer_code}%"))
                customer = cursor.fetchone()
                if customer:
                    enriched["customer_id"] = customer["customer_id"]
                    enriched["customer_code"] = customer["customer_code"]
                    enriched["customer_name"] = customer["short_name"] or customer["company_name"]
                    enriched["customer_matched"] = True
                else:
                    # Customer not found - get list of available customers for selection
                    cursor.execute("""
                        SELECT customer_id, customer_code, short_name 
                        FROM customers 
                        WHERE is_active = TRUE
                        ORDER BY short_name
                        LIMIT 20
                    """)
                    available = cursor.fetchall()
                    enriched["available_customers"] = [
                        {"id": c["customer_id"], "code": c["customer_code"], "name": c["short_name"]}
                        for c in available
                    ]
                    enriched["customer_warning"] = f"Không tìm thấy khách hàng '{customer_code}' trong DB. Vui lòng chọn khách hàng đúng."
            
            # Lookup route based on addresses
            pickup = entities.get("pickup_address", "")
            delivery = entities.get("delivery_address", "")
            if pickup or delivery:
                cursor.execute("""
                    SELECT route_id, origin, destination, route_code
                    FROM master_routes 
                    WHERE origin ILIKE %s OR destination ILIKE %s
                    LIMIT 1
                """, (f"%{pickup}%", f"%{delivery}%"))
                route = cursor.fetchone()
                if route:
                    enriched["route_id"] = route["route_id"]
                    enriched["route_name"] = f"{route['origin']} → {route['destination']}"
                    enriched["route_code"] = route.get("route_code")
            
            # Lookup pricing
            customer_id = enriched.get("customer_id")
            route_id = enriched.get("route_id")
            vehicle_type = entities.get("vehicle_type")
            
            if customer_id and route_id and vehicle_type:
                # Customer rate (revenue)
                cursor.execute("""
                    SELECT price FROM customer_rates 
                    WHERE customer_id = %s AND route_id = %s AND vehicle_type = %s
                    AND is_active = TRUE
                    ORDER BY effective_date DESC LIMIT 1
                """, (customer_id, route_id, vehicle_type))
                customer_rate = cursor.fetchone()
                
                # Get suggested vendor and cost
                cursor.execute("""
                    SELECT v.vendor_id, v.vendor_name, v.short_name, vr.price as cost
                    FROM vendor_rates vr
                    JOIN vendors v ON vr.vendor_id = v.vendor_id
                    WHERE vr.route_id = %s AND vr.vehicle_type = %s
                    AND vr.is_active = TRUE
                    ORDER BY vr.price ASC LIMIT 1
                """, (route_id, vehicle_type))
                vendor_rate = cursor.fetchone()
                
                pricing = {}
                if customer_rate:
                    pricing["revenue"] = float(customer_rate["price"])
                if vendor_rate:
                    pricing["cost"] = float(vendor_rate["cost"])
                    enriched["vendor_id"] = vendor_rate["vendor_id"]
                    enriched["vendor_name"] = vendor_rate["short_name"] or vendor_rate["vendor_name"]
                
                if "revenue" in pricing and "cost" in pricing:
                    pricing["profit"] = pricing["revenue"] - pricing["cost"]
                    pricing["margin"] = (pricing["profit"] / pricing["cost"] * 100) if pricing["cost"] else 0
                
                enriched["pricing"] = pricing
            
        finally:
            cursor.close()
            conn.close()
        
        return enriched
    
    async def _enrich_update_job(self, entities: Dict) -> Dict:
        """Enrich UPDATE_JOB entities - auto lookup job info from DB"""
        enriched = dict(entities)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            job_id = None
            job_data = None
            
            # Find job by job_number first
            job_number = entities.get("job_number")
            invoice_ref = entities.get("invoice_ref")
            bl_awb_ref = entities.get("bl_awb_ref")
            
            if job_number:
                cursor.execute("""
                    SELECT j.*, c.customer_code, c.short_name as customer_name
                    FROM jobs j
                    JOIN customers c ON j.customer_id = c.customer_id
                    WHERE j.job_no ILIKE %s
                    LIMIT 1
                """, (f"%{job_number}%",))
                job_data = cursor.fetchone()
            
            if not job_data and invoice_ref:
                cursor.execute("""
                    SELECT j.*, c.customer_code, c.short_name as customer_name, 
                           js.invoice_numbers
                    FROM jobs j
                    JOIN customers c ON j.customer_id = c.customer_id
                    JOIN job_services js ON js.job_id = j.job_id
                    WHERE js.invoice_numbers ILIKE %s
                    LIMIT 1
                """, (f"%{invoice_ref}%",))
                job_data = cursor.fetchone()
            
            if not job_data and bl_awb_ref:
                cursor.execute("""
                    SELECT j.*, c.customer_code, c.short_name as customer_name,
                           js.bl_awb_no
                    FROM jobs j
                    JOIN customers c ON j.customer_id = c.customer_id
                    JOIN job_services js ON js.job_id = j.job_id
                    WHERE js.bl_awb_no ILIKE %s
                    LIMIT 1
                """, (f"%{bl_awb_ref}%",))
                job_data = cursor.fetchone()
            
            if job_data:
                enriched["job_found"] = True
                enriched["job_id"] = job_data["job_id"]
                enriched["job_number"] = job_data["job_no"]
                enriched["customer_id"] = job_data["customer_id"]
                enriched["customer_code"] = job_data["customer_code"]
                enriched["customer_name"] = job_data["customer_name"]
                enriched["customer_matched"] = True
                enriched["current_status"] = job_data["status_code"]
                
                # Get service info
                cursor.execute("""
                    SELECT js.*, mst.name_vi as service_name
                    FROM job_services js
                    LEFT JOIN master_service_types mst ON js.service_type_code = mst.service_code
                    WHERE js.job_id = %s
                """, (job_data["job_id"],))
                services = cursor.fetchall()
                
                if services:
                    svc = services[0]
                    enriched["service_type_code"] = svc["service_type_code"]
                    enriched["service_name"] = svc["service_name"]
                    enriched["scheduled_date"] = str(svc["scheduled_date"]) if svc["scheduled_date"] else None
                    enriched["services_count"] = len(services)
                
                logger.info(f"UPDATE_JOB: Found job {job_data['job_no']} for customer {job_data['customer_name']}")
            else:
                enriched["job_found"] = False
                enriched["customer_matched"] = False
                enriched["job_warning"] = "Không tìm thấy job. Vui lòng nhập job_number, invoice hoặc B/L."
                logger.warning(f"UPDATE_JOB: Job not found for {job_number or invoice_ref or bl_awb_ref}")
        
        finally:
            conn.close()
        
        return enriched
    
    async def _enrich_assign_vehicle(self, entities: Dict) -> Dict:
        """Enrich ASSIGN_VEHICLE entities"""
        enriched = dict(entities)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Find pending jobs that might match (use job_services for trucking)
            cursor.execute("""
                SELECT j.job_id, j.job_no, c.customer_code, js.scheduled_date, js.scheduled_time,
                       js.service_details
                FROM jobs j
                JOIN customers c ON j.customer_id = c.customer_id
                LEFT JOIN job_services js ON j.job_id = js.job_id
                WHERE j.status_code IN ('PENDING', 'CONFIRMED', 'DRAFT')
                AND (js.vehicle_id IS NULL OR js.vehicle_id = 0)
                ORDER BY j.created_at DESC
                LIMIT 10
            """)
            pending_jobs = cursor.fetchall()
            
            # Try to match based on hints
            hint = entities.get("linked_job_hint", "")
            matched_job = None
            
            for job in pending_jobs:
                # Match by customer code in hint
                if job["customer_code"] and job["customer_code"].lower() in hint.lower():
                    matched_job = job
                    break
            
            # If no match, suggest most recent
            if not matched_job and pending_jobs:
                matched_job = pending_jobs[0]
            
            if matched_job:
                enriched["job_id"] = matched_job["job_id"]
                enriched["job_number"] = matched_job["job_no"]
                enriched["job_customer"] = matched_job["customer_code"]
                enriched["job_date"] = str(matched_job["scheduled_date"]) if matched_job.get("scheduled_date") else None
                # Get invoice from service_details if available
                if matched_job.get("service_details"):
                    details = matched_job["service_details"]
                    if isinstance(details, str):
                        details = json.loads(details)
                    if details.get("invoice_numbers"):
                        enriched["invoice_numbers"] = details["invoice_numbers"]
            
            # Lookup driver if exists
            license_plate = entities.get("license_plate", "").replace(" ", "").replace(".", "")
            if license_plate:
                cursor.execute("""
                    SELECT driver_id, full_name, phone, id_card
                    FROM drivers 
                    WHERE REPLACE(REPLACE(license_plate, ' ', ''), '.', '') ILIKE %s
                    LIMIT 1
                """, (f"%{license_plate}%",))
                driver = cursor.fetchone()
                if driver:
                    enriched["driver_id"] = driver["driver_id"]
                    enriched["existing_driver"] = True
            
        finally:
            cursor.close()
            conn.close()
        
        return enriched
    
    # Job operations
    
    async def create_job(self, job_data: Dict, user_id: int) -> Dict:
        """Create new job using actual schema (jobs + job_services) with multi-service support"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Determine service type and job prefix
            service_type = job_data.get("service_type_code", "TRUCKING_SHORT")
            
            # Set job prefix based on service type
            if service_type.startswith("WHS"):
                prefix = "WHS"
            elif service_type.startswith("CUS"):
                prefix = "CUS"
            elif service_type.startswith("SVC"):
                prefix = "PKG"  # Packing services
            else:
                prefix = "TRK"
            
            # Generate job number
            today = date.today()
            cursor.execute("""
                SELECT COUNT(*) + 1 as next_num FROM jobs 
                WHERE DATE(created_at) = %s AND job_no LIKE %s
            """, (today, f"{prefix}%"))
            result = cursor.fetchone()
            next_num = result["next_num"] if result else 1
            job_no = f"{prefix}-{today.strftime('%d%m')}-{next_num:04d}"
            
            # Build description from entities
            dims = ""
            if job_data.get("dimension_length_cm"):
                dims = f"{job_data.get('dimension_length_cm')}x{job_data.get('dimension_width_cm')}x{job_data.get('dimension_height_cm')}cm"
            
            pkg_info = ""
            if job_data.get("package_quantity"):
                pkg_info = f"{job_data.get('package_quantity')} {job_data.get('package_unit', 'kiện')}"
            
            description = f"{job_data.get('cargo_type', '')} - {pkg_info} {dims} - Invoice: {job_data.get('invoice_numbers', '')}"
            
            # Insert into jobs table (main job record)
            cursor.execute("""
                INSERT INTO jobs (
                    job_no, customer_id, description, etd, status_code
                ) VALUES (
                    %s, %s, %s, %s, 'PENDING'
                ) RETURNING job_id, job_no
            """, (
                job_no,
                job_data.get("customer_id"),
                description.strip(),
                job_data.get("booking_date") or job_data.get("storage_start_date")
            ))
            
            job = cursor.fetchone()
            job_id = job["job_id"]
            
            logger.info(f"Created job: job_id={job_id}, job_no={job_no}")
            
            # Get services from job_data (AI already detected)
            services = job_data.get("services", [])
            
            # Fallback: if no services array, use service_type_code
            if not services:
                if service_type.startswith("WHS"):
                    services = ["WHS_STORAGE"]
                    # Also add WHS_HANDLE if in special requirements
                    special_reqs = job_data.get("special_requirements", "") or ""
                    if "nâng" in special_reqs.lower() or "bốc" in special_reqs.lower():
                        services.append("WHS_HANDLE")
                else:
                    services = [service_type]
            
            logger.info(f"Services to create: {services}")
            
            # Handle multi-item cargo - create separate job_service for each item
            cargo_items = job_data.get("cargo_items", [])
            packing_items = job_data.get("packing_items", [])
            
            # Use cargo_items for general services, packing_items for SVC_* services
            items_to_process = packing_items if service_type.startswith("SVC") else cargo_items
            
            if items_to_process:
                # Create job_service for each cargo/packing item
                for item in items_to_process:
                    cursor.execute("""
                        INSERT INTO job_services (
                            job_id, service_type_code, scheduled_date, scheduled_time,
                            origin_address, dest_address, vendor_id, status_code,
                            cargo_type, package_quantity, package_unit, weight_kg,
                            dimension_length_cm, dimension_width_cm, dimension_height_cm,
                            invoice_numbers, special_requirements,
                            storage_start_date, storage_end_date,
                            declaration_no, declaration_datetime, loai_hinh, customs_type,
                            customs_port, buyer_name, seller_name, hs_code, bl_awb_no, co_no,
                            packing_type, items_count, packages_output,
                            before_length_cm, before_width_cm, before_height_cm,
                            after_length_cm, after_width_cm, after_height_cm,
                            shrink_wrap, vacuum_pack, lashing, fumigation
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, 'PENDING',
                            %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s,
                            %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s, %s
                    ) RETURNING svc_id
                    """, (
                        job_id,
                        service_type,
                        job_data.get("booking_date") or job_data.get("storage_start_date"),
                        job_data.get("pickup_time"),
                        job_data.get("pickup_address"),
                        job_data.get("delivery_address"),
                        job_data.get("vendor_id"),
                        # Item-specific cargo info
                        item.get("description") or job_data.get("cargo_type"),
                        item.get("package_quantity") or 1,  # package count for this item
                        item.get("package_unit") or job_data.get("package_unit") or "kiện",
                        item.get("weight_kg"),
                        # Dimensions - support both cargo_items (length_cm) and packing_items (before_length_cm)
                        item.get("length_cm") or item.get("before_length_cm") or job_data.get("dimension_length_cm"),
                        item.get("width_cm") or item.get("before_width_cm") or job_data.get("dimension_width_cm"),
                        item.get("height_cm") or item.get("before_height_cm") or job_data.get("dimension_height_cm"),
                        # Invoice - item-specific or job-level
                        item.get("invoice_no") or job_data.get("invoice_numbers"),
                        job_data.get("special_requirements"),
                        job_data.get("storage_start_date"),
                        job_data.get("storage_end_date"),
                        job_data.get("declaration_no"),
                        job_data.get("declaration_datetime"),
                        job_data.get("loai_hinh"),
                        job_data.get("customs_type"),
                        job_data.get("customs_port"),
                        job_data.get("buyer_name"),
                        job_data.get("seller_name"),
                        job_data.get("hs_code"),
                        job_data.get("bl_awb_no"),
                        job_data.get("co_no"),
                        # Packing item-specific
                        job_data.get("packing_type") or "WOODEN_BOX",
                        1,  # items_count per record
                        1,  # packages_output per record
                        item.get("before_length_cm"),
                        item.get("before_width_cm"),
                        item.get("before_height_cm"),
                        item.get("after_length_cm"),
                        item.get("after_width_cm"),
                        item.get("after_height_cm"),
                        item.get("shrink_wrap") or False,
                        item.get("vacuum_pack") or False,
                        item.get("lashing") or False,
                        item.get("fumigation") or False
                    ))
                    
                    svc = cursor.fetchone()
                    logger.info(f"Created packing item service: svc_id={svc['svc_id']}, item_no={item.get('item_no')}")
                
                # Skip normal service creation loop
                services = []
                logger.info(f"Created {len(packing_items)} packing item services")
            
            # Insert each service (for non-packing or single-item packing)
            for svc_type in services:
                cursor.execute("""
                    INSERT INTO job_services (
                        job_id, service_type_code, scheduled_date, scheduled_time,
                        origin_address, dest_address, vendor_id, status_code,
                        cargo_type, package_quantity, package_unit, weight_kg,
                        dimension_length_cm, dimension_width_cm, dimension_height_cm,
                        invoice_numbers, special_requirements,
                        storage_start_date, storage_end_date,
                        -- Customs fields
                        declaration_no, declaration_datetime, loai_hinh, customs_type,
                        customs_port, buyer_name, seller_name, hs_code, bl_awb_no, co_no,
                        -- Packing fields
                        packing_type, items_count, packages_output,
                        before_length_cm, before_width_cm, before_height_cm,
                        after_length_cm, after_width_cm, after_height_cm,
                        shrink_wrap, vacuum_pack, lashing, fumigation
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, 'PENDING',
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s,
                        %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s
                    ) RETURNING svc_id
                """, (
                    job_id,
                    svc_type,
                    job_data.get("booking_date") or job_data.get("storage_start_date"),
                    job_data.get("pickup_time"),
                    job_data.get("pickup_address"),
                    job_data.get("delivery_address"),
                    job_data.get("vendor_id"),
                    job_data.get("cargo_type"),
                    job_data.get("package_quantity"),
                    job_data.get("package_unit"),
                    job_data.get("weight_kg"),
                    job_data.get("dimension_length_cm"),
                    job_data.get("dimension_width_cm"),
                    job_data.get("dimension_height_cm"),
                    job_data.get("invoice_numbers"),
                    job_data.get("special_requirements"),
                    job_data.get("storage_start_date"),
                    job_data.get("storage_end_date"),
                    # Customs
                    job_data.get("declaration_no"),
                    job_data.get("declaration_datetime"),
                    job_data.get("loai_hinh"),
                    job_data.get("customs_type"),
                    job_data.get("customs_port"),
                    job_data.get("buyer_name"),
                    job_data.get("seller_name"),
                    job_data.get("hs_code"),
                    job_data.get("bl_awb_no"),
                    job_data.get("co_no"),
                    # Packing
                    job_data.get("packing_type"),
                    job_data.get("items_count"),
                    job_data.get("packages_output"),
                    job_data.get("before_length_cm"),
                    job_data.get("before_width_cm"),
                    job_data.get("before_height_cm"),
                    job_data.get("after_length_cm"),
                    job_data.get("after_width_cm"),
                    job_data.get("after_height_cm"),
                    job_data.get("shrink_wrap") or False,
                    job_data.get("vacuum_pack") or False,
                    job_data.get("lashing") or False,
                    job_data.get("fumigation") or False
                ))
                
                svc = cursor.fetchone()
                logger.info(f"Created job_service: svc_id={svc['svc_id']}, type={svc_type}")
            
            conn.commit()
            
            return {
                "id": job_id, 
                "job_number": job_no,
                "services_count": len(services),
                "services": services
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating job: {e}")
            logger.error(traceback.format_exc())
            raise e
        finally:
            cursor.close()
            conn.close()
    
    async def assign_vehicle(self, job_id: int, vehicle_data: Dict, user_id: int) -> Dict:
        """Assign vehicle to job service"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Update job_services with vehicle info
            cursor.execute("""
                UPDATE job_services SET
                    vendor_text_input = %s,
                    status_code = 'DISPATCHED',
                    updated_at = NOW()
                WHERE job_id = %s
                RETURNING svc_id
            """, (
                json.dumps({
                    "license_plate": vehicle_data.get("license_plate"),
                    "driver_name": vehicle_data.get("driver_name"),
                    "driver_phone": vehicle_data.get("driver_phone"),
                    "driver_id_card": vehicle_data.get("driver_id_card")
                }),
                job_id
            ))
            
            # Update job status
            cursor.execute("""
                UPDATE jobs SET
                    status_code = 'DISPATCHED',
                    updated_at = NOW()
                WHERE job_id = %s
                RETURNING job_id, job_no
            """, (job_id,))
            
            job = cursor.fetchone()
            conn.commit()
            
            return {"id": job["job_id"], "job_number": job["job_no"]}
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    async def get_job(self, job_id: int) -> Optional[Dict]:
        """Get job details"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT j.*, 
                       c.customer_code, c.short_name as customer_name,
                       v.vendor_name, v.short_name as vendor_short_name,
                       js.scheduled_date, js.scheduled_time, js.origin_address, js.dest_address,
                       js.service_details, js.vendor_text_input
                FROM jobs j
                LEFT JOIN customers c ON j.customer_id = c.customer_id
                LEFT JOIN job_services js ON j.job_id = js.job_id
                LEFT JOIN vendors v ON js.vendor_id = v.vendor_id
                WHERE j.job_id = %s
            """, (job_id,))
            
            return cursor.fetchone()
            
        finally:
            cursor.close()
            conn.close()


# Singleton
_data_service: Optional[DataService] = None


def get_data_service() -> DataService:
    global _data_service
    if _data_service is None:
        _data_service = DataService()
    return _data_service
