# backend/app/api/search.py
"""
Search API endpoints for customers, vendors, and vehicles.
Uses raw SQL queries via DatabaseSession.
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
import logging

from app.db.session import get_db, DatabaseSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.get("/customers")
def search_customers(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(20, ge=1, le=100),
    db: DatabaseSession = Depends(get_db)
):
    """
    Search customers by code or name.
    """
    try:
        search_term = f"%{q}%"
        
        db.execute("""
            SELECT customer_id as id, customer_code as code, 
                   COALESCE(short_name, company_name) as name,
                   company_name as full_name,
                   address, contact_phone as phone
            FROM customers 
            WHERE is_active = true
              AND (customer_code ILIKE %s 
                   OR company_name ILIKE %s 
                   OR short_name ILIKE %s)
            ORDER BY customer_code
            LIMIT %s
        """, (search_term, search_term, search_term, limit))
        
        results = db.fetchall()
        
        return {
            "results": [dict(r) for r in results],
            "total": len(results)
        }
    except Exception as e:
        logger.error(f"Customer search error: {e}")
        return {"results": [], "total": 0, "error": str(e)}


@router.get("/vendors")
def search_vendors(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(20, ge=1, le=100),
    db: DatabaseSession = Depends(get_db)
):
    """
    Search vendors by code or name.
    """
    try:
        search_term = f"%{q}%"
        
        db.execute("""
            SELECT vendor_id as id, vendor_code as code, 
                   vendor_name as name,
                   phone, address
            FROM vendors 
            WHERE is_active = true
              AND (vendor_code ILIKE %s OR vendor_name ILIKE %s)
            ORDER BY vendor_code
            LIMIT %s
        """, (search_term, search_term, limit))
        
        results = db.fetchall()
        
        return {
            "results": [dict(r) for r in results],
            "total": len(results)
        }
    except Exception as e:
        logger.error(f"Vendor search error: {e}")
        return {"results": [], "total": 0, "error": str(e)}


@router.get("/vehicles")
def search_vehicles(
    q: str = Query(..., min_length=1, description="Search term"),
    vendor_id: Optional[int] = Query(None, description="Filter by vendor ID"),
    limit: int = Query(20, ge=1, le=100),
    db: DatabaseSession = Depends(get_db)
):
    """
    Search vehicles by license plate or driver name.
    """
    try:
        search_term = f"%{q}%"
        
        if vendor_id:
            db.execute("""
                SELECT v.vehicle_id as id, v.license_plate, 
                       v.vehicle_type, v.vendor_id,
                       d.driver_name, d.phone as driver_phone
                FROM vehicles v
                LEFT JOIN drivers d ON v.vehicle_id = d.vehicle_id AND d.is_active = true
                WHERE v.is_active = true
                  AND v.vendor_id = %s
                  AND (v.license_plate ILIKE %s OR d.driver_name ILIKE %s)
                ORDER BY v.license_plate
                LIMIT %s
            """, (vendor_id, search_term, search_term, limit))
        else:
            db.execute("""
                SELECT v.vehicle_id as id, v.license_plate, 
                       v.vehicle_type, v.vendor_id,
                       d.driver_name, d.phone as driver_phone
                FROM vehicles v
                LEFT JOIN drivers d ON v.vehicle_id = d.vehicle_id AND d.is_active = true
                WHERE v.is_active = true
                  AND (v.license_plate ILIKE %s OR d.driver_name ILIKE %s)
                ORDER BY v.license_plate
                LIMIT %s
            """, (search_term, search_term, limit))
        
        results = db.fetchall()
        
        return {
            "results": [dict(r) for r in results],
            "total": len(results)
        }
    except Exception as e:
        logger.error(f"Vehicle search error: {e}")
        return {"results": [], "total": 0, "error": str(e)}


@router.get("/drivers")
def search_drivers(
    q: str = Query(..., min_length=1, description="Search term"),
    vendor_id: Optional[int] = Query(None, description="Filter by vendor ID"),
    limit: int = Query(20, ge=1, le=100),
    db: DatabaseSession = Depends(get_db)
):
    """
    Search drivers by name or phone.
    """
    try:
        search_term = f"%{q}%"
        
        if vendor_id:
            db.execute("""
                SELECT driver_id as id, driver_name as name, 
                       phone, cccd, vendor_id
                FROM drivers 
                WHERE is_active = true
                  AND vendor_id = %s
                  AND (driver_name ILIKE %s OR phone ILIKE %s)
                ORDER BY driver_name
                LIMIT %s
            """, (vendor_id, search_term, search_term, limit))
        else:
            db.execute("""
                SELECT driver_id as id, driver_name as name, 
                       phone, cccd, vendor_id
                FROM drivers 
                WHERE is_active = true
                  AND (driver_name ILIKE %s OR phone ILIKE %s)
                ORDER BY driver_name
                LIMIT %s
            """, (search_term, search_term, limit))
        
        results = db.fetchall()
        
        return {
            "results": [dict(r) for r in results],
            "total": len(results)
        }
    except Exception as e:
        logger.error(f"Driver search error: {e}")
        return {"results": [], "total": 0, "error": str(e)}
