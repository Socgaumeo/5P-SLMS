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
                   COALESCE(short_name, company_name) as name,
                   contact_phone as phone, address
            FROM vendors
            WHERE is_active = true
              AND (vendor_code ILIKE %s OR short_name ILIKE %s OR company_name ILIKE %s)
            ORDER BY vendor_code
            LIMIT %s
        """, (search_term, search_term, search_term, limit))
        
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


@router.get("/jobs")
def search_jobs(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(10, ge=1, le=50),
    db: DatabaseSession = Depends(get_db)
):
    """
    Search jobs by job_no, customer_code, or customer_name.
    Returns results for header search dropdown.
    """
    try:
        search_term = f"%{q}%"

        db.execute("""
            SELECT DISTINCT
                j.job_id, j.job_no, j.status_code, j.etd,
                j.created_at,
                c.customer_code,
                COALESCE(c.short_name, c.company_name) as customer_name,
                (SELECT js.service_type_code
                 FROM job_services js
                 WHERE js.job_id = j.job_id
                 ORDER BY js.svc_id LIMIT 1) as service_type
            FROM jobs j
            LEFT JOIN customers c ON j.customer_id = c.customer_id
            WHERE j.job_no ILIKE %s
               OR c.customer_code ILIKE %s
               OR c.short_name ILIKE %s
               OR c.company_name ILIKE %s
            ORDER BY j.created_at DESC
            LIMIT %s
        """, (search_term, search_term, search_term, search_term, limit))

        results = db.fetchall()

        return {
            "results": [dict(r) for r in results],
            "total": len(results)
        }
    except Exception as e:
        logger.error(f"Job search error: {e}")
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


@router.get("/jobs-by-entity")
def search_jobs_by_entity(
    entity_type: str = Query(..., description="customer or vendor"),
    entity_id: int = Query(..., description="Customer or Vendor ID"),
    from_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    to_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    month: Optional[str] = Query(None, description="Month filter YYYY-MM"),
    status: Optional[str] = Query(None, description="Status filter"),
    db: DatabaseSession = Depends(get_db)
):
    """
    Get ALL jobs for a customer or vendor (no limit, for export).
    Returns complete job data with revenue/cost totals calculated from service_details.
    """
    import json

    try:
        if entity_type not in ["customer", "vendor"]:
            return {"results": [], "error": "entity_type must be customer or vendor"}

        # Build date filters
        date_conditions = ""
        params = []

        if month:
            year, mon = month.split('-')
            import calendar
            last_day = calendar.monthrange(int(year), int(mon))[1]
            date_conditions = " AND j.etd >= %s AND j.etd <= %s"
            params.extend([f"{year}-{mon}-01", f"{year}-{mon}-{last_day}"])
        else:
            if from_date:
                date_conditions += " AND j.etd >= %s"
                params.append(from_date)
            if to_date:
                date_conditions += " AND j.etd <= %s"
                params.append(to_date)

        if status:
            date_conditions += " AND j.status_code = %s"
            params.append(status.upper())

        if entity_type == "customer":
            query = f"""
                SELECT j.job_id, j.job_no, j.status_code, j.etd, j.created_at,
                       j.total_revenue, j.total_cost, j.profit,
                       c.customer_code, c.short_name as customer_name,
                       (SELECT array_agg(DISTINCT js.service_type_code)
                        FROM job_services js WHERE js.job_id = j.job_id) as service_types
                FROM jobs j
                JOIN customers c ON j.customer_id = c.customer_id
                WHERE j.customer_id = %s {date_conditions}
                ORDER BY j.created_at DESC
            """
            db.execute(query, (entity_id, *params))
        else:
            # Vendor: find jobs where vendor provided services
            query = f"""
                SELECT DISTINCT j.job_id, j.job_no, j.status_code, j.etd, j.created_at,
                       j.total_revenue, j.total_cost, j.profit,
                       c.customer_code, c.short_name as customer_name,
                       v.vendor_code, v.short_name as vendor_name,
                       (SELECT array_agg(DISTINCT js.service_type_code)
                        FROM job_services js WHERE js.job_id = j.job_id AND js.vendor_id = %s) as service_types
                FROM jobs j
                JOIN customers c ON j.customer_id = c.customer_id
                JOIN job_services js ON j.job_id = js.job_id
                JOIN vendors v ON js.vendor_id = v.vendor_id
                WHERE js.vendor_id = %s {date_conditions}
                ORDER BY j.created_at DESC
            """
            db.execute(query, (entity_id, entity_id, *params))

        raw_results = db.fetchall()
        results = []

        # For each job, calculate totals from service_details if jobs table has 0
        for row in raw_results:
            job = dict(row)
            job_id = job['job_id']

            # If totals are 0, calculate from service_details
            if (job.get('total_revenue') or 0) == 0 and (job.get('total_cost') or 0) == 0:
                db.execute("""
                    SELECT service_details FROM job_services WHERE job_id = %s
                """, (job_id,))
                svc_rows = db.fetchall()

                calc_revenue = 0
                calc_cost = 0
                for svc in svc_rows:
                    details = svc.get('service_details') or {}
                    if isinstance(details, str):
                        try:
                            details = json.loads(details)
                        except Exception:
                            details = {}
                    calc_revenue += float(details.get('selling_price') or details.get('total_revenue') or 0)
                    calc_cost += float(details.get('buying_price') or details.get('total_cost') or 0)

                job['total_revenue'] = calc_revenue
                job['total_cost'] = calc_cost
                job['profit'] = calc_revenue - calc_cost

            results.append(job)

        # Get entity info
        entity_info = {}
        if entity_type == "customer":
            db.execute("""
                SELECT customer_id as id, customer_code as code,
                       short_name as name, company_name
                FROM customers WHERE customer_id = %s
            """, (entity_id,))
            row = db.fetchone()
            if row:
                entity_info = dict(row)
        else:
            db.execute("""
                SELECT vendor_id as id, vendor_code as code,
                       short_name as name, company_name
                FROM vendors WHERE vendor_id = %s
            """, (entity_id,))
            row = db.fetchone()
            if row:
                entity_info = dict(row)

        return {
            "results": results,
            "total": len(results),
            "entity": entity_info,
            "entity_type": entity_type
        }
    except Exception as e:
        logger.error(f"Jobs by entity search error: {e}")
        return {"results": [], "total": 0, "error": str(e)}
