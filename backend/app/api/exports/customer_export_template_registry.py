# backend/app/api/exports/customer_template_registry.py
"""
Customer Export Template Registry
=================================
Maps customer codes to their custom export templates.
Add new customer templates here when needed.

Usage:
1. Create template file: {customer_code}_export_template.py
2. Register in CUSTOMER_TEMPLATES below
3. Template will auto-enable for that customer
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Registry of customer-specific export templates
# Key: customer_code (uppercase), Value: template info
CUSTOMER_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "MEIKO": {
        "name": "MEIKO Electronics Vietnam",
        "description": "Bảng kê 3 sheets: Bảng kê IM, Truck, Debit",
        "module": "meiko_customer_export_template",
        "sheets": ["Bảng kê IM", "Truck", "Debit"],
        "supports_date_filter": True,
    },
    "DAINESE": {
        "name": "DAINESE Vietnam",
        "description": "Bảng kê theo loại dịch vụ: Nhập SEA/AIR, CO, TC+CPN, TT, Xuất",
        "module": "dainese_customer_export_template",
        "supports_date_filter": True,
        # When `templates` is present, the frontend renders ONE button per
        # entry so the user picks which Bảng kê variant to export.
        "templates": [],  # populated lazily below to avoid import cycles
    },
    # Add more customer templates here:
    # "SAMSUNG": {
    #     "name": "Samsung Electronics",
    #     "description": "Custom Samsung export format",
    #     "module": "samsung_export_template",
    #     "sheets": ["Summary", "Details"],
    #     "supports_date_filter": True,
    # },
}


def _populate_dainese_templates() -> None:
    """Load DAINESE template list lazily (sub-templates live in the module)."""
    try:
        from app.api.exports.dainese_customer_export_template import list_dainese_templates
        CUSTOMER_TEMPLATES["DAINESE"]["templates"] = list_dainese_templates()
    except Exception as e:  # pragma: no cover - import guard
        logger.warning(f"Could not load DAINESE templates: {e}")


_populate_dainese_templates()


def get_customer_template(customer_code: str) -> Optional[Dict[str, Any]]:
    """Get template info for a customer, returns None if no custom template."""
    return CUSTOMER_TEMPLATES.get(customer_code.upper())


def has_custom_template(customer_code: str) -> bool:
    """Check if customer has a custom export template."""
    return customer_code.upper() in CUSTOMER_TEMPLATES


def list_available_templates() -> List[Dict[str, Any]]:
    """List all available customer templates."""
    return [
        {"customer_code": code, **info}
        for code, info in CUSTOMER_TEMPLATES.items()
    ]


# ============================================================
# API Endpoints
# ============================================================

@router.get("/templates")
async def get_export_templates():
    """List all available customer export templates."""
    return {
        "templates": list_available_templates(),
        "count": len(CUSTOMER_TEMPLATES)
    }


@router.get("/templates/{customer_code}")
async def get_customer_template_info(customer_code: str):
    """Get export template info for a specific customer."""
    template = get_customer_template(customer_code)
    if template:
        return {
            "has_template": True,
            "customer_code": customer_code.upper(),
            **template
        }
    return {
        "has_template": False,
        "customer_code": customer_code.upper(),
        "message": "No custom template, will use default export"
    }


@router.get("/customer/{customer_code}")
async def export_customer_jobs(
    customer_code: str,
    month: Optional[str] = Query(None, description="Month filter YYYY-MM"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    template: Optional[str] = Query(
        None,
        description="Sub-template key (required for customers with multiple templates, e.g. DAINESE)",
    ),
    service_type: Optional[str] = Query(
        None,
        description="Optional service_type_code filter (e.g. SEA_IMP, TRUCKING_DOM)",
    ),
):
    """
    Export jobs for a customer using their custom template if available.
    Falls back to generic export if no custom template.
    """
    from fastapi.responses import RedirectResponse

    template_info = get_customer_template(customer_code)

    if template_info:
        # Route to customer-specific export by redirecting to existing endpoint
        module_name = template_info["module"]

        # Get customer_id from customer_code
        from app.db.supabase_client import get_supabase
        client = get_supabase()
        result = client.table('customers').select('customer_id').eq(
            'customer_code', customer_code.upper()
        ).limit(1).execute()

        if not result.data:
            raise HTTPException(404, f"Customer {customer_code} not found")

        customer_id = result.data[0]['customer_id']

        if module_name == "meiko_customer_export_template":
            redirect_url = f"/api/jobs/exports/meiko?customer_id={customer_id}"

        elif module_name == "dainese_customer_export_template":
            # DAINESE requires `template` to choose which Bảng kê to generate
            from fastapi import Query as _Q
            template = template or "nhap_sea_air"
            redirect_url = (
                f"/api/jobs/exports/dainese?customer_id={customer_id}&template={template}"
            )

        else:
            raise HTTPException(
                501, f"Module '{module_name}' not wired in registry"
            )

        if month:
            redirect_url += f"&month={month}"
        if start_date:
            redirect_url += f"&from_date={start_date}"
        if end_date:
            redirect_url += f"&to_date={end_date}"
        if service_type:
            redirect_url += f"&service_type={service_type}"

        return RedirectResponse(url=redirect_url, status_code=307)

    # No custom template - use generic export
    raise HTTPException(
        400,
        f"Customer {customer_code} has no custom template. Use default export."
    )
