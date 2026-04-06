"""
Debit Template CRUD + Generation API endpoints.

Template management:
  GET    /api/debit/templates              — List templates (filter by customer_id)
  POST   /api/debit/templates              — Create template (upload Excel + mapping)
  PUT    /api/debit/templates/{id}         — Update mapping or template file
  DELETE /api/debit/templates/{id}         — Delete template

Generation:
  POST   /api/debit/generate               — Single debit note for specific jobs
  POST   /api/debit/batch-generate          — Batch: all jobs for customer + month → ZIP
"""

import os
import logging
import tempfile
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.api.dependencies import get_current_user, require_manager_or_admin
from app.db.supabase_client import get_supabase

import importlib
debit_generator = importlib.import_module("app.services.debit-note-generator-service")

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/debit", tags=["Debit Templates"])


# ─── Pydantic Models ─────────────────────────────────────────

class GenerateRequest(BaseModel):
    template_id: str
    job_ids: List[int]


class BatchGenerateRequest(BaseModel):
    template_id: str
    customer_id: int
    month: str  # YYYY-MM


# ─── TEMPLATE CRUD ────────────────────────────────────────────

@router.get("/templates")
async def list_templates(
    customer_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """List debit templates, optionally filtered by customer."""
    try:
        client = get_supabase()
        query = client.table('debit_templates').select(
            '*, customers(customer_id, customer_code, short_name, company_name)'
        ).eq('is_active', True)

        if customer_id:
            query = query.eq('customer_id', customer_id)

        result = query.order('created_at', desc=True).execute()
        return {"data": result.data, "count": len(result.data)}
    except Exception as e:
        logger.error(f"List templates error: {e}")
        raise HTTPException(500, str(e))


@router.post("/templates")
async def create_template(
    template_name: str = Form(...),
    customer_id: int = Form(...),
    field_mapping: str = Form(...),  # JSON string
    file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(require_manager_or_admin),
):
    """Create a new debit template with optional Excel file upload."""
    import json

    try:
        mapping = json.loads(field_mapping)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid field_mapping JSON")

    try:
        client = get_supabase()

        # Save template file to disk if provided
        local_path = None
        if file:
            ext = os.path.splitext(file.filename or '')[1].lower()
            if ext not in ('.xlsx', '.xls'):
                raise HTTPException(400, "Template must be .xlsx or .xls file")

            # Save to stored_files/templates/
            templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'stored_files', 'templates')
            os.makedirs(templates_dir, exist_ok=True)
            local_path = os.path.join(templates_dir, f"{customer_id}_{template_name.replace(' ', '_')}{ext}")

            content = await file.read()
            with open(local_path, 'wb') as f:
                f.write(content)

        # Insert DB record
        data = {
            'customer_id': customer_id,
            'template_name': template_name,
            'field_mapping': mapping,
            'local_file_path': local_path,
            'is_active': True,
            'created_by': current_user.get('user_id'),
        }
        result = client.table('debit_templates').insert(data).execute()

        if result.data:
            return {"success": True, "template": result.data[0]}
        raise HTTPException(500, "Failed to create template")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create template error: {e}")
        raise HTTPException(500, str(e))


@router.put("/templates/{template_id}")
async def update_template(
    template_id: str,
    template_name: Optional[str] = Form(None),
    field_mapping: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(require_manager_or_admin),
):
    """Update template mapping or re-upload template file."""
    import json

    try:
        client = get_supabase()

        # Check exists
        existing = client.table('debit_templates').select('*').eq('id', template_id).limit(1).execute()
        if not existing.data:
            raise HTTPException(404, "Template not found")

        updates = {'updated_at': 'now()'}
        if template_name:
            updates['template_name'] = template_name
        if field_mapping:
            try:
                updates['field_mapping'] = json.loads(field_mapping)
            except json.JSONDecodeError:
                raise HTTPException(400, "Invalid field_mapping JSON")

        if file:
            ext = os.path.splitext(file.filename or '')[1].lower()
            if ext not in ('.xlsx', '.xls'):
                raise HTTPException(400, "Template must be .xlsx or .xls file")

            tmpl = existing.data[0]
            templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'stored_files', 'templates')
            os.makedirs(templates_dir, exist_ok=True)
            local_path = os.path.join(templates_dir, f"{tmpl['customer_id']}_{(template_name or tmpl['template_name']).replace(' ', '_')}{ext}")

            content = await file.read()
            with open(local_path, 'wb') as f:
                f.write(content)
            updates['local_file_path'] = local_path

        result = client.table('debit_templates').update(updates).eq('id', template_id).execute()
        return {"success": True, "template": result.data[0] if result.data else None}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update template error: {e}")
        raise HTTPException(500, str(e))


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    current_user: dict = Depends(require_manager_or_admin),
):
    """Soft-delete template (set is_active=false)."""
    try:
        client = get_supabase()
        result = client.table('debit_templates').update(
            {'is_active': False}
        ).eq('id', template_id).execute()

        if result.data:
            return {"success": True, "deleted_id": template_id}
        raise HTTPException(404, "Template not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete template error: {e}")
        raise HTTPException(500, str(e))


# ─── GENERATION ───────────────────────────────────────────────

@router.post("/generate")
async def generate_debit_note(
    request: GenerateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate a single debit note for specific jobs."""
    if not request.job_ids:
        raise HTTPException(400, "job_ids cannot be empty")
    if len(request.job_ids) > 100:
        raise HTTPException(400, "Max 100 jobs per generation")

    try:
        file_path = await debit_generator.generate_single(request.template_id, request.job_ids)
        if not file_path:
            raise HTTPException(500, "Failed to generate debit note")

        return FileResponse(
            path=file_path,
            filename=f"debit_note_{request.job_ids[0]}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate error: {e}")
        raise HTTPException(500, str(e))


@router.post("/batch-generate")
async def batch_generate_debit_notes(
    request: BatchGenerateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Batch generate debit notes for all jobs of a customer in a month."""
    try:
        zip_path = await debit_generator.generate_batch(
            request.template_id, request.customer_id, request.month
        )
        if not zip_path:
            raise HTTPException(404, "No jobs found for the specified customer and month")

        return FileResponse(
            path=zip_path,
            filename=f"debit_batch_{request.customer_id}_{request.month}.zip",
            media_type="application/zip",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch generate error: {e}")
        raise HTTPException(500, str(e))
