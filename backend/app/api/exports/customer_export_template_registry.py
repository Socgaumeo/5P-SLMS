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
# --------------------------------------------------------------------------
# Generic family templates (Phase 1+2 of customer-bang-ke roadmap).
# Add a customer here to enable "Mẫu {Code}" export buttons in the UI.
#
# Keys per template:
#   key, label, icon, description       — shown to user
#   family                              — 'trucking' | 'handling' (dispatched
#                                         to generic_customer_export_endpoint)
#   service_types                       — DB filter list
#   config (optional)                   — per-customer overrides for the
#                                         family renderer (sheet_name,
#                                         title_template, vat_rate, etc.)
# --------------------------------------------------------------------------

_TRUCKING_SERVICE_TYPES = ["TRUCKING_DOM", "TRUCKING_SHORT", "TRUCKING_LONG"]
# Handling family is service-type agnostic — it lists every cost line as one
# row regardless of underlying service. Default = all common service types.
_HANDLING_DEFAULT_TYPES = [
    "TRUCKING_DOM", "TRUCKING_SHORT", "TRUCKING_LONG",
    "CUS_CO", "CUS_IMPORT", "CUS_EXPORT",
    "SEA_IMP", "SEA_EXP", "SEA_DOM",
    "AIR_IMP", "AIR_EXP", "AIR_DOM",
    "BORDER_IMP", "BORDER_EXP",
    "SVC_OTHER", "SVC_PACK", "SVC_FUMI", "SVC_VACUUM",
    "WHS_STORAGE", "WHS_HANDLE", "WHS_VAS",
]
# Customs family — only services whose fee statement is a customs-declaration
# bảng kê (no transport / no warehouse). CUS_CO handled by other templates.
_CUSTOMS_SERVICE_TYPES = ["CUS_IMPORT", "CUS_EXPORT", "CUS"]


def _trucking_template(label_suffix: str = "") -> Dict[str, Any]:
    suffix = f" — {label_suffix}" if label_suffix else ""
    return {
        "key": "trucking",
        "label": f"Bảng kê Vận chuyển đường bộ{suffix}",
        "icon": "🚚",
        "description": "Bảng kê dịch vụ vận chuyển đường bộ nội địa",
        "family": "trucking",
        "service_types": _TRUCKING_SERVICE_TYPES,
        "implemented": True,
    }


def _handling_template(label_suffix: str = "", service_types: Optional[List[str]] = None) -> Dict[str, Any]:
    suffix = f" — {label_suffix}" if label_suffix else ""
    return {
        "key": "handling",
        "label": f"Bảng kê Dịch vụ làm hàng{suffix}",
        "icon": "📋",
        "description": "Bảng kê chi tiết phí dịch vụ làm hàng (1 dòng/cost)",
        "family": "handling",
        "service_types": service_types or _HANDLING_DEFAULT_TYPES,
        "implemented": True,
    }


def _customs_template(label_suffix: str = "") -> Dict[str, Any]:
    """
    Customs-declaration bảng kê (Family C).
    Output = 1..3 sheets split by cd_no prefix (108→NHAP KHAU, 308→XNK TAI CHO).
    Covers GLOREX, THÁI HOÀ, GANG THÉP TN (customs variant), and similar customers.
    """
    suffix = f" — {label_suffix}" if label_suffix else ""
    return {
        "key": "customs",
        "label": f"Bảng kê Thủ tục hải quan{suffix}",
        "icon": "📜",
        "description": "Bảng kê lệ phí hải quan — tách sheet NHAP KHAU / XNK TAI CHO theo cd_no prefix",
        "family": "customs",
        "service_types": _CUSTOMS_SERVICE_TYPES,
        "implemented": True,
    }


CUSTOMER_TEMPLATES: Dict[str, Dict[str, Any]] = {
    # ---- Special customers with custom dedicated modules ----
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
        "templates": [],  # populated lazily below
    },

    # ---- FAMILY A: Trucking (7 customers) ----
    "BINHMINH": {
        "name": "Bình Minh - ATC", "module": "generic_customer_export",
        "supports_date_filter": True,
        "templates": [_trucking_template()],
    },
    "KK": {
        "name": "K+K Fashion", "module": "generic_customer_export",
        "supports_date_filter": True,
        "templates": [_trucking_template()],
    },
    "KKFASHION": {
        "name": "K+K Fashion", "module": "generic_customer_export",
        "supports_date_filter": True,
        "templates": [_trucking_template()],
    },
    "DONGSUNG": {
        "name": "Dongsung", "module": "generic_customer_export",
        "supports_date_filter": True,
        "templates": [_trucking_template()],
    },
    "UPGAIN": {
        "name": "Upgain Vietnam", "module": "generic_customer_export",
        "supports_date_filter": True,
        "templates": [_trucking_template()],
    },
    "UTRACON": {
        "name": "Utracon Vietnam", "module": "generic_customer_export",
        "supports_date_filter": True,
        "templates": [_trucking_template()],
    },
    "TVC": {
        "name": "Thái Việt Trung Logistics", "module": "generic_customer_export",
        "supports_date_filter": True,
        "templates": [_trucking_template()],
    },

    # ---- FAMILY B: Handling (7 customers) ----
    "HUNGPHAT": {
        "name": "Hưng Phát", "module": "generic_customer_export",
        "supports_date_filter": True,
        "templates": [_handling_template()],
    },
    "VINTECH": {
        "name": "Vintech Automation", "module": "generic_customer_export",
        "supports_date_filter": True,
        "templates": [_handling_template()],
    },
    "KTXL": {
        "name": "Xây Lắp VN", "module": "generic_customer_export",
        "supports_date_filter": True,
        "templates": [_handling_template()],
    },
    "LOGIMARKHN": {
        "name": "Logimark HN", "module": "generic_customer_export",
        "supports_date_filter": True,
        "templates": [_handling_template()],
    },
    "MESSERHP": {
        "name": "Messer Hải Phòng", "module": "generic_customer_export",
        "supports_date_filter": True,
        "templates": [_handling_template()],
    },
    "GANGTHEPTN": {
        "name": "Gang Thép TN", "module": "generic_customer_export",
        "supports_date_filter": True,
        # Gang Thép has BOTH customs-declaration bảng kê (Family C) and a
        # general handling bảng kê — user picks which to export.
        "templates": [_customs_template(), _handling_template()],
    },
    "LAS": {
        "name": "LAS", "module": "generic_customer_export",
        "supports_date_filter": True,
        "templates": [_handling_template()],
    },

    # ---- FAMILY C: Customs declaration (multi-sheet) ----
    "GLOREX": {
        "name": "Glorex Vietnam", "module": "generic_customer_export",
        "supports_date_filter": True,
        "templates": [_customs_template()],
    },
    "THAIHOA": {
        "name": "Thái Hoà", "module": "generic_customer_export",
        "supports_date_filter": True,
        "templates": [_customs_template()],
    },
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
            template = template or "nhap_sea_air"
            redirect_url = (
                f"/api/jobs/exports/dainese?customer_id={customer_id}&template={template}"
            )

        elif module_name == "generic_customer_export":
            # Family-A/B customers — pick template by `template` key
            templates_list = template_info.get("templates", [])
            if not templates_list:
                raise HTTPException(400, f"Customer {customer_code} has no templates configured")
            # Default to first template if none specified
            tpl = next((t for t in templates_list if t["key"] == template), templates_list[0])
            family = tpl.get("family")
            svc_types = ",".join(tpl.get("service_types", []))
            redirect_url = (
                f"/api/jobs/exports/generic"
                f"?customer_id={customer_id}&family={family}"
                f"&service_types={svc_types}"
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
