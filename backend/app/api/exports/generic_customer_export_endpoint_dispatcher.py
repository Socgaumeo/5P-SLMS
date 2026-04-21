"""
Generic customer-export endpoint that dispatches to the right family
renderer based on registry config.

Single endpoint `/api/jobs/exports/generic` handles all non-DAINESE/MEIKO
customers (Family A trucking, Family B handling, plus future Family C/D).

The endpoint reads the customer registry to:
  1. Determine which family renderer to use (trucking/handling/customs/intl)
  2. Pull the right service_types from DB
  3. Pass per-customer config (sheet name, title, VAT, options) to renderer
"""

import logging
import tempfile
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.db.session import get_db, DatabaseSession

from app.api.exports.common_bang_ke_styling_and_formatting import DEFAULT_LOGO_PATH
from app.api.exports.generic_template_renderer_family_a_trucking import (
    render_trucking_workbook,
)
from app.api.exports.generic_template_renderer_family_b_handling import (
    render_handling_workbook,
)
from app.api.exports.generic_template_renderer_family_c_customs import (
    render_customs_workbook,
)


logger = logging.getLogger(__name__)
router = APIRouter()


# ---------- Family-name → renderer mapping ----------

FAMILY_RENDERERS = {
    "trucking": render_trucking_workbook,
    "handling": render_handling_workbook,
    "customs": render_customs_workbook,        # Family C — customs multi-sheet
    # 'international': render_intl_workbook,   # TODO Family D
}


# ---------- Data fetch (mirrors DAINESE pattern) ----------

def _fetch_jobs_services_costs(
    db: DatabaseSession,
    customer_id: int,
    service_types: List[str],
    month: Optional[str],
    from_date: Optional[str],
    to_date: Optional[str],
    service_type_filter: Optional[str] = None,
) -> tuple[List[Dict], List[Dict], Dict[int, List[Dict]]]:
    """Same data-fetch logic as DAINESE — kept independent to avoid coupling."""
    date_clause = ""
    params: List[Any] = [customer_id]

    if month:
        import calendar
        year, mon = month.split("-")
        last_day = calendar.monthrange(int(year), int(mon))[1]
        date_clause = " AND j.etd >= %s AND j.etd <= %s"
        params.extend([f"{year}-{mon}-01", f"{year}-{mon}-{last_day}"])
    else:
        if from_date:
            date_clause += " AND j.etd >= %s"
            params.append(from_date)
        if to_date:
            date_clause += " AND j.etd <= %s"
            params.append(to_date)

    db.execute(
        f"""
        SELECT j.job_id, j.job_no, j.status_code, j.etd, j.created_at, j.invoice_number
        FROM jobs j
        WHERE j.customer_id = %s {date_clause}
        ORDER BY j.created_at
        """,
        tuple(params),
    )
    jobs = [dict(r) for r in db.fetchall()]
    if not jobs:
        return [], [], {}

    job_ids = [j["job_id"] for j in jobs]

    # Apply optional explicit service_type filter (narrow registry's default list)
    effective_types = service_types
    if service_type_filter:
        effective_types = [service_type_filter]

    type_ph = ",".join(["%s"] * len(effective_types))
    job_ph = ",".join(["%s"] * len(job_ids))

    db.execute(
        f"""
        SELECT js.*, v.vendor_code, v.short_name AS vendor_name
        FROM job_services js
        LEFT JOIN vendors v ON js.vendor_id = v.vendor_id
        WHERE js.job_id IN ({job_ph})
          AND js.service_type_code IN ({type_ph})
        ORDER BY js.scheduled_date
        """,
        tuple(job_ids + list(effective_types)),
    )
    services = [dict(r) for r in db.fetchall()]

    svc_ids = [s["svc_id"] for s in services]
    costs_by_svc: Dict[int, List[Dict]] = {sid: [] for sid in svc_ids}
    if svc_ids:
        svc_ph = ",".join(["%s"] * len(svc_ids))
        db.execute(
            f"""
            SELECT cost_id, svc_id, job_id, cost_name, quantity, unit,
                   buying_amount, selling_amount, is_reimbursement, vat_rate,
                   buying_rate, selling_rate
            FROM job_costs
            WHERE svc_id IN ({svc_ph})
            ORDER BY svc_id, cost_id
            """,
            tuple(svc_ids),
        )
        for row in db.fetchall():
            d = dict(row)
            costs_by_svc.setdefault(d["svc_id"], []).append(d)

    return jobs, services, costs_by_svc


# ---------- Endpoint ----------

@router.get("/exports/generic")
def export_generic_template(
    customer_id: int = Query(..., description="Target customer ID"),
    family: str = Query(..., description="Family key: trucking | handling"),
    service_types: str = Query(..., description="Comma-separated service_type_codes"),
    month: Optional[str] = Query(None, description="Month filter YYYY-MM"),
    from_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    to_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    service_type: Optional[str] = Query(None, description="Optional narrow filter"),
    sheet_name: Optional[str] = Query(None),
    title_template: Optional[str] = Query(None),
    vat_rate: Optional[float] = Query(0.08),
    db: DatabaseSession = Depends(get_db),
):
    """
    Generic export — picks renderer by `family`, applies per-call config overrides.
    Called via the customer registry redirect, not directly by frontend in
    most cases (frontend uses /api/exports/customer/{code}).
    """
    renderer = FAMILY_RENDERERS.get(family)
    if not renderer:
        raise HTTPException(400, f"Unknown family '{family}'. Valid: {list(FAMILY_RENDERERS.keys())}")

    # Customer info
    db.execute(
        """
        SELECT customer_id, customer_code, short_name, company_name, address,
               contact_name, tax_code
        FROM customers WHERE customer_id = %s
        """,
        (customer_id,),
    )
    cust_row = db.fetchone()
    if not cust_row:
        raise HTTPException(404, "Customer not found")
    customer = dict(cust_row)

    # Fetch data
    types_list = [s.strip() for s in service_types.split(",") if s.strip()]
    jobs, services, costs_by_svc = _fetch_jobs_services_costs(
        db, customer_id=customer_id, service_types=types_list,
        month=month, from_date=from_date, to_date=to_date,
        service_type_filter=service_type,
    )
    if not jobs:
        raise HTTPException(404, "No jobs found for this customer in the specified period")

    jobs_map = {j["job_id"]: j for j in jobs}

    # Per-call config (overrides registry defaults)
    config = {
        "vat_rate": vat_rate,
    }
    if sheet_name:
        config["sheet_name"] = sheet_name
    if title_template:
        config["title_template"] = title_template

    # Render
    wb = renderer(
        customer=customer,
        services=services,
        jobs_map=jobs_map,
        costs_by_svc=costs_by_svc,
        month=month,
        logo_path=str(DEFAULT_LOGO_PATH) if DEFAULT_LOGO_PATH.exists() else None,
        config=config,
    )

    # Save + stream
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    wb.save(tmp.name)
    tmp.close()

    period_tag = month or f"{from_date or ''}_{to_date or ''}".strip("_") or "all"
    filename = f"{customer.get('customer_code', 'customer')}_{family}_{period_tag}.xlsx"
    return FileResponse(
        path=tmp.name,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
