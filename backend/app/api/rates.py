"""
Rates API - Customer and vendor rate lookup endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Any
import logging
from datetime import date

from app.db.supabase_client import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rates", tags=["Rates"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class CustomerRateCreate(BaseModel):
    customer_id: int
    vehicle_type: Optional[str] = None
    price: float
    origin_province: Optional[str] = None
    destination_province: Optional[str] = None
    notes: Optional[str] = None
    service_type_code: Optional[str] = None
    currency: Optional[str] = "VND"
    unit: Optional[str] = None
    metadata: Optional[Any] = None


class VendorRateCreate(BaseModel):
    vendor_id: int
    vehicle_type: Optional[str] = None
    price: float
    origin_province: Optional[str] = None
    destination_province: Optional[str] = None
    notes: Optional[str] = None
    currency: Optional[str] = "VND"
    unit: Optional[str] = None
    rate_code: Optional[str] = None
    rate_type: Optional[str] = None
    conditions: Optional[str] = None


# ---------------------------------------------------------------------------
# GET /api/rates/customer/{customer_id}
# ---------------------------------------------------------------------------

@router.get("/customer/{customer_id}")
async def get_customer_rates(
    customer_id: int,
    vehicle_type: Optional[str] = Query(None),
    origin: Optional[str] = Query(None),
    destination: Optional[str] = Query(None),
    service_type_code: Optional[str] = Query(None),
):
    """
    Lookup active selling rates for a customer.
    Supports optional fuzzy filtering on vehicle_type, origin, destination, service_type_code.
    Sorted by effective_date DESC.
    """
    try:
        client = get_supabase()

        query = client.table("customer_rates").select(
            "id, customer_id, service_id, route_id, vehicle_type, price, currency, unit, "
            "vendor_rate_id, margin_percent, effective_date, expiry_date, contract_number, "
            "is_active, created_at, notes, service_type_code, metadata, "
            "origin_province, destination_province, file_reference_id"
        ).eq("customer_id", customer_id).eq("is_active", True)

        if vehicle_type:
            query = query.ilike("vehicle_type", f"%{vehicle_type}%")
        if origin:
            query = query.ilike("origin_province", f"%{origin}%")
        if destination:
            query = query.ilike("destination_province", f"%{destination}%")
        if service_type_code:
            query = query.ilike("service_type_code", f"%{service_type_code}%")

        result = query.order("effective_date", desc=True).execute()

        return {
            "customer_id": customer_id,
            "count": len(result.data or []),
            "rates": result.data or [],
        }

    except Exception as e:
        logger.error(f"get_customer_rates error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /api/rates/vendor/{vendor_id}
# ---------------------------------------------------------------------------

@router.get("/vendor/{vendor_id}")
async def get_vendor_rates(
    vendor_id: int,
    vehicle_type: Optional[str] = Query(None),
    origin: Optional[str] = Query(None),
    destination: Optional[str] = Query(None),
):
    """
    Lookup active buying rates for a vendor.
    Supports optional fuzzy filtering on vehicle_type, origin, destination.
    Sorted by effective_date DESC.
    """
    try:
        client = get_supabase()

        query = client.table("vendor_rates").select(
            "id, vendor_id, service_id, route_id, vehicle_type, price, currency, unit, "
            "effective_date, expiry_date, min_weight, max_weight, conditions, "
            "is_active, created_at, notes, rate_code, rate_type"
        ).eq("vendor_id", vendor_id).eq("is_active", True)

        if vehicle_type:
            query = query.ilike("vehicle_type", f"%{vehicle_type}%")
        if origin:
            # vendor_rates may store origin/destination in route_id or conditions;
            # check notes and conditions as fallback since there are no province columns
            # If the table has origin_province / destination_province columns, use them:
            try:
                query = query.ilike("origin_province", f"%{origin}%")
            except Exception:
                pass
        if destination:
            try:
                query = query.ilike("destination_province", f"%{destination}%")
            except Exception:
                pass

        result = query.order("effective_date", desc=True).execute()

        return {
            "vendor_id": vendor_id,
            "count": len(result.data or []),
            "rates": result.data or [],
        }

    except Exception as e:
        logger.error(f"get_vendor_rates error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /api/rates/lookup
# ---------------------------------------------------------------------------

@router.get("/lookup")
async def lookup_rates(
    customer_id: int = Query(...),
    vendor_id: int = Query(...),
    vehicle_type: Optional[str] = Query(None),
    origin: Optional[str] = Query(None),
    destination: Optional[str] = Query(None),
):
    """
    Smart rate lookup: returns both selling (customer) and buying (vendor) rates
    plus calculated margin. Uses fuzzy (ILIKE) matching on origin/destination.

    Response: { selling, buying, margin, margin_pct }
    """
    try:
        client = get_supabase()

        # ---- Customer (selling) side ----
        cq = client.table("customer_rates").select(
            "id, customer_id, vehicle_type, price, currency, unit, notes, "
            "service_type_code, origin_province, destination_province, "
            "effective_date, is_active, margin_percent"
        ).eq("customer_id", customer_id).eq("is_active", True)

        if vehicle_type:
            cq = cq.ilike("vehicle_type", f"%{vehicle_type}%")
        if origin:
            cq = cq.ilike("origin_province", f"%{origin}%")
        if destination:
            cq = cq.ilike("destination_province", f"%{destination}%")

        cr = cq.order("effective_date", desc=True).limit(1).execute()
        selling = cr.data[0] if cr.data else None

        # ---- Vendor (buying) side ----
        vq = client.table("vendor_rates").select(
            "id, vendor_id, vehicle_type, price, currency, unit, notes, "
            "rate_code, rate_type, effective_date, is_active"
        ).eq("vendor_id", vendor_id).eq("is_active", True)

        if vehicle_type:
            vq = vq.ilike("vehicle_type", f"%{vehicle_type}%")

        vr = vq.order("effective_date", desc=True).limit(1).execute()
        buying = vr.data[0] if vr.data else None

        # ---- Margin calculation ----
        margin: Optional[float] = None
        margin_pct: Optional[float] = None

        if selling and buying:
            sell_price = float(selling.get("price") or 0)
            buy_price = float(buying.get("price") or 0)
            margin = round(sell_price - buy_price, 2)
            if sell_price > 0:
                margin_pct = round(margin / sell_price * 100, 2)

        return {
            "selling": selling,
            "buying": buying,
            "margin": margin,
            "margin_pct": margin_pct,
        }

    except Exception as e:
        logger.error(f"lookup_rates error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# POST /api/rates/customer  (create or update)
# ---------------------------------------------------------------------------

@router.post("/customer")
async def upsert_customer_rate(body: CustomerRateCreate):
    """
    Create or update a customer selling rate.
    Duplicate key: same customer_id + vehicle_type + origin_province + destination_province + service_type_code.
    If duplicate found, updates price/notes/metadata instead of inserting new row.
    No admin auth required.
    """
    try:
        client = get_supabase()

        # Build duplicate-check query
        dup_q = client.table("customer_rates").select("id").eq("customer_id", body.customer_id)

        if body.vehicle_type is not None:
            dup_q = dup_q.eq("vehicle_type", body.vehicle_type)
        else:
            dup_q = dup_q.is_("vehicle_type", "null")

        if body.origin_province is not None:
            dup_q = dup_q.eq("origin_province", body.origin_province)
        else:
            dup_q = dup_q.is_("origin_province", "null")

        if body.destination_province is not None:
            dup_q = dup_q.eq("destination_province", body.destination_province)
        else:
            dup_q = dup_q.is_("destination_province", "null")

        if body.service_type_code is not None:
            dup_q = dup_q.eq("service_type_code", body.service_type_code)
        else:
            dup_q = dup_q.is_("service_type_code", "null")

        dup_result = dup_q.limit(1).execute()

        payload = {
            "customer_id": body.customer_id,
            "vehicle_type": body.vehicle_type,
            "price": body.price,
            "origin_province": body.origin_province,
            "destination_province": body.destination_province,
            "notes": body.notes,
            "service_type_code": body.service_type_code,
            "currency": body.currency,
            "unit": body.unit,
            "metadata": body.metadata,
            "is_active": True,
            "effective_date": date.today().isoformat(),
        }

        if dup_result.data:
            existing_id = dup_result.data[0]["id"]
            # Update only mutable fields
            update_payload = {
                "price": body.price,
                "notes": body.notes,
                "currency": body.currency,
                "unit": body.unit,
                "metadata": body.metadata,
                "effective_date": date.today().isoformat(),
            }
            result = client.table("customer_rates").update(update_payload).eq("id", existing_id).execute()
            action = "updated"
        else:
            result = client.table("customer_rates").insert(payload).execute()
            action = "created"

        if not result.data:
            raise HTTPException(status_code=500, detail="DB operation returned no data")

        return {"action": action, "rate": result.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"upsert_customer_rate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# POST /api/rates/vendor  (create or update)
# ---------------------------------------------------------------------------

@router.post("/vendor")
async def upsert_vendor_rate(body: VendorRateCreate):
    """
    Create or update a vendor buying rate.
    Duplicate key: same vendor_id + vehicle_type + rate_code (if provided).
    If duplicate found, updates price/notes/conditions instead of inserting.
    No admin auth required.
    """
    try:
        client = get_supabase()

        # Build duplicate-check query
        dup_q = client.table("vendor_rates").select("id").eq("vendor_id", body.vendor_id)

        if body.vehicle_type is not None:
            dup_q = dup_q.eq("vehicle_type", body.vehicle_type)
        else:
            dup_q = dup_q.is_("vehicle_type", "null")

        if body.rate_code is not None:
            dup_q = dup_q.eq("rate_code", body.rate_code)
        else:
            dup_q = dup_q.is_("rate_code", "null")

        dup_result = dup_q.limit(1).execute()

        payload = {
            "vendor_id": body.vendor_id,
            "vehicle_type": body.vehicle_type,
            "price": body.price,
            "notes": body.notes,
            "currency": body.currency,
            "unit": body.unit,
            "rate_code": body.rate_code,
            "rate_type": body.rate_type,
            "conditions": body.conditions,
            "is_active": True,
            "effective_date": date.today().isoformat(),
        }

        if dup_result.data:
            existing_id = dup_result.data[0]["id"]
            update_payload = {
                "price": body.price,
                "notes": body.notes,
                "currency": body.currency,
                "unit": body.unit,
                "conditions": body.conditions,
                "rate_type": body.rate_type,
                "effective_date": date.today().isoformat(),
            }
            result = client.table("vendor_rates").update(update_payload).eq("id", existing_id).execute()
            action = "updated"
        else:
            result = client.table("vendor_rates").insert(payload).execute()
            action = "created"

        if not result.data:
            raise HTTPException(status_code=500, detail="DB operation returned no data")

        return {"action": action, "rate": result.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"upsert_vendor_rate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
