"""
Data Service - Database lookups and enrichment using Supabase SDK
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import date, time
import json
import traceback

from app.db.supabase_client import get_supabase
from app.ai.utils.smart_parser import (
    format_date_iso, format_time_str, parse_number
)

logger = logging.getLogger(__name__)


class DataService:
    """Service for database operations using Supabase SDK"""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Lazy load Supabase client"""
        if self._client is None:
            self._client = get_supabase()
        return self._client

    async def enrich_entities(
        self,
        intent: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enrich extracted entities with database lookups"""
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
        enriched["customer_matched"] = False

        customer_code = entities.get("customer_code")

        # Search by customer_code
        if customer_code:
            result = self.client.table('customers').select(
                'customer_id, customer_code, company_name, short_name'
            ).or_(
                f"customer_code.ilike.%{customer_code}%,"
                f"short_name.ilike.%{customer_code}%,"
                f"company_name.ilike.%{customer_code}%"
            ).limit(1).execute()

            if result.data:
                customer = result.data[0]
                enriched["customer_id"] = customer["customer_id"]
                enriched["customer_code"] = customer["customer_code"]
                enriched["customer_name"] = customer["short_name"] or customer["company_name"]
                enriched["customer_matched"] = True

        # Fallback: search from pickup_address
        if not enriched["customer_matched"]:
            pickup_addr = entities.get("pickup_address", "")
            delivery_addr = entities.get("delivery_address", "")
            search_terms = [t.strip() for t in (pickup_addr + " " + delivery_addr).split() if len(t.strip()) > 2]

            for term in search_terms[:5]:  # Limit search terms
                result = self.client.table('customers').select(
                    'customer_id, customer_code, company_name, short_name'
                ).or_(
                    f"customer_code.ilike.%{term}%,"
                    f"short_name.ilike.%{term}%,"
                    f"company_name.ilike.%{term}%"
                ).limit(1).execute()

                if result.data:
                    customer = result.data[0]
                    enriched["customer_id"] = customer["customer_id"]
                    enriched["customer_code"] = customer["customer_code"]
                    enriched["customer_name"] = customer["short_name"] or customer["company_name"]
                    enriched["customer_matched"] = True
                    enriched["customer_from_address"] = term
                    break

        # If still not matched, show available customers
        if not enriched["customer_matched"]:
            result = self.client.table('customers').select(
                'customer_id, customer_code, short_name'
            ).eq('is_active', True).order('short_name').limit(20).execute()

            enriched["available_customers"] = [
                {"id": c["customer_id"], "code": c["customer_code"], "name": c["short_name"]}
                for c in result.data
            ]
            enriched["customer_warning"] = f"Khong tim thay khach hang '{customer_code or 'N/A'}' trong DB."

        # Lookup route
        pickup = entities.get("pickup_address", "")
        delivery = entities.get("delivery_address", "")
        if pickup or delivery:
            result = self.client.table('master_routes').select(
                'route_id, origin, destination, route_code'
            ).or_(
                f"origin.ilike.%{pickup}%,destination.ilike.%{delivery}%"
            ).limit(1).execute()

            if result.data:
                route = result.data[0]
                enriched["route_id"] = route["route_id"]
                enriched["route_name"] = f"{route['origin']} -> {route['destination']}"
                enriched["route_code"] = route.get("route_code")

        # Lookup pricing
        customer_id = enriched.get("customer_id")
        route_id = enriched.get("route_id")
        vehicle_type = entities.get("vehicle_type")

        if customer_id and route_id and vehicle_type:
            # Customer rate (revenue)
            cr_result = self.client.table('customer_rates').select('price').eq(
                'customer_id', customer_id
            ).eq('route_id', route_id).eq('vehicle_type', vehicle_type).eq(
                'is_active', True
            ).order('effective_date', desc=True).limit(1).execute()

            # Vendor rate (cost)
            vr_result = self.client.table('vendor_rates').select(
                'price, vendor_id, vendors(company_name, short_name)'
            ).eq('route_id', route_id).eq('vehicle_type', vehicle_type).eq(
                'is_active', True
            ).order('price').limit(1).execute()

            pricing = {}
            if cr_result.data:
                pricing["revenue"] = float(cr_result.data[0]["price"])
            if vr_result.data:
                vr = vr_result.data[0]
                pricing["cost"] = float(vr["price"])
                enriched["vendor_id"] = vr["vendor_id"]
                if vr.get("vendors"):
                    enriched["vendor_name"] = vr["vendors"].get("short_name") or vr["vendors"].get("company_name")

            if "revenue" in pricing and "cost" in pricing:
                pricing["profit"] = pricing["revenue"] - pricing["cost"]
                pricing["margin"] = (pricing["profit"] / pricing["cost"] * 100) if pricing["cost"] else 0

            enriched["pricing"] = pricing

        return enriched

    async def _enrich_update_job(self, entities: Dict) -> Dict:
        """Enrich UPDATE_JOB entities"""
        enriched = dict(entities)
        job_data = None

        job_number = entities.get("job_number")
        invoice_ref = entities.get("invoice_ref")
        bl_awb_ref = entities.get("bl_awb_ref")

        # Find job by job_number
        if job_number:
            result = self.client.table('jobs').select(
                '*, customers(customer_code, short_name)'
            ).ilike('job_no', f'%{job_number}%').limit(1).execute()
            if result.data:
                job_data = result.data[0]

        # Find by invoice
        if not job_data and invoice_ref:
            result = self.client.table('job_services').select(
                'job_id, jobs(*, customers(customer_code, short_name))'
            ).ilike('invoice_numbers', f'%{invoice_ref}%').limit(1).execute()
            if result.data and result.data[0].get('jobs'):
                job_data = result.data[0]['jobs']

        # Find by B/L
        if not job_data and bl_awb_ref:
            result = self.client.table('job_services').select(
                'job_id, jobs(*, customers(customer_code, short_name))'
            ).ilike('bl_awb_no', f'%{bl_awb_ref}%').limit(1).execute()
            if result.data and result.data[0].get('jobs'):
                job_data = result.data[0]['jobs']

        if job_data:
            enriched["job_found"] = True
            enriched["job_id"] = job_data["job_id"]
            enriched["job_number"] = job_data["job_no"]
            enriched["customer_id"] = job_data["customer_id"]
            enriched["current_status"] = job_data["status_code"]
            enriched["customer_matched"] = True

            if job_data.get("customers"):
                enriched["customer_code"] = job_data["customers"]["customer_code"]
                enriched["customer_name"] = job_data["customers"]["short_name"]

            # Get services
            svc_result = self.client.table('job_services').select(
                '*, master_service_types(name_vi)'
            ).eq('job_id', job_data["job_id"]).execute()

            if svc_result.data:
                svc = svc_result.data[0]
                enriched["service_type_code"] = svc["service_type_code"]
                enriched["service_name"] = svc.get("master_service_types", {}).get("name_vi")
                enriched["scheduled_date"] = str(svc["scheduled_date"]) if svc.get("scheduled_date") else None
                enriched["services_count"] = len(svc_result.data)
        else:
            enriched["job_found"] = False
            enriched["customer_matched"] = False
            enriched["job_warning"] = "Khong tim thay job. Vui long nhap job_number, invoice hoac B/L."

        return enriched

    async def _enrich_assign_vehicle(self, entities: Dict) -> Dict:
        """Enrich ASSIGN_VEHICLE entities"""
        enriched = dict(entities)

        # Lookup by job_number if provided
        job_number = entities.get("job_number")
        if job_number:
            result = self.client.table('jobs').select(
                'job_id, job_no, customers(customer_code), '
                'job_services(scheduled_date, scheduled_time, service_details, origin_address, dest_address)'
            ).ilike('job_no', f'%{job_number}%').limit(1).execute()

            if result.data:
                job = result.data[0]
                enriched["job_id"] = job["job_id"]
                enriched["job_number"] = job["job_no"]
                if job.get("customers"):
                    enriched["job_customer"] = job["customers"]["customer_code"]
                if job.get("job_services") and len(job["job_services"]) > 0:
                    svc = job["job_services"][0]
                    enriched["job_date"] = str(svc["scheduled_date"]) if svc.get("scheduled_date") else None
                    enriched["pickup_address"] = svc.get("origin_address")
                    enriched["delivery_address"] = svc.get("dest_address")

                    if svc.get("service_details"):
                        details = svc["service_details"]
                        if isinstance(details, str):
                            details = json.loads(details)
                        if details.get("invoice_numbers"):
                            enriched["invoice_numbers"] = details["invoice_numbers"]
                        if details.get("package_quantity"):
                            enriched["package_quantity"] = details["package_quantity"]
                return enriched

        # Fallback: Find pending jobs
        result = self.client.table('jobs').select(
            'job_id, job_no, customers(customer_code), description, '
            'job_services(scheduled_date, scheduled_time, service_details, origin_address, dest_address, vehicle_id)'
        ).in_('status_code', ['PENDING', 'CONFIRMED', 'DRAFT']).order(
            'created_at', desc=True
        ).limit(10).execute()

        pending_jobs = result.data or []
        hint = entities.get("linked_job_hint", "") or ""
        matched_job = None

        for job in pending_jobs:
            if hint and job.get("job_no") and job["job_no"].upper() in hint.upper():
                matched_job = job
                break
            if job.get("customers") and job["customers"]["customer_code"].lower() in hint.lower():
                matched_job = job
                break

        if not matched_job and pending_jobs:
            matched_job = pending_jobs[0]

        if matched_job:
            enriched["job_id"] = matched_job["job_id"]
            enriched["job_number"] = matched_job["job_no"]
            if matched_job.get("customers"):
                enriched["job_customer"] = matched_job["customers"]["customer_code"]
            if matched_job.get("job_services") and len(matched_job["job_services"]) > 0:
                svc = matched_job["job_services"][0]
                enriched["job_date"] = str(svc["scheduled_date"]) if svc.get("scheduled_date") else None
                enriched["pickup_address"] = svc.get("origin_address")
                enriched["delivery_address"] = svc.get("dest_address")

        # Lookup driver by license plate
        license_plate = entities.get("license_plate", "").replace(" ", "").replace(".", "")
        if license_plate:
            result = self.client.table('drivers').select(
                'driver_id, full_name, phone, id_card'
            ).ilike('license_plate', f'%{license_plate}%').limit(1).execute()
            if result.data:
                driver = result.data[0]
                enriched["driver_id"] = driver["driver_id"]
                enriched["existing_driver"] = True

        return enriched

    # Job operations

    async def create_job(self, job_data: Dict, user_id: int) -> Dict:
        """Create new job using Supabase"""
        try:
            # Determine service type and prefix
            service_type = job_data.get("service_type_code", "TRUCKING_SHORT")

            if service_type.startswith("WHS"):
                prefix = "WHS"
            elif service_type.startswith("CUS"):
                prefix = "CUS"
            elif service_type.startswith("SVC"):
                prefix = "PKG"
            else:
                prefix = "TRK"

            # Generate job number
            today = date.today()
            count_result = self.client.table('jobs').select(
                'job_id', count='exact'
            ).gte('created_at', today.isoformat()).ilike('job_no', f'{prefix}%').execute()

            next_num = (count_result.count or 0) + 1
            job_no = f"{prefix}-{today.strftime('%d%m')}-{next_num:04d}"

            # Build description
            dims = ""
            if job_data.get("dimension_length_cm"):
                dims = f"{job_data.get('dimension_length_cm')}x{job_data.get('dimension_width_cm')}x{job_data.get('dimension_height_cm')}cm"

            pkg_info = ""
            if job_data.get("package_quantity"):
                pkg_info = f"{job_data.get('package_quantity')} {job_data.get('package_unit', 'kien')}"

            description = f"{job_data.get('cargo_type', '')} - {pkg_info} {dims} - Invoice: {job_data.get('invoice_numbers', '')}"

            # Parse booking date using smart parser (handles multiple formats)
            booking_date_raw = job_data.get("booking_date") or job_data.get("storage_start_date")
            etd_date = format_date_iso(booking_date_raw) if booking_date_raw else today.isoformat()

            # Insert job
            job_result = self.client.table('jobs').insert({
                'job_no': job_no,
                'customer_id': job_data.get("customer_id"),
                'description': description.strip(),
                'etd': etd_date,
                'status_code': 'PENDING'
            }).execute()

            job = job_result.data[0]
            job_id = job["job_id"]

            logger.info(f"Created job: job_id={job_id}, job_no={job_no}")

            # Get services
            services = job_data.get("services", [])
            if not services:
                services = [service_type]

            # Handle cargo items
            cargo_items = job_data.get("cargo_items", [])
            packing_items = job_data.get("packing_items", [])
            items_to_process = packing_items if service_type.startswith("SVC") else cargo_items

            # Create services from items
            if items_to_process:
                for item in items_to_process:
                    service_details_json = {
                        "invoice_numbers": [item.get("invoice_no")] if item.get("invoice_no") else [],
                        "cargo_items": [item] if item else [],
                        "package_quantity": item.get("package_quantity") or 1,
                        "package_unit": item.get("package_unit") or job_data.get("package_unit") or "kien",
                        "cargo_type": item.get("description") or job_data.get("cargo_type"),
                    }

                    # Use smart parser for flexible date/time handling
                    scheduled_date_str = format_date_iso(job_data.get("booking_date")) or today.isoformat()
                    scheduled_time_str = format_time_str(job_data.get("pickup_time"))

                    self.client.table('job_services').insert({
                        'job_id': job_id,
                        'service_type_code': service_type,
                        'scheduled_date': scheduled_date_str,
                        'scheduled_time': scheduled_time_str,
                        'origin_address': job_data.get("pickup_address"),
                        'dest_address': job_data.get("delivery_address"),
                        'vendor_id': job_data.get("vendor_id"),
                        'status_code': 'PENDING',
                        'cargo_type': item.get("description") or job_data.get("cargo_type"),
                        'package_quantity': item.get("package_quantity") or 1,
                        'package_unit': item.get("package_unit") or job_data.get("package_unit") or "kien",
                        'weight_kg': item.get("weight_kg"),
                        'dimension_length_cm': item.get("length_cm") or job_data.get("dimension_length_cm"),
                        'dimension_width_cm': item.get("width_cm") or job_data.get("dimension_width_cm"),
                        'dimension_height_cm': item.get("height_cm") or job_data.get("dimension_height_cm"),
                        'invoice_numbers': item.get("invoice_no") or job_data.get("invoice_numbers"),
                        'special_requirements': job_data.get("special_requirements"),
                        'service_details': service_details_json
                    }).execute()
                services = []

            # Create services (single-item mode)
            for svc_type in services:
                invoice_nums = job_data.get("invoice_numbers") or []
                if isinstance(invoice_nums, str):
                    invoice_nums = [i.strip() for i in invoice_nums.split(",") if i.strip()]

                service_details_json = {
                    "invoice_numbers": invoice_nums,
                    "cargo_items": [],
                    "package_quantity": job_data.get("package_quantity") or 0,
                    "package_unit": job_data.get("package_unit") or "kien",
                    "cargo_type": job_data.get("cargo_type"),
                }

                # Use smart parser for flexible date/time handling
                scheduled_date_str = format_date_iso(job_data.get("booking_date")) or today.isoformat()
                scheduled_time_str = format_time_str(job_data.get("pickup_time"))
                storage_start = format_date_iso(job_data.get("storage_start_date"))
                storage_end = format_date_iso(job_data.get("storage_end_date"))

                self.client.table('job_services').insert({
                    'job_id': job_id,
                    'service_type_code': svc_type,
                    'scheduled_date': scheduled_date_str,
                    'scheduled_time': scheduled_time_str,
                    'origin_address': job_data.get("pickup_address"),
                    'dest_address': job_data.get("delivery_address"),
                    'vendor_id': job_data.get("vendor_id"),
                    'status_code': 'PENDING',
                    'cargo_type': job_data.get("cargo_type"),
                    'package_quantity': job_data.get("package_quantity"),
                    'package_unit': job_data.get("package_unit"),
                    'weight_kg': job_data.get("weight_kg"),
                    'dimension_length_cm': job_data.get("dimension_length_cm"),
                    'dimension_width_cm': job_data.get("dimension_width_cm"),
                    'dimension_height_cm': job_data.get("dimension_height_cm"),
                    'invoice_numbers': job_data.get("invoice_numbers"),
                    'special_requirements': job_data.get("special_requirements"),
                    'storage_start_date': storage_start,
                    'storage_end_date': storage_end,
                    'declaration_no': job_data.get("declaration_no"),
                    'loai_hinh': job_data.get("loai_hinh"),
                    'customs_type': job_data.get("customs_type"),
                    'customs_port': job_data.get("customs_port"),
                    'buyer_name': job_data.get("buyer_name"),
                    'seller_name': job_data.get("seller_name"),
                    'hs_code': job_data.get("hs_code"),
                    'bl_awb_no': job_data.get("bl_awb_no"),
                    'co_no': job_data.get("co_no"),
                    'packing_type': job_data.get("packing_type"),
                    'items_count': job_data.get("items_count"),
                    'packages_output': job_data.get("packages_output"),
                    'shrink_wrap': job_data.get("shrink_wrap") or False,
                    'vacuum_pack': job_data.get("vacuum_pack") or False,
                    'lashing': job_data.get("lashing") or False,
                    'fumigation': job_data.get("fumigation") or False,
                    'service_details': service_details_json
                }).execute()

                logger.info(f"Created job_service for type={svc_type}")

            return {
                "id": job_id,
                "job_number": job_no,
                "services_count": len(services) or len(items_to_process),
                "services": services
            }

        except Exception as e:
            logger.error(f"Error creating job: {e}")
            logger.error(traceback.format_exc())
            raise e

    async def assign_vehicle(self, job_id: int, vehicle_data: Dict, user_id: int) -> Dict:
        """Assign vehicle to job service"""
        try:
            vendor_id = None
            vendor_name = vehicle_data.get("vendor_name")
            license_plate = vehicle_data.get("license_plate", "").replace(" ", "").replace(".", "")
            driver_phone = vehicle_data.get("driver_phone", "").replace(" ", "").replace("-", "")

            # Auto-lookup by license plate
            if license_plate:
                result = self.client.table('vehicles').select('vendor_id').ilike(
                    'plate_number', f'%{license_plate}%'
                ).limit(1).execute()
                if result.data and result.data[0].get('vendor_id'):
                    vendor_id = result.data[0]['vendor_id']
                    logger.info(f"Auto-found vendor {vendor_id} by license plate")

            # Auto-lookup by driver phone
            if driver_phone and not vendor_id:
                result = self.client.table('drivers').select('vendor_id').ilike(
                    'phone', f'%{driver_phone}%'
                ).limit(1).execute()
                if result.data and result.data[0].get('vendor_id'):
                    vendor_id = result.data[0]['vendor_id']

            # Manual vendor name search
            if vendor_name and not vendor_id:
                result = self.client.table('vendors').select('vendor_id').or_(
                    f"short_name.ilike.%{vendor_name}%,company_name.ilike.%{vendor_name}%"
                ).limit(1).execute()
                if result.data:
                    vendor_id = result.data[0]['vendor_id']

            # Update job_services
            update_data = {
                'vendor_text_input': json.dumps({
                    "license_plate": vehicle_data.get("license_plate"),
                    "driver_name": vehicle_data.get("driver_name"),
                    "driver_phone": vehicle_data.get("driver_phone"),
                    "driver_id_card": vehicle_data.get("driver_id_card"),
                    "vendor_name": vendor_name
                }),
                'status_code': 'DISPATCHED'
            }
            if vendor_id:
                update_data['vendor_id'] = vendor_id

            self.client.table('job_services').update(update_data).eq('job_id', job_id).execute()

            # Update job status
            job_result = self.client.table('jobs').update({
                'status_code': 'DISPATCHED'
            }).eq('job_id', job_id).execute()

            job = job_result.data[0]
            return {"id": job["job_id"], "job_number": job["job_no"]}

        except Exception as e:
            logger.error(f"Error assigning vehicle: {e}")
            raise e

    async def get_job(self, job_id: int) -> Optional[Dict]:
        """Get job details"""
        result = self.client.table('jobs').select(
            '*, customers(customer_code, short_name), '
            'job_services(*, vendors(company_name, short_name))'
        ).eq('job_id', job_id).limit(1).execute()

        if result.data:
            job = result.data[0]
            # Flatten for compatibility
            if job.get('customers'):
                job['customer_code'] = job['customers']['customer_code']
                job['customer_name'] = job['customers']['short_name']
            if job.get('job_services') and len(job['job_services']) > 0:
                svc = job['job_services'][0]
                job['scheduled_date'] = svc.get('scheduled_date')
                job['scheduled_time'] = svc.get('scheduled_time')
                job['origin_address'] = svc.get('origin_address')
                job['dest_address'] = svc.get('dest_address')
                job['service_details'] = svc.get('service_details')
                job['vendor_text_input'] = svc.get('vendor_text_input')
                if svc.get('vendors'):
                    job['vendor_name'] = svc['vendors'].get('company_name')
                    job['vendor_short_name'] = svc['vendors'].get('short_name')
            return job
        return None


# Singleton
_data_service: Optional[DataService] = None


def get_data_service() -> DataService:
    global _data_service
    if _data_service is None:
        _data_service = DataService()
    return _data_service
