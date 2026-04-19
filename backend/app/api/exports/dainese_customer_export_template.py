"""
DAINESE Customer Export Template
================================
Generates Excel statements (Bảng kê) for DAINESE Vietnam in 5 different formats:

1. nhap_sea_air  - Bảng kê nhập SEA/AIR (international import - sea + air)
2. phi_co        - Bảng kê phí CO (certificate of origin fees)
3. tc_cpn        - Bảng kê TC + nhập CPN (customs + express courier)
4. tt            - Bảng kê TT (payment statement / domestic trucking)
5. xuat          - Bảng kê xuất (exports)

The user picks which template to generate via the `template` query param.
Each template reproduces the exact layout, fonts, colors, and Excel formulas
of the customer's reference files (see plans/reports/dainese-templates/).

NOTE: Only `nhap_sea_air` is fully implemented (file 1). Other templates
return HTTP 501 (Not Implemented) until their reference files are analyzed.
"""

import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.db.session import get_db, DatabaseSession
from app.api.exports.dainese_template_renderer_nhap_sea_air import (
    render_nhap_sea_air_workbook,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ---- Catalog of templates DAINESE supports (used by the registry to render UI buttons) ----

DAINESE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "nhap_sea_air": {
        "label": "Bảng kê nhập SEA/AIR",
        "icon": "🚢",
        "description": "Nhập khẩu quốc tế đường biển + hàng không",
        "service_types": ["SEA_IMP", "AIR_IMP"],
        "implemented": True,
    },
    "phi_co": {
        "label": "Bảng kê phí CO",
        "icon": "📜",
        "description": "Phí Certificate of Origin",
        "service_types": ["CUS_CO"],
        "implemented": False,
    },
    "tc_cpn": {
        "label": "Bảng kê TC + CPN",
        "icon": "📦",
        "description": "Thủ tục hải quan + Chuyển phát nhanh",
        "service_types": ["CUS_IMPORT"],
        "implemented": False,
    },
    "tt": {
        "label": "Bảng kê TT",
        "icon": "🚚",
        "description": "Thanh toán / Trucking nội địa",
        "service_types": ["TRUCKING_DOM", "TRUCKING_SHORT", "TRUCKING_LONG"],
        "implemented": False,
    },
    "xuat": {
        "label": "Bảng kê xuất",
        "icon": "📤",
        "description": "Xuất khẩu",
        "service_types": ["SEA_EXP", "AIR_EXP", "BORDER_EXP", "CUS_EXPORT"],
        "implemented": False,
    },
}


def list_dainese_templates() -> List[Dict[str, Any]]:
    """List of available DAINESE templates - consumed by the registry/frontend."""
    return [
        {"key": k, **{kk: v[kk] for kk in ("label", "icon", "description", "implemented")}}
        for k, v in DAINESE_TEMPLATES.items()
    ]


# ---- Logo path (5P star logo extracted from reference files) ----

LOGO_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "plans" / "reports" / "dainese-templates" / "logos"
    / "Bảng_kê_nhập_tháng_3_2026_sea_air__image1.png"
)


# ---- Data fetch ----

def _fetch_jobs_and_services(
    db: DatabaseSession,
    customer_id: int,
    service_types: List[str],
    month: Optional[str],
    from_date: Optional[str],
    to_date: Optional[str],
) -> tuple[List[Dict], List[Dict]]:
    """Pull jobs + their services for the requested period and service types."""
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
        return [], []

    job_ids = [j["job_id"] for j in jobs]
    type_placeholders = ",".join(["%s"] * len(service_types))
    job_placeholders = ",".join(["%s"] * len(job_ids))

    db.execute(
        f"""
        SELECT js.*, v.vendor_code, v.short_name AS vendor_name
        FROM job_services js
        LEFT JOIN vendors v ON js.vendor_id = v.vendor_id
        WHERE js.job_id IN ({job_placeholders})
          AND js.service_type_code IN ({type_placeholders})
        ORDER BY js.scheduled_date
        """,
        tuple(job_ids + service_types),
    )
    services = [dict(r) for r in db.fetchall()]
    return jobs, services


# ---- API endpoint ----

@router.get("/exports/dainese")
def export_dainese_template(
    customer_id: int = Query(..., description="DAINESE customer ID"),
    template: str = Query(..., description="Template key (e.g. nhap_sea_air, phi_co, tc_cpn, tt, xuat)"),
    month: Optional[str] = Query(None, description="Month filter YYYY-MM"),
    from_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    to_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    db: DatabaseSession = Depends(get_db),
):
    """
    Generate a DAINESE Excel statement for the requested template type.
    The frontend selects `template` based on the customer's button click.
    """
    template_def = DAINESE_TEMPLATES.get(template)
    if not template_def:
        raise HTTPException(400, f"Unknown DAINESE template: {template}")
    if not template_def["implemented"]:
        raise HTTPException(501, f"Template '{template}' not implemented yet")

    # Customer info
    db.execute(
        """
        SELECT customer_id, customer_code, short_name, company_name, address, contact_name
        FROM customers WHERE customer_id = %s
        """,
        (customer_id,),
    )
    customer_row = db.fetchone()
    if not customer_row:
        raise HTTPException(404, "Customer not found")
    customer = dict(customer_row)

    # Fetch data
    jobs, services = _fetch_jobs_and_services(
        db,
        customer_id=customer_id,
        service_types=template_def["service_types"],
        month=month,
        from_date=from_date,
        to_date=to_date,
    )
    if not jobs:
        raise HTTPException(404, "No jobs found for this customer in the specified period")

    jobs_map = {j["job_id"]: j for j in jobs}

    # Render the requested template
    if template == "nhap_sea_air":
        wb = render_nhap_sea_air_workbook(
            customer=customer,
            services=services,
            jobs_map=jobs_map,
            month=month,
            logo_path=str(LOGO_PATH) if LOGO_PATH.exists() else None,
        )
    else:
        # Defensive — should be unreachable due to implemented check above
        raise HTTPException(501, f"Renderer for '{template}' not wired")

    # Save and stream
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    wb.save(tmp.name)
    tmp.close()

    period_tag = month or f"{from_date or ''}_{to_date or ''}".strip("_") or "all"
    filename = f"DAINESE_{template}_{period_tag}.xlsx"
    return FileResponse(
        path=tmp.name,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
