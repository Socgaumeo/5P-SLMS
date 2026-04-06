"""
Debit Note Generator Service — load Excel templates, fill data, generate debit notes.

Core engine:
1. Load template from server disk (or download from Telegram file_id)
2. Query job data from DB (jobs + job_services + customer info)
3. Fill cells per field_mapping JSON from debit_templates table
4. Return filled workbook as temp file path

Supports: text, currency, date, percentage formats + table ranges for line items.
"""

import io
import os
import re
import tempfile
import logging
import zipfile
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from app.db.supabase_client import get_supabase

import importlib
telegram_downloader = importlib.import_module("app.services.telegram-file-downloader")

logger = logging.getLogger(__name__)

# Template cache directory
TEMPLATE_CACHE_DIR = os.path.join(tempfile.gettempdir(), '5p_debit_templates')
os.makedirs(TEMPLATE_CACHE_DIR, exist_ok=True)


async def load_template_workbook(template: dict):
    """
    Load template Excel workbook.
    Tries local_file_path first, then downloads from Telegram file_id.
    Returns openpyxl Workbook or None.
    """
    # Try local file path
    if template.get('local_file_path') and os.path.exists(template['local_file_path']):
        return load_workbook(template['local_file_path'])

    # Try Telegram file_id
    if template.get('telegram_file_id'):
        cache_path = os.path.join(TEMPLATE_CACHE_DIR, f"{template['id']}.xlsx")

        # Check cache
        if os.path.exists(cache_path):
            return load_workbook(cache_path)

        # Download from Telegram
        file_data = await telegram_downloader.download_telegram_file(template['telegram_file_id'])
        if file_data:
            file_bytes, _ = file_data
            with open(cache_path, 'wb') as f:
                f.write(file_bytes)
            return load_workbook(cache_path)

    logger.error(f"Cannot load template {template['id']}: no file source")
    return None


def resolve_job_data(job_ids: List[int], customer_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Query DB and build data dict for template filling.
    Returns combined data from jobs, job_services, and customer info.
    """
    client = get_supabase()

    # Get jobs
    jobs_result = client.table('jobs').select(
        '*, customers(customer_id, customer_code, company_name, short_name, tax_code, address)'
    ).in_('job_id', job_ids).execute()
    jobs = jobs_result.data or []

    if not jobs:
        return {}

    # Get services for these jobs
    services_result = client.table('job_services').select(
        '*, vendors(vendor_code, short_name, company_name)'
    ).in_('job_id', job_ids).order('scheduled_date').execute()
    services = services_result.data or []

    # Customer info from first job
    customer = jobs[0].get('customers', {}) or {}

    # Calculate totals
    total_revenue = sum(float(j.get('total_revenue') or 0) for j in jobs)
    total_cost = sum(float(j.get('total_cost') or 0) for j in jobs)

    # Build service line items
    service_items = []
    for idx, svc in enumerate(services, 1):
        vendor = svc.get('vendors', {}) or {}
        service_items.append({
            'stt': idx,
            'service_type': svc.get('service_type_code', ''),
            'service_description': svc.get('special_requirements', '') or svc.get('service_type_code', ''),
            'scheduled_date': svc.get('scheduled_date', ''),
            'origin': svc.get('origin_address', ''),
            'destination': svc.get('dest_address', ''),
            'vendor_name': vendor.get('short_name') or vendor.get('company_name', ''),
            'license_plate': svc.get('license_plate', ''),
            'driver_name': svc.get('driver_name', ''),
            'quantity': 1,
            'unit_price': 0,
            'amount': 0,
        })

    # Build data dictionary
    now = datetime.now()
    data = {
        # Customer info
        'customer_name': customer.get('short_name') or customer.get('company_name', ''),
        'customer_code': customer.get('customer_code', ''),
        'company_name': customer.get('company_name', ''),
        'tax_code': customer.get('tax_code', ''),
        'customer_address': customer.get('address', ''),

        # Job info (first job or aggregated)
        'job_no': jobs[0].get('job_no', '') if len(jobs) == 1 else f"{len(jobs)} jobs",
        'job_count': len(jobs),
        'booking_date': jobs[0].get('booking_date', ''),

        # Financial
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'profit': total_revenue - total_cost,
        'vat_rate': 0.08,
        'vat_amount': total_revenue * 0.08,
        'grand_total': total_revenue * 1.08,

        # Date
        'month_year': now.strftime('%m/%Y'),
        'current_date': now.strftime('%d/%m/%Y'),
        'month': now.strftime('%m'),
        'year': now.strftime('%Y'),

        # Service line items
        'services': service_items,

        # All jobs list
        'jobs': [{'job_no': j.get('job_no', ''), 'job_id': j.get('job_id')} for j in jobs],
    }

    return data


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
                # Convert format string
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

    # Default: text
    return str(value) if value else ''


def _evaluate_formula(formula: str, data: dict) -> Any:
    """
    Evaluate simple formulas like 'total_revenue * 0.08'.
    Only supports basic arithmetic with data field references.
    """
    try:
        # Replace field names with values
        expr = formula
        for key, val in data.items():
            if isinstance(val, (int, float)):
                expr = expr.replace(key, str(val))
        # Safe eval of simple arithmetic
        if re.match(r'^[\d\.\+\-\*\/\(\)\s]+$', expr):
            return eval(expr)
        return 0
    except Exception:
        return 0


def fill_template(wb, field_mapping: dict, data: dict) -> None:
    """
    Fill workbook cells according to field_mapping.
    Handles single cells and table ranges.
    """
    ws = wb.active  # Use first sheet by default

    for cell_ref, mapping in field_mapping.items():
        # Table range (e.g., "A8:E50")
        if ':' in cell_ref and mapping.get('format') == 'table':
            _fill_table_range(ws, cell_ref, mapping, data)
            continue

        # Single cell
        field = mapping.get('field', '')
        fmt = mapping.get('format', 'text')

        # Resolve value
        if mapping.get('formula'):
            value = _evaluate_formula(mapping['formula'], data)
        else:
            value = data.get(field, '')

        # Format and write
        formatted = _format_value(value, fmt, mapping.get('date_format', 'DD/MM/YYYY'))

        try:
            ws[cell_ref] = formatted
            # Apply number format for currency
            if fmt == 'currency':
                ws[cell_ref].number_format = '#,##0'
            elif fmt == 'percentage':
                ws[cell_ref].number_format = '0.00%'
        except Exception as e:
            logger.warning(f"Error writing cell {cell_ref}: {e}")


def _fill_table_range(ws, range_ref: str, mapping: dict, data: dict) -> None:
    """Fill a table range with service line items."""
    start_ref, end_ref = range_ref.split(':')

    # Parse start row and columns
    start_col = re.match(r'([A-Z]+)', start_ref).group(1)
    start_row = int(re.search(r'(\d+)', start_ref).group(1))

    columns = mapping.get('columns', {})
    items = data.get(mapping.get('field', 'services'), [])

    for idx, item in enumerate(items):
        row = start_row + idx
        for col_letter, field_name in columns.items():
            cell = f"{col_letter}{row}"
            value = item.get(field_name, '')
            try:
                ws[cell] = value
            except Exception:
                pass


async def generate_single(template_id: str, job_ids: List[int]) -> Optional[str]:
    """
    Generate a single debit note.
    Returns path to temporary Excel file, or None on error.
    """
    client = get_supabase()

    # Get template
    result = client.table('debit_templates').select('*').eq('id', template_id).limit(1).execute()
    if not result.data:
        logger.error(f"Template {template_id} not found")
        return None

    template = result.data[0]
    field_mapping = template.get('field_mapping', {})

    # Load workbook
    wb = await load_template_workbook(template)
    if not wb:
        return None

    # Resolve data
    data = resolve_job_data(job_ids, template.get('customer_id'))
    if not data:
        logger.error(f"No job data found for job_ids: {job_ids}")
        return None

    # Fill template
    fill_template(wb, field_mapping, data)

    # Save to temp file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    wb.save(tmp.name)
    tmp.close()

    return tmp.name


async def generate_batch(template_id: str, customer_id: int, month: str) -> Optional[str]:
    """
    Generate debit notes for all jobs of a customer in a month.
    Returns path to temporary ZIP file containing individual Excel files.
    """
    import calendar

    client = get_supabase()

    # Get template
    tmpl_result = client.table('debit_templates').select('*').eq('id', template_id).limit(1).execute()
    if not tmpl_result.data:
        return None
    template = tmpl_result.data[0]

    # Get jobs for this customer + month
    year, mon = month.split('-')
    last_day = calendar.monthrange(int(year), int(mon))[1]
    start_date = f"{year}-{mon}-01"
    end_date = f"{year}-{mon}-{last_day}"

    jobs_result = client.table('jobs').select('job_id, job_no').eq(
        'customer_id', customer_id
    ).gte('created_at', start_date).lte('created_at', end_date).execute()

    jobs = jobs_result.data or []
    if not jobs:
        logger.info(f"No jobs found for customer {customer_id} in {month}")
        return None

    # Generate for all jobs together (single debit note with all jobs)
    job_ids = [j['job_id'] for j in jobs]
    excel_path = await generate_single(template_id, job_ids)

    if not excel_path:
        return None

    # Wrap in ZIP
    zip_path = tempfile.NamedTemporaryFile(delete=False, suffix='.zip').name
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        customer_result = client.table('customers').select('customer_code, short_name').eq(
            'customer_id', customer_id
        ).limit(1).execute()
        cust_code = customer_result.data[0]['customer_code'] if customer_result.data else 'unknown'
        filename = f"DEBIT_{cust_code}_{month}.xlsx"
        zf.write(excel_path, filename)

    # Cleanup temp excel
    os.unlink(excel_path)

    return zip_path
