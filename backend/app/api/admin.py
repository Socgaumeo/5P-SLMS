# backend/app/api/admin.py
"""
Admin API endpoints for master data CRUD operations.
Handles: Service Types, Vendors, Customers, Buying/Selling Rates.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional, List
import logging
from datetime import date

from app.db.supabase_client import get_supabase
from app.api.dependencies import require_manager_or_admin

logger = logging.getLogger(__name__)


def fetch_all_with_pagination(table_query, page_size: int = 1000):
    """
    Fetch all records from Supabase with pagination.
    Supabase has a default limit of 1000 rows per query.
    """
    all_data = []
    offset = 0
    while True:
        result = table_query.range(offset, offset + page_size - 1).execute()
        if not result.data:
            break
        all_data.extend(result.data)
        if len(result.data) < page_size:
            break
        offset += page_size
    return all_data

router = APIRouter(
    prefix="/api/admin", tags=["Admin"],
    dependencies=[Depends(require_manager_or_admin)]
)


# ============================================================
# PYDANTIC MODELS
# ============================================================

class ServiceTypeCreate(BaseModel):
    service_code: str
    name_vi: str
    name_en: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[str] = None  # comma-separated keywords for AI detection
    is_active: bool = True


class ServiceTypeUpdate(BaseModel):
    name_vi: Optional[str] = None
    name_en: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[str] = None
    is_active: Optional[bool] = None


class VendorCreate(BaseModel):
    vendor_code: str
    vendor_name: str
    short_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tax_code: Optional[str] = None
    country: Optional[str] = "VN"
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_swift: Optional[str] = None
    bank_address: Optional[str] = None
    currency: Optional[str] = "VND"
    contact_person: Optional[str] = None
    is_active: bool = True


class VendorUpdate(BaseModel):
    vendor_name: Optional[str] = None
    short_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tax_code: Optional[str] = None
    country: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_swift: Optional[str] = None
    bank_address: Optional[str] = None
    currency: Optional[str] = None
    contact_person: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerCreate(BaseModel):
    customer_code: str
    company_name: str
    short_name: Optional[str] = None
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    tax_code: Optional[str] = None
    is_active: bool = True


class CustomerUpdate(BaseModel):
    company_name: Optional[str] = None
    short_name: Optional[str] = None
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    tax_code: Optional[str] = None
    is_active: Optional[bool] = None


class RateCreate(BaseModel):
    customer_id: Optional[int] = None  # For selling rate
    vendor_id: Optional[int] = None    # For buying rate
    route_id: Optional[int] = None
    service_type_code: Optional[str] = None
    vehicle_type: Optional[str] = None
    price: float
    currency: str = "VND"
    unit: Optional[str] = None  # per trip, per kg, per cbm, etc.
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    notes: Optional[str] = None
    # Trucking specific fields
    origin_province: Optional[str] = None
    destination_province: Optional[str] = None
    rate_type: Optional[str] = "STANDARD"  # STANDARD, REFRIGERATED
    temperature_range: Optional[str] = None
    conditions: Optional[str] = None
    is_active: bool = True
    # Service-specific metadata (customs_type, packing_type, etc.)
    metadata: Optional[dict] = None


class RateUpdate(BaseModel):
    price: Optional[float] = None
    currency: Optional[str] = None
    unit: Optional[str] = None
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    service_type_code: Optional[str] = None
    metadata: Optional[dict] = None


# ============================================================
# SERVICE TYPES CRUD
# ============================================================

@router.get("/service-types")
def list_service_types(
    include_inactive: bool = Query(False),
    category: Optional[str] = Query(None)
):
    """List all service types"""
    try:
        client = get_supabase()
        query = client.table('master_service_types').select('*')

        if not include_inactive:
            query = query.eq('is_active', True)
        if category:
            query = query.eq('category', category)

        result = query.order('service_code').execute()
        return {"data": result.data, "total": len(result.data)}
    except Exception as e:
        logger.error(f"Error listing service types: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/service-types/{service_code}")
def get_service_type(service_code: str):
    """Get single service type by code"""
    try:
        client = get_supabase()
        result = client.table('master_service_types').select('*').eq(
            'service_code', service_code
        ).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Service type not found")
        return {"data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service type: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/service-types")
def create_service_type(data: ServiceTypeCreate):
    """Create new service type"""
    try:
        client = get_supabase()
        result = client.table('master_service_types').insert({
            'service_code': data.service_code.upper(),
            'name_vi': data.name_vi,
            'name_en': data.name_en,
            'category': data.category,
            'keywords': data.keywords,
            'is_active': data.is_active
        }).execute()

        return {"data": result.data[0], "message": "Service type created"}
    except Exception as e:
        logger.error(f"Error creating service type: {e}")
        if "duplicate key" in str(e).lower():
            raise HTTPException(status_code=400, detail="Service code already exists")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/service-types/{service_code}")
def update_service_type(service_code: str, data: ServiceTypeUpdate):
    """Update service type"""
    try:
        client = get_supabase()
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")

        result = client.table('master_service_types').update(update_data).eq(
            'service_code', service_code
        ).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Service type not found")
        return {"data": result.data[0], "message": "Service type updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating service type: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/service-types/{service_code}")
def delete_service_type(service_code: str, hard_delete: bool = Query(False)):
    """Delete service type (soft delete by default)"""
    try:
        client = get_supabase()

        if hard_delete:
            result = client.table('master_service_types').delete().eq(
                'service_code', service_code
            ).execute()
        else:
            result = client.table('master_service_types').update({
                'is_active': False
            }).eq('service_code', service_code).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Service type not found")
        return {"message": "Service type deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting service type: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# VENDORS CRUD
# ============================================================

@router.get("/vendors")
def list_vendors(
    include_inactive: bool = Query(False),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """List all vendors with pagination"""
    try:
        client = get_supabase()
        query = client.table('vendors').select('*', count='exact')

        if not include_inactive:
            query = query.eq('is_active', True)
        if search:
            query = query.or_(
                f"vendor_code.ilike.%{search}%,"
                f"vendor_name.ilike.%{search}%,"
                f"short_name.ilike.%{search}%"
            )

        result = query.order('vendor_code').range(offset, offset + limit - 1).execute()
        return {"data": result.data, "total": result.count or len(result.data)}
    except Exception as e:
        logger.error(f"Error listing vendors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vendors/{vendor_id}")
def get_vendor(vendor_id: int):
    """Get single vendor by ID"""
    try:
        client = get_supabase()
        result = client.table('vendors').select('*').eq('vendor_id', vendor_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Vendor not found")
        return {"data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vendor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vendors")
def create_vendor(data: VendorCreate):
    """Create new vendor"""
    try:
        client = get_supabase()
        insert_data = {
            'vendor_code': data.vendor_code.upper(),
            'vendor_name': data.vendor_name,
            'short_name': data.short_name,
            'address': data.address,
            'phone': data.phone,
            'email': data.email,
            'tax_code': data.tax_code,
            'country': data.country,
            'bank_name': data.bank_name,
            'bank_account': data.bank_account,
            'bank_swift': data.bank_swift,
            'bank_address': data.bank_address,
            'currency': data.currency,
            'contact_person': data.contact_person,
            'is_active': data.is_active,
        }
        # Remove None values to let DB defaults apply
        insert_data = {k: v for k, v in insert_data.items() if v is not None}
        result = client.table('vendors').insert(insert_data).execute()

        return {"data": result.data[0], "message": "Vendor created"}
    except Exception as e:
        logger.error(f"Error creating vendor: {e}")
        if "duplicate key" in str(e).lower():
            raise HTTPException(status_code=400, detail="Vendor code already exists")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/vendors/{vendor_id}")
def update_vendor(vendor_id: int, data: VendorUpdate):
    """Update vendor"""
    try:
        client = get_supabase()
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")

        result = client.table('vendors').update(update_data).eq('vendor_id', vendor_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Vendor not found")
        return {"data": result.data[0], "message": "Vendor updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vendor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/vendors/{vendor_id}")
def delete_vendor(vendor_id: int, hard_delete: bool = Query(False)):
    """Delete vendor (soft delete by default)"""
    try:
        client = get_supabase()

        if hard_delete:
            result = client.table('vendors').delete().eq('vendor_id', vendor_id).execute()
        else:
            result = client.table('vendors').update({
                'is_active': False
            }).eq('vendor_id', vendor_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Vendor not found")
        return {"message": "Vendor deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting vendor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# CUSTOMERS CRUD
# ============================================================

@router.get("/customers")
def list_customers(
    include_inactive: bool = Query(False),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """List all customers with pagination"""
    try:
        client = get_supabase()
        query = client.table('customers').select('*', count='exact')

        if not include_inactive:
            query = query.eq('is_active', True)
        if search:
            query = query.or_(
                f"customer_code.ilike.%{search}%,"
                f"company_name.ilike.%{search}%,"
                f"short_name.ilike.%{search}%"
            )

        result = query.order('customer_code').range(offset, offset + limit - 1).execute()
        return {"data": result.data, "total": result.count or len(result.data)}
    except Exception as e:
        logger.error(f"Error listing customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/{customer_id}")
def get_customer(customer_id: int):
    """Get single customer by ID"""
    try:
        client = get_supabase()
        result = client.table('customers').select('*').eq(
            'customer_id', customer_id
        ).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customers")
def create_customer(data: CustomerCreate):
    """Create new customer"""
    try:
        client = get_supabase()
        result = client.table('customers').insert({
            'customer_code': data.customer_code.upper(),
            'company_name': data.company_name,
            'short_name': data.short_name,
            'address': data.address,
            'contact_phone': data.contact_phone,
            'contact_email': data.contact_email,
            'tax_code': data.tax_code,
            'is_active': data.is_active
        }).execute()

        return {"data": result.data[0], "message": "Customer created"}
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        if "duplicate key" in str(e).lower():
            raise HTTPException(status_code=400, detail="Customer code already exists")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/customers/{customer_id}")
def update_customer(customer_id: int, data: CustomerUpdate):
    """Update customer"""
    try:
        client = get_supabase()
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")

        result = client.table('customers').update(update_data).eq(
            'customer_id', customer_id
        ).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"data": result.data[0], "message": "Customer updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/customers/{customer_id}")
def delete_customer(customer_id: int, hard_delete: bool = Query(False)):
    """Delete customer (soft delete by default)"""
    try:
        client = get_supabase()

        if hard_delete:
            result = client.table('customers').delete().eq(
                'customer_id', customer_id
            ).execute()
        else:
            result = client.table('customers').update({
                'is_active': False
            }).eq('customer_id', customer_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"message": "Customer deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# SELLING RATES (Customer Rates) CRUD
# ============================================================

@router.get("/selling-rates")
def list_selling_rates(
    customer_id: Optional[int] = Query(None),
    route_id: Optional[int] = Query(None),
    service_type_code: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """List selling rates (customer rates)"""
    try:
        client = get_supabase()
        query = client.table('customer_rates').select(
            '*, customers(customer_code, short_name), '
            'master_routes(route_code, origin, destination)',
            count='exact'
        )

        if not include_inactive:
            query = query.eq('is_active', True)
        if customer_id:
            query = query.eq('customer_id', customer_id)
        if route_id:
            query = query.eq('route_id', route_id)
        if service_type_code:
            query = query.eq('service_type_code', service_type_code)

        result = query.order('customer_id').range(offset, offset + limit - 1).execute()
        return {"data": result.data, "total": result.count or len(result.data)}
    except Exception as e:
        logger.error(f"Error listing selling rates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/selling-rates")
def create_selling_rate(data: RateCreate):
    """Create new selling rate (customer rate)"""
    try:
        if not data.customer_id:
            raise HTTPException(status_code=400, detail="customer_id is required")

        client = get_supabase()
        insert_data = {
            'customer_id': data.customer_id,
            'route_id': data.route_id,
            'vehicle_type': data.vehicle_type,
            'price': data.price,
            'currency': data.currency,
            'unit': data.unit or 'TRIP',
            'effective_date': data.effective_date or date.today().isoformat(),
            'expiry_date': data.expiry_date,
            'notes': data.notes,
            'is_active': data.is_active,
            'service_type_code': data.service_type_code,
            'metadata': data.metadata,
            'origin_province': data.origin_province,
            'destination_province': data.destination_province,
        }

        # Remove None values to let DB use defaults
        insert_data = {k: v for k, v in insert_data.items() if v is not None}

        result = client.table('customer_rates').insert(insert_data).execute()

        return {"data": result.data[0], "message": "Selling rate created"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating selling rate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/selling-rates/{rate_id}")
def update_selling_rate(rate_id: int, data: RateUpdate):
    """Update selling rate"""
    try:
        client = get_supabase()
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")

        result = client.table('customer_rates').update(update_data).eq(
            'id', rate_id
        ).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Rate not found")
        return {"data": result.data[0], "message": "Selling rate updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating selling rate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/selling-rates/{rate_id}")
def delete_selling_rate(rate_id: int, hard_delete: bool = Query(False)):
    """Delete selling rate (soft delete by default)"""
    try:
        client = get_supabase()

        if hard_delete:
            result = client.table('customer_rates').delete().eq('id', rate_id).execute()
        else:
            result = client.table('customer_rates').update({
                'is_active': False
            }).eq('id', rate_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Rate not found")
        return {"message": "Selling rate deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting selling rate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# SELLING RATES SUMMARY (grouped by customer)
# ============================================================

@router.get("/selling-rates/summary")
def get_selling_rates_summary():
    """Get summary of selling rates grouped by customer with stats"""
    try:
        client = get_supabase()
        query = client.table('customer_rates').select(
            'customer_id, service_type_code, vehicle_type, effective_date, '
            'customers(customer_id, customer_code, company_name, short_name)'
        ).eq('is_active', True)
        all_data = fetch_all_with_pagination(query)

        cust_map = {}
        for r in all_data:
            cid = r['customer_id']
            if cid not in cust_map:
                customer = r.get('customers', {}) or {}
                cust_map[cid] = {
                    'customer_id': cid,
                    'customer_code': customer.get('customer_code'),
                    'customer_name': customer.get('short_name') or customer.get('company_name'),
                    'rate_count': 0,
                    'service_types': set(),
                    'vehicle_types': set(),
                    'routes_count': set(),
                    'effective_date': r.get('effective_date'),
                }
            cust_map[cid]['rate_count'] += 1
            if r.get('service_type_code'):
                cust_map[cid]['service_types'].add(r['service_type_code'])
            if r.get('vehicle_type'):
                cust_map[cid]['vehicle_types'].add(r['vehicle_type'])
            # Count unique routes
            orig = r.get('origin_province', '')
            dest = r.get('destination_province', '')
            if orig and dest:
                cust_map[cid]['routes_count'].add(f"{orig}→{dest}")

        summary = []
        for v in cust_map.values():
            v['service_types'] = sorted(list(v['service_types']))
            v['vehicle_types'] = sorted(list(v['vehicle_types']))
            v['routes_count'] = len(v['routes_count'])
            summary.append(v)

        summary.sort(key=lambda x: x['customer_name'] or '')
        return {"data": summary, "total": len(summary)}
    except Exception as e:
        logger.error(f"Error getting selling rates summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Vehicle type sort order for matrix display (small → large)
VEHICLE_SORT_ORDER = {
    'Truck 1.25T': 1, 'Truck 2.5T': 2, 'Truck 3.5T': 3,
    'Truck 5T': 4, 'Truck 7T-8T': 5, 'Truck 8T': 5,
    'Truck 9T-10T': 6, 'Truck 10T': 6, 'Truck 15T': 7,
    "CONT 20''": 10, "CONT 40''": 11,
}

# Keywords that identify surcharge rates (not route-based)
SURCHARGE_KEYWORDS = ['chờ giờ', 'lưu ca', 'huỷ', 'hủy', 'phụ phí', 'phụ thu',
                       'cao tốc', 'đường cấm', 'nâng hạ', 'bốc xếp']


def _is_surcharge(rate: dict) -> bool:
    """Check if a rate is a surcharge (not a route rate)"""
    notes = (rate.get('notes') or '').lower()
    return any(kw in notes for kw in SURCHARGE_KEYWORDS)


@router.get("/selling-rates/customer/{customer_id}")
def get_customer_rates_detail(customer_id: int):
    """Get selling rates for a customer in Excel-like matrix format.
    Returns routes grouped by service type, with vehicle types as columns."""
    try:
        client = get_supabase()

        customer_result = client.table('customers').select(
            'customer_id, customer_code, company_name, short_name'
        ).eq('customer_id', customer_id).execute()
        if not customer_result.data:
            raise HTTPException(status_code=404, detail="Customer not found")
        customer = customer_result.data[0]

        query = client.table('customer_rates').select('*').eq(
            'customer_id', customer_id
        ).eq('is_active', True)
        all_rates = fetch_all_with_pagination(query.order('price'))

        # Separate surcharges from route rates
        surcharges = []
        route_rates = []
        for r in all_rates:
            if _is_surcharge(r):
                surcharges.append(r)
            else:
                route_rates.append(r)

        # Group route rates by service_type → route → vehicle_type (matrix)
        svc_map = {}
        all_vehicle_types = set()
        for r in route_rates:
            svc = r.get('service_type_code') or 'OTHER'
            orig = r.get('origin_province') or ''
            dest = r.get('destination_province') or ''
            route_key = f"{orig} → {dest}" if orig and dest else (r.get('notes') or f"Rate #{r['id']}")
            vt = r.get('vehicle_type') or '-'
            all_vehicle_types.add(vt)

            if svc not in svc_map:
                svc_map[svc] = {}
            if route_key not in svc_map[svc]:
                svc_map[svc][route_key] = {'prices': {}, 'notes': r.get('notes'), 'unit': r.get('unit')}
            svc_map[svc][route_key]['prices'][vt] = {
                'price': r.get('price', 0),
                'id': r['id'],
                'unit': r.get('unit'),
            }

        # Sort vehicle types by size
        sorted_vt = sorted(all_vehicle_types,
                           key=lambda x: VEHICLE_SORT_ORDER.get(x, 50))

        # Build structured response per service type
        service_groups = []
        for svc_code, routes in sorted(svc_map.items()):
            route_rows = []
            for route_name, route_data in sorted(routes.items()):
                route_rows.append({
                    'route': route_name,
                    'notes': route_data.get('notes'),
                    'prices': route_data['prices'],  # {vehicle_type: {price, id, unit}}
                })
            service_groups.append({
                'service_type': svc_code,
                'vehicle_types': sorted_vt,
                'routes': route_rows,
                'route_count': len(route_rows),
            })

        # Surcharges grouped by vehicle type too
        surcharge_data = []
        for s in surcharges:
            surcharge_data.append({
                'id': s['id'],
                'notes': s.get('notes') or '-',
                'vehicle_type': s.get('vehicle_type'),
                'price': s.get('price', 0),
                'unit': s.get('unit'),
            })

        return {
            "customer": customer,
            "service_groups": service_groups,
            "vehicle_types": sorted_vt,
            "surcharges": surcharge_data,
            "total": len(all_rates),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer rates detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# BUYING RATES (Vendor Rates) CRUD
# ============================================================

@router.get("/buying-rates")
def list_buying_rates(
    vendor_id: Optional[int] = Query(None),
    route_id: Optional[int] = Query(None),
    service_type_code: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """List buying rates (vendor rates)"""
    try:
        client = get_supabase()
        query = client.table('vendor_rates').select(
            '*, vendors(vendor_id, vendor_code, company_name, short_name)',
            count='exact'
        )

        if not include_inactive:
            query = query.eq('is_active', True)
        if vendor_id:
            query = query.eq('vendor_id', vendor_id)
        if route_id:
            query = query.eq('route_id', route_id)
        if service_type_code:
            query = query.eq('service_type_code', service_type_code)

        result = query.order('vendor_id').range(offset, offset + limit - 1).execute()
        return {"data": result.data, "total": result.count or len(result.data)}
    except Exception as e:
        logger.error(f"Error listing buying rates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buying-rates")
def create_buying_rate(data: RateCreate):
    """Create new buying rate (vendor rate)"""
    try:
        if not data.vendor_id:
            raise HTTPException(status_code=400, detail="vendor_id is required")

        client = get_supabase()
        insert_data = {
            'vendor_id': data.vendor_id,
            'route_id': data.route_id,
            'vehicle_type': data.vehicle_type,
            'price': data.price,
            'currency': data.currency,
            'unit': data.unit or 'TRIP',
            'effective_date': data.effective_date or date.today().isoformat(),
            'expiry_date': data.expiry_date,
            'notes': data.notes,
            'is_active': data.is_active,
            'service_type_code': data.service_type_code,
            'metadata': data.metadata,
            # Trucking specific fields
            'origin_province': data.origin_province,
            'destination_province': data.destination_province,
            'rate_type': data.rate_type or 'STANDARD',
            'temperature_range': data.temperature_range,
            'conditions': data.conditions,
        }

        # Remove None values to let DB use defaults
        insert_data = {k: v for k, v in insert_data.items() if v is not None}

        result = client.table('vendor_rates').insert(insert_data).execute()

        return {"data": result.data[0], "message": "Buying rate created"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating buying rate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/buying-rates/{rate_id}")
def update_buying_rate(rate_id: int, data: RateUpdate):
    """Update buying rate"""
    try:
        client = get_supabase()
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")

        result = client.table('vendor_rates').update(update_data).eq(
            'id', rate_id
        ).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Rate not found")
        return {"data": result.data[0], "message": "Buying rate updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating buying rate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/buying-rates/{rate_id}")
def delete_buying_rate(rate_id: int, hard_delete: bool = Query(False)):
    """Delete buying rate (soft delete by default)"""
    try:
        client = get_supabase()

        if hard_delete:
            result = client.table('vendor_rates').delete().eq('id', rate_id).execute()
        else:
            result = client.table('vendor_rates').update({
                'is_active': False
            }).eq('id', rate_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Rate not found")
        return {"message": "Buying rate deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting buying rate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ROUTES CRUD (bonus - needed for rates)
# ============================================================

@router.get("/routes")
def list_routes(
    include_inactive: bool = Query(False),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500)
):
    """List all routes"""
    try:
        client = get_supabase()
        query = client.table('master_routes').select('*')

        if not include_inactive:
            query = query.eq('is_active', True)
        if search:
            query = query.or_(
                f"route_code.ilike.%{search}%,"
                f"origin.ilike.%{search}%,"
                f"destination.ilike.%{search}%"
            )

        result = query.order('route_code').limit(limit).execute()
        return {"data": result.data, "total": len(result.data)}
    except Exception as e:
        logger.error(f"Error listing routes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# VENDOR RATES SUMMARY (grouped by vendor)
# ============================================================

@router.get("/buying-rates/summary")
def get_vendor_rates_summary():
    """Get summary of rates grouped by vendor with stats"""
    try:
        client = get_supabase()

        # Get all vendor rates with vendor info (with pagination)
        query = client.table('vendor_rates').select(
            'vendor_id, origin_province, destination_province, vehicle_type, '
            'rate_type, effective_date, file_reference_id, '
            'vendors(vendor_id, vendor_code, company_name, short_name)'
        ).eq('is_active', True)
        all_data = fetch_all_with_pagination(query)

        # Group by vendor
        vendor_map = {}
        for r in all_data:
            vid = r['vendor_id']
            if vid not in vendor_map:
                vendor = r.get('vendors', {})
                vendor_map[vid] = {
                    'vendor_id': vid,
                    'vendor_code': vendor.get('vendor_code'),
                    'vendor_name': vendor.get('short_name') or vendor.get('company_name'),
                    'rate_count': 0,
                    'routes': set(),
                    'vehicle_types': set(),
                    'rate_types': set(),
                    'effective_date': r.get('effective_date'),
                    'file_reference_id': r.get('file_reference_id'),
                }
            vendor_map[vid]['rate_count'] += 1
            if r.get('origin_province') and r.get('destination_province'):
                vendor_map[vid]['routes'].add(f"{r['origin_province']} -> {r['destination_province']}")
            if r.get('vehicle_type'):
                vendor_map[vid]['vehicle_types'].add(r['vehicle_type'])
            if r.get('rate_type'):
                vendor_map[vid]['rate_types'].add(r['rate_type'])

        # Convert sets to lists
        summary = []
        for v in vendor_map.values():
            v['routes'] = list(v['routes'])[:5]  # Limit to 5 sample routes
            v['vehicle_types'] = sorted(list(v['vehicle_types']))
            v['rate_types'] = list(v['rate_types'])
            v['routes_count'] = len(v['routes'])
            summary.append(v)

        # Sort by vendor name
        summary.sort(key=lambda x: x['vendor_name'] or '')

        return {"data": summary, "total": len(summary)}
    except Exception as e:
        logger.error(f"Error getting vendor rates summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buying-rates/vendor/{vendor_id}")
def get_vendor_rates_detail(
    vendor_id: int,
    search: Optional[str] = Query(None, description="Search in sub-route (notes)"),
    vehicle_type: Optional[str] = Query(None),
    rate_type: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
):
    """Get detailed rates for a specific vendor, grouped by route and sub-route"""
    try:
        client = get_supabase()

        # Get vendor info
        vendor_result = client.table('vendors').select(
            'vendor_id, vendor_code, company_name, short_name'
        ).eq('vendor_id', vendor_id).execute()

        if not vendor_result.data:
            raise HTTPException(status_code=404, detail="Vendor not found")

        vendor = vendor_result.data[0]

        # Get all rates for this vendor with pagination (Supabase limits to 1000)
        query = client.table('vendor_rates').select('*').eq(
            'vendor_id', vendor_id
        ).eq('is_active', True)

        # Apply filters
        if vehicle_type:
            query = query.eq('vehicle_type', vehicle_type)
        if rate_type:
            query = query.eq('rate_type', rate_type)
        if min_price is not None:
            query = query.gte('price', min_price)
        if max_price is not None:
            query = query.lte('price', max_price)

        # Fetch all data with pagination
        all_rates_data = fetch_all_with_pagination(
            query.order('origin_province').order('destination_province').order('vehicle_type')
        )

        # Create a mock result object for compatibility
        class RatesResult:
            def __init__(self, data):
                self.data = data
        rates_result = RatesResult(all_rates_data)

        # Filter by search (sub-route in notes)
        filtered_data = rates_result.data
        if search:
            search_lower = search.lower()
            filtered_data = [
                r for r in rates_result.data
                if r.get('notes') and search_lower in r['notes'].lower()
            ]

        # Get unique values for filter dropdowns
        all_vehicle_types = sorted(set(r.get('vehicle_type') for r in rates_result.data if r.get('vehicle_type')))
        all_rate_types = list(set(r.get('rate_type') for r in rates_result.data if r.get('rate_type')))
        all_sub_routes = sorted(set(r.get('notes') for r in rates_result.data if r.get('notes')))

        # Group by route (origin_province -> destination_province), then by sub-route (notes)
        routes_map = {}
        for r in filtered_data:
            route_key = f"{r.get('origin_province', 'N/A')} -> {r.get('destination_province', 'N/A')}"
            sub_route = r.get('notes') or 'Không xác định'

            if route_key not in routes_map:
                routes_map[route_key] = {
                    'route': route_key,
                    'origin': r.get('origin_province'),
                    'destination': r.get('destination_province'),
                    'sub_routes': {}
                }

            if sub_route not in routes_map[route_key]['sub_routes']:
                routes_map[route_key]['sub_routes'][sub_route] = {
                    'sub_route': sub_route,
                    'rate_type': r.get('rate_type'),
                    'temperature_range': r.get('temperature_range'),
                    'rates': []
                }

            routes_map[route_key]['sub_routes'][sub_route]['rates'].append({
                'id': r['id'],
                'vehicle_type': r.get('vehicle_type'),
                'price': r.get('price'),
                'currency': r.get('currency', 'VND'),
                'unit': r.get('unit'),
                'conditions': r.get('conditions'),
            })

        # Convert sub_routes dict to list for each route
        routes_list = []
        for route in routes_map.values():
            route['sub_routes'] = sorted(
                list(route['sub_routes'].values()),
                key=lambda x: x['sub_route']
            )
            route['sub_routes_count'] = len(route['sub_routes'])
            routes_list.append(route)

        return {
            "vendor": {
                "id": vendor['vendor_id'],
                "code": vendor['vendor_code'],
                "name": vendor.get('short_name') or vendor.get('company_name'),
            },
            "effective_date": rates_result.data[0].get('effective_date') if rates_result.data else None,
            "file_reference_id": rates_result.data[0].get('file_reference_id') if rates_result.data else None,
            "routes": routes_list,
            "total_rates": len(filtered_data),
            "filters": {
                "vehicle_types": all_vehicle_types,
                "rate_types": all_rate_types,
                "sub_routes": all_sub_routes,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vendor rates detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# COST ITEMS CRUD
# ============================================================

class CostItemCreate(BaseModel):
    cost_code: str
    name_vi: str
    name_en: Optional[str] = None
    category: Optional[str] = None
    region: Optional[str] = None
    service_type: Optional[str] = None
    customer_code: Optional[str] = None
    default_price: float = 0
    selling_price: float = 0
    unit: str = 'UNIT'
    currency: str = 'VND'
    notes: Optional[str] = None
    is_active: bool = True


class CostItemUpdate(BaseModel):
    name_vi: Optional[str] = None
    name_en: Optional[str] = None
    category: Optional[str] = None
    region: Optional[str] = None
    service_type: Optional[str] = None
    customer_code: Optional[str] = None
    default_price: Optional[float] = None
    selling_price: Optional[float] = None
    unit: Optional[str] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/cost-items")
def list_cost_items(
    include_inactive: bool = Query(False),
    category: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """List all cost items with filtering"""
    try:
        client = get_supabase()
        query = client.table('master_cost_items').select('*', count='exact')

        if not include_inactive:
            query = query.eq('is_active', True)
        if category:
            query = query.eq('category', category)
        if region:
            query = query.eq('region', region)
        if search:
            query = query.or_(
                f"cost_code.ilike.%{search}%,"
                f"name_vi.ilike.%{search}%"
            )

        result = query.order('cost_code').range(offset, offset + limit - 1).execute()
        return {"data": result.data, "total": result.count or len(result.data)}
    except Exception as e:
        logger.error(f"Error listing cost items: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cost-items/{cost_item_id}")
def get_cost_item(cost_item_id: int):
    """Get single cost item by ID"""
    try:
        client = get_supabase()
        result = client.table('master_cost_items').select('*').eq(
            'cost_item_id', cost_item_id
        ).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Cost item not found")
        return {"data": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cost item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cost-items")
def create_cost_item(data: CostItemCreate):
    """Create new cost item"""
    try:
        client = get_supabase()
        result = client.table('master_cost_items').insert({
            'cost_code': data.cost_code.upper(),
            'name_vi': data.name_vi,
            'name_en': data.name_en,
            'category': data.category,
            'region': data.region,
            'service_type': data.service_type,
            'customer_code': data.customer_code,
            'default_price': data.default_price,
            'selling_price': data.selling_price,
            'unit': data.unit,
            'currency': data.currency,
            'notes': data.notes,
            'is_active': data.is_active
        }).execute()

        return {"data": result.data[0], "message": "Cost item created"}
    except Exception as e:
        logger.error(f"Error creating cost item: {e}")
        if "duplicate key" in str(e).lower():
            raise HTTPException(status_code=400, detail="Cost code already exists")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/cost-items/{cost_item_id}")
def update_cost_item(cost_item_id: int, data: CostItemUpdate):
    """Update cost item"""
    try:
        client = get_supabase()
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")

        result = client.table('master_cost_items').update(update_data).eq(
            'cost_item_id', cost_item_id
        ).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Cost item not found")
        return {"data": result.data[0], "message": "Cost item updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cost item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cost-items/{cost_item_id}")
def delete_cost_item(cost_item_id: int, hard: bool = Query(False)):
    """Delete or deactivate cost item"""
    try:
        client = get_supabase()
        if hard:
            result = client.table('master_cost_items').delete().eq('cost_item_id', cost_item_id).execute()
        else:
            result = client.table('master_cost_items').update({
                'is_active': False
            }).eq('cost_item_id', cost_item_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Cost item not found")
        return {"message": "Cost item deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cost item: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cost-items/bulk-import")
def bulk_import_cost_items(items: List[CostItemCreate]):
    """Bulk import cost items"""
    try:
        client = get_supabase()
        data_to_insert = [{
            'cost_code': item.cost_code.upper(),
            'name_vi': item.name_vi,
            'name_en': item.name_en,
            'category': item.category,
            'region': item.region,
            'service_type': item.service_type,
            'customer_code': item.customer_code,
            'default_price': item.default_price,
            'selling_price': item.selling_price,
            'unit': item.unit,
            'currency': item.currency,
            'notes': item.notes,
            'is_active': item.is_active
        } for item in items]

        result = client.table('master_cost_items').upsert(
            data_to_insert,
            on_conflict='cost_code'
        ).execute()

        return {"message": f"Imported {len(result.data)} cost items", "count": len(result.data)}
    except Exception as e:
        logger.error(f"Error bulk importing cost items: {e}")
        raise HTTPException(status_code=500, detail=str(e))
