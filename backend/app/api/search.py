# backend/app/api/search.py
"""
Search API endpoints for customers, vendors, and vehicles.
Uses raw SQL queries via DatabaseSession.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from app.db.session import get_db, DatabaseSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["Search"])


# ============================================================
# CREATE MODELS (operator-level, no admin auth)
# ============================================================

class CreateCustomerRequest(BaseModel):
    customer_code: str
    company_name: str
    short_name: Optional[str] = None
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    tax_code: Optional[str] = None

class CreateVendorRequest(BaseModel):
    vendor_code: str
    company_name: str
    short_name: Optional[str] = None
    address: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    tax_code: Optional[str] = None


@router.post("/customers/create")
def create_customer(data: CreateCustomerRequest, db: DatabaseSession = Depends(get_db)):
    """Create new customer (operator-level access)"""
    try:
        db.execute("""
            INSERT INTO customers (customer_code, company_name, short_name, address,
                                   contact_phone, contact_email, tax_code, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, true)
            RETURNING customer_id, customer_code, company_name, short_name
        """, (data.customer_code.upper(), data.company_name,
              data.short_name or data.customer_code.upper(),
              data.address, data.contact_phone, data.contact_email, data.tax_code))
        result = db.fetchone()
        db.commit()
        return {"data": dict(result), "message": "Customer created"}
    except Exception as e:
        logger.error(f"Create customer error: {e}")
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(status_code=400, detail=f"Customer code {data.customer_code} already exists")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vendors/create")
def create_vendor(data: CreateVendorRequest, db: DatabaseSession = Depends(get_db)):
    """Create new vendor (operator-level access)"""
    try:
        db.execute("""
            INSERT INTO vendors (vendor_code, company_name, short_name, address,
                                 contact_phone, contact_email, tax_code, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, true)
            RETURNING vendor_id, vendor_code, company_name, short_name
        """, (data.vendor_code.upper(), data.company_name,
              data.short_name or data.vendor_code.upper(),
              data.address, data.contact_phone, data.contact_email, data.tax_code))
        result = db.fetchone()
        db.commit()
        return {"data": dict(result), "message": "Vendor created"}
    except Exception as e:
        logger.error(f"Create vendor error: {e}")
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(status_code=400, detail=f"Vendor code {data.vendor_code} already exists")
        raise HTTPException(status_code=500, detail=str(e))


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
    Vehicles are stored in the drivers table (license_plate + vehicle_type columns).
    """
    try:
        search_term = f"%{q}%"
        
        if vendor_id:
            db.execute("""
                SELECT d.driver_id as id, d.license_plate, 
                       d.vehicle_type, d.vendor_id,
                       d.full_name as driver_name, d.phone as driver_phone
                FROM drivers d
                WHERE d.is_active = true
                  AND d.vendor_id = %s
                  AND (d.license_plate ILIKE %s OR d.full_name ILIKE %s)
                ORDER BY d.license_plate
                LIMIT %s
            """, (vendor_id, search_term, search_term, limit))
        else:
            db.execute("""
                SELECT d.driver_id as id, d.license_plate, 
                       d.vehicle_type, d.vendor_id,
                       d.full_name as driver_name, d.phone as driver_phone
                FROM drivers d
                WHERE d.is_active = true
                  AND (d.license_plate ILIKE %s OR d.full_name ILIKE %s)
                ORDER BY d.license_plate
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
    Search jobs by job_no, customer_code, customer_name,
    or document numbers (cd_no, bl_awb_no, co_no, invoice_numbers, GNT in cost_name).
    """
    try:
        search_term = f"%{q}%"

        db.execute("""
            SELECT DISTINCT
                j.job_id, j.job_no, j.status_code, j.etd,
                j.created_at, j.total_revenue,
                c.customer_code,
                COALESCE(c.short_name, c.company_name) as customer_name,
                (SELECT js2.service_type_code
                 FROM job_services js2
                 WHERE js2.job_id = j.job_id
                 ORDER BY js2.svc_id LIMIT 1) as service_type,
                -- Include matched document info for display
                js.cd_no, js.bl_awb_no, js.co_no, js.invoice_numbers
            FROM jobs j
            LEFT JOIN customers c ON j.customer_id = c.customer_id
            LEFT JOIN job_services js ON j.job_id = js.job_id
            LEFT JOIN job_costs jc ON j.job_id = jc.job_id
            WHERE j.job_no ILIKE %s
               OR c.customer_code ILIKE %s
               OR c.short_name ILIKE %s
               OR c.company_name ILIKE %s
               OR js.cd_no ILIKE %s
               OR js.bl_awb_no ILIKE %s
               OR js.co_no ILIKE %s
               OR js.invoice_numbers ILIKE %s
               OR jc.cost_name ILIKE %s
            ORDER BY j.created_at DESC
            LIMIT %s
        """, (search_term,) * 9 + (limit,))

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
                SELECT driver_id as id, full_name as name,
                       phone, id_card as cccd, vendor_id, license_plate
                FROM drivers
                WHERE is_active = true
                  AND vendor_id = %s
                  AND (full_name ILIKE %s OR phone ILIKE %s OR license_plate ILIKE %s)
                ORDER BY full_name
                LIMIT %s
            """, (vendor_id, search_term, search_term, search_term, limit))
        else:
            db.execute("""
                SELECT driver_id as id, full_name as name,
                       phone, id_card as cccd, vendor_id, license_plate
                FROM drivers
                WHERE is_active = true
                  AND (full_name ILIKE %s OR phone ILIKE %s OR license_plate ILIKE %s)
                ORDER BY full_name
                LIMIT %s
            """, (search_term, search_term, search_term, limit))

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
    service_type: Optional[str] = Query(None, description="service_type_code filter, e.g. SEA_IMP"),
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

        # Optional service_type filter — only return jobs that have at least
        # one job_services row matching the selected service_type_code.
        svc_type_condition = ""
        if service_type:
            svc_type_condition = (
                " AND EXISTS (SELECT 1 FROM job_services js_f "
                "             WHERE js_f.job_id = j.job_id "
                "               AND js_f.service_type_code = %s)"
            )

        if entity_type == "customer":
            query = f"""
                SELECT j.job_id, j.job_no, j.status_code, j.etd, j.created_at,
                       j.total_revenue, j.total_cost, j.profit,
                       c.customer_code, c.short_name as customer_name,
                       (SELECT array_agg(DISTINCT js.service_type_code)
                        FROM job_services js WHERE js.job_id = j.job_id) as service_types
                FROM jobs j
                JOIN customers c ON j.customer_id = c.customer_id
                WHERE j.customer_id = %s {date_conditions}{svc_type_condition}
                ORDER BY j.created_at DESC
            """
            args = [entity_id, *params]
            if service_type:
                args.append(service_type)
            db.execute(query, tuple(args))
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
                WHERE js.vendor_id = %s {date_conditions}{svc_type_condition}
                ORDER BY j.created_at DESC
            """
            args = [entity_id, entity_id, *params]
            if service_type:
                args.append(service_type)
            db.execute(query, tuple(args))

        raw_results = db.fetchall()
        results = []

        # Collect all job_ids for batch reimbursement query
        all_job_ids = [dict(r)['job_id'] for r in raw_results]

        # Batch fetch reimbursement (at-cost / chi hộ) totals — split selling vs buying
        reimb_rev_map = {}
        reimb_cost_map = {}
        if all_job_ids:
            placeholders = ','.join(['%s'] * len(all_job_ids))
            db.execute(f"""
                SELECT job_id,
                       SUM(selling_amount) as reimb_rev,
                       SUM(buying_amount)  as reimb_cost
                FROM job_costs
                WHERE job_id IN ({placeholders}) AND is_reimbursement = true
                GROUP BY job_id
            """, tuple(all_job_ids))
            for r in db.fetchall():
                reimb_rev_map[r['job_id']] = float(r['reimb_rev'] or 0)
                reimb_cost_map[r['job_id']] = float(r['reimb_cost'] or 0)

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

            reimb_rev = reimb_rev_map.get(job_id, 0)
            reimb_cost = reimb_cost_map.get(job_id, 0)
            # jobs.total_revenue / total_cost are kept by a DB trigger that
            # already excludes is_reimbursement rows — do NOT subtract again.
            total_rev = float(job.get('total_revenue') or 0)
            total_cost = float(job.get('total_cost') or 0)
            job['reimbursement_total'] = reimb_rev          # legacy name for BC
            job['reimbursement_cost_total'] = reimb_cost
            job['net_revenue'] = total_rev                  # already net of chi hộ
            job['net_cost'] = total_cost
            job['profit'] = total_rev - total_cost
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


@router.get("/check-duplicate-documents")
def check_duplicate_documents(
    doc_value: str = Query(..., min_length=1, description="Document number to check"),
    exclude_svc_id: Optional[int] = Query(None, description="Exclude this service ID (for edits)"),
    db: DatabaseSession = Depends(get_db)
):
    """
    Check if a document number already exists in the system.
    Searches across cd_no, bl_awb_no, co_no, invoice_numbers in job_services.
    Uses indexed columns for fast lookup (<1ms).
    """
    try:
        val = doc_value.strip()
        if not val:
            return {"duplicates": []}

        exclude_clause = ""
        params = [val, val, val, f"%{val}%"]
        if exclude_svc_id:
            exclude_clause = "AND js.svc_id != %s"
            params.append(exclude_svc_id)

        db.execute(f"""
            SELECT DISTINCT j.job_id, j.job_no, j.etd,
                   c.customer_code, COALESCE(c.short_name, c.company_name) as customer_name,
                   js.cd_no, js.bl_awb_no, js.co_no, js.invoice_numbers,
                   CASE
                     WHEN js.cd_no = %s THEN 'cd_no'
                     WHEN js.bl_awb_no = %s THEN 'bl_awb_no'
                     WHEN js.co_no = %s THEN 'co_no'
                     WHEN js.invoice_numbers ILIKE %s THEN 'invoice_numbers'
                   END as matched_field
            FROM job_services js
            JOIN jobs j ON js.job_id = j.job_id
            LEFT JOIN customers c ON j.customer_id = c.customer_id
            WHERE (js.cd_no = %s OR js.bl_awb_no = %s OR js.co_no = %s OR js.invoice_numbers ILIKE %s)
            {exclude_clause}
            ORDER BY j.etd DESC
            LIMIT 10
        """, (*params, val, val, val, f"%{val}%", *([exclude_svc_id] if exclude_svc_id else [])))

        results = [dict(r) for r in db.fetchall()]
        return {"duplicates": results, "total": len(results)}
    except Exception as e:
        logger.error(f"Check duplicate docs error: {e}")
        return {"duplicates": [], "error": str(e)}
