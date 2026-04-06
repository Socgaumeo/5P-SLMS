"""
Debit Note Job Data Resolver — query DB, build data dict for template filling.

Resolves job + job_services + customer data into a flat dict that template
fillers can use to populate Excel cells.
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.db.supabase_client import get_supabase

logger = logging.getLogger(__name__)


def resolve_job_data(job_ids: List[int], customer_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Query DB and build data dict for template filling.
    Returns combined data from jobs, job_services, and customer info.
    """
    client = get_supabase()

    # Get jobs with customer info
    jobs_result = client.table('jobs').select(
        '*, customers(customer_id, customer_code, company_name, short_name, tax_code, address)'
    ).in_('job_id', job_ids).execute()
    jobs = jobs_result.data or []

    if not jobs:
        return {}

    # Get services for these jobs ordered by date
    services_result = client.table('job_services').select(
        '*, vendors(vendor_code, short_name, company_name)'
    ).in_('job_id', job_ids).order('scheduled_date').execute()
    services = services_result.data or []

    customer = jobs[0].get('customers', {}) or {}
    total_revenue = sum(float(j.get('total_revenue') or 0) for j in jobs)
    total_cost = sum(float(j.get('total_cost') or 0) for j in jobs)

    # Group services by job_id
    svc_by_job: Dict[int, list] = {}
    for svc in services:
        jid = svc['job_id']
        if jid not in svc_by_job:
            svc_by_job[jid] = []
        svc_by_job[jid].append(svc)

    jobs_detail = _build_jobs_detail(jobs, svc_by_job)

    now = datetime.now()
    return {
        # Customer info
        'customer_name': customer.get('short_name') or customer.get('company_name', ''),
        'customer_code': customer.get('customer_code', ''),
        'company_name': customer.get('company_name', ''),
        'tax_code': customer.get('tax_code', ''),
        'customer_address': customer.get('address', ''),

        # Job info
        'job_no': jobs[0].get('job_no', '') if len(jobs) == 1 else f"{len(jobs)} jobs",
        'job_count': len(jobs),
        'booking_date': jobs[0].get('booking_date', ''),

        # Financial aggregates
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'profit': total_revenue - total_cost,
        'vat_rate': 0.08,
        'vat_amount': total_revenue * 0.08,
        'grand_total': total_revenue * 1.08,

        # Dates
        'month_year': now.strftime('%m/%Y'),
        'current_date': now.strftime('%d/%m/%Y'),
        'month': now.strftime('%m'),
        'year': now.strftime('%Y'),

        # Line items (same list used under both keys for compatibility)
        'services': jobs_detail,
        'jobs': [{'job_no': j.get('job_no', ''), 'job_id': j.get('job_id')} for j in jobs],
        'jobs_detail': jobs_detail,
    }


def _build_jobs_detail(jobs: list, svc_by_job: dict) -> list:
    """Build per-job detail row dicts for column-based template filling."""
    detail = []
    for idx, job in enumerate(jobs, 1):
        jid = job['job_id']
        job_svcs = svc_by_job.get(jid, [])
        first_svc = job_svcs[0] if job_svcs else {}
        revenue = float(job.get('total_revenue') or 0)

        origin = first_svc.get('origin_address', '')
        dest = first_svc.get('dest_address', '')

        detail.append({
            'stt': idx,
            'job_no': job.get('job_no', ''),
            'service_date': first_svc.get('scheduled_date') or job.get('booking_date', ''),
            'declaration_date': first_svc.get('scheduled_date') or job.get('booking_date', ''),

            # Locations
            'origin': origin,
            'destination': dest,
            'route': f"{origin} → {dest}" if origin or dest else '',
            'pickup_location': origin,
            'pickup_province': origin.split(',')[-1].strip() if origin else '',
            'delivery_location': dest,
            'delivery_province': dest.split(',')[-1].strip() if dest else '',

            # Vehicle / transport
            'license_plate': first_svc.get('license_plate', ''),
            'vehicle_type': job.get('vehicle_type', ''),
            'transport_type': first_svc.get('service_type_code', ''),

            # Fees — revenue as main amount; per-fee fields default 0 until DB supports them
            'transport_fee': revenue,
            'customs_fee': revenue,
            'amount': revenue,
            'total': revenue,
            'unit_price': revenue,
            'quantity': 1,
            'surcharge': 0,
            'fuel_surcharge': 0,
            'inspection_fee': 0,
            'handling_fee': 0,
            'expense_amount': 0,

            # Document refs (populated from job_services data when available)
            'declaration_number': '',
            'commercial_invoice': '',
            'bill_of_lading': '',
            'container_no': '',
            'clearance_channel': '',
            'co_number': '',
            'co_form': '',
            'co_date': '',
            'invoice_number': '',
            'invoice_ref': '',
            'receipt_number': '',
            'expense_description': '',
            'note': '',
            'notes': '',
            'weight_kg': '',
        })

    return detail


def _format_value(value: Any, fmt: str, date_format: str = 'DD/MM/YYYY') -> Any:
    """Format value according to field mapping format specification."""
    if value is None:
        return ''

    if fmt == 'currency':
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0

    if fmt == 'date':
        if isinstance(value, str) and value:
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                py_fmt = date_format.replace('DD', '%d').replace('MM', '%m').replace('YYYY', '%Y')
                return dt.strftime(py_fmt)
            except Exception:
                return value
        return value

    if fmt == 'percentage':
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0

    return str(value) if value else ''


def _evaluate_formula(formula: str, data: dict) -> Any:
    """Evaluate simple arithmetic formulas with data field references."""
    try:
        expr = formula
        for key, val in data.items():
            if isinstance(val, (int, float)):
                expr = expr.replace(key, str(val))
        if re.match(r'^[\d\.\+\-\*\/\(\)\s]+$', expr):
            return eval(expr)  # nosec — restricted to numeric expressions only
        return 0
    except Exception:
        return 0
