"""
Debit Note Generator Service — orchestrates template loading and debit note generation.

1. Load Excel template from disk or Telegram file_id
2. Resolve job data from DB via debit-note-job-data-resolver
3. Fill template cells via debit-note-excel-template-filler
4. Return path to filled .xlsx or .zip file
"""

import os
import tempfile
import logging
import zipfile
import importlib

from openpyxl import load_workbook
from typing import List, Optional

from app.db.supabase_client import get_supabase

telegram_downloader = importlib.import_module("app.services.telegram-file-downloader")
_resolver = importlib.import_module("app.services.debit-note-job-data-resolver")
_filler = importlib.import_module("app.services.debit-note-excel-template-filler")

resolve_job_data = _resolver.resolve_job_data
fill_template = _filler.fill_template

logger = logging.getLogger(__name__)

TEMPLATE_CACHE_DIR = os.path.join(tempfile.gettempdir(), '5p_debit_templates')
os.makedirs(TEMPLATE_CACHE_DIR, exist_ok=True)


async def load_template_workbook(template: dict):
    """
    Load template Excel workbook.
    Tries local_file_path first, then downloads from Telegram file_id.
    Returns openpyxl Workbook or None.
    """
    if template.get('local_file_path') and os.path.exists(template['local_file_path']):
        return load_workbook(template['local_file_path'])

    if template.get('telegram_file_id'):
        cache_path = os.path.join(TEMPLATE_CACHE_DIR, f"{template['id']}.xlsx")
        if os.path.exists(cache_path):
            return load_workbook(cache_path)

        file_data = await telegram_downloader.download_telegram_file(template['telegram_file_id'])
        if file_data:
            file_bytes, _ = file_data
            with open(cache_path, 'wb') as f:
                f.write(file_bytes)
            return load_workbook(cache_path)

    logger.error(f"Cannot load template {template['id']}: no file source")
    return None


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
    start = f"{year}-{mon}-01T00:00:00"
    end = f"{year}-{mon}-{last_day}T23:59:59"

    jobs_result = client.table('jobs').select('job_id, job_no').eq(
        'customer_id', customer_id
    ).gte('created_at', start).lte('created_at', end).execute()

    jobs = jobs_result.data or []

    # Filter by service type if template has service_type mapping
    field_mapping = template.get('field_mapping', {})
    svc_type = field_mapping.get('service_type', '')
    svc_type_map = {
        "CO": ["CUS_SUBMITTED", "CUS_PROCESSING", "CUS_APPROVED"],
        "SEA_AIR_IMPORT": ["SEA_IMP", "AIR_IMP"],
        "DOM_CUSTOMS": ["BORDER_IMP", "CUS_SUBMITTED"],
        "TRUCKING": ["TRUCKING_DOM", "TRUCKING_SHORT", "TRUCKING_LONG"],
        "EXPORT": ["SEA_EXP", "AIR_EXP"],
    }
    svc_codes = svc_type_map.get(svc_type, [])
    if svc_codes and jobs:
        job_ids_all = [j['job_id'] for j in jobs]
        svcs = client.table('job_services').select('job_id').in_(
            'job_id', job_ids_all
        ).in_('service_type_code', svc_codes).execute()
        matching = set(s['job_id'] for s in (svcs.data or []))
        jobs = [j for j in jobs if j['job_id'] in matching]

    if not jobs:
        logger.info(f"No jobs found for customer {customer_id} in {month} (svc_type={svc_type})")
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
