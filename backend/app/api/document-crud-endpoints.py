"""
Document CRUD API — list, download, web upload, delete, batch ZIP, stats.

Endpoints:
  GET    /api/documents                  — List documents (filter by job_id, customer_id, month, doc_type)
  GET    /api/documents/{id}/download    — Download file via Telegram getFile API
  POST   /api/documents/upload           — Web upload fallback (multipart form)
  DELETE /api/documents/{id}             — Delete document (admin or uploader)
  POST   /api/documents/batch-download   — Download multiple files as ZIP
  GET    /api/documents/stats            — Summary counts by doc_type and month
"""

import io
import zipfile
import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.dependencies import get_current_user, require_manager_or_admin
from app.db.supabase_client import get_supabase
from app.core.config import settings

import importlib
telegram_downloader = importlib.import_module("app.services.telegram-file-downloader")

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["Documents"])

# Allowed file extensions for web upload
ALLOWED_EXTENSIONS = {'.pdf', '.xlsx', '.xls', '.docx', '.doc', '.png', '.jpg', '.jpeg'}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB (Telegram limit)

# MIME type mapping
MIME_MAP = {
    '.pdf': 'application/pdf',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xls': 'application/vnd.ms-excel',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.doc': 'application/msword',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
}


class BatchDownloadRequest(BaseModel):
    document_ids: List[str]


# ─── DOCUMENT STATS (must be before /{document_id} routes) ────
@router.get("/stats")
async def document_stats(
    month: Optional[str] = Query(None, description="YYYY-MM"),
    customer_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Get document summary counts by doc_type."""
    try:
        client = get_supabase()
        query = client.table('documents').select('doc_type, job_id', count='exact')

        if month:
            start = f"{month}-01T00:00:00"
            year, mon = month.split('-')
            if int(mon) == 12:
                end = f"{int(year)+1}-01-01T00:00:00"
            else:
                end = f"{year}-{int(mon)+1:02d}-01T00:00:00"
            query = query.gte('uploaded_at', start).lt('uploaded_at', end)

        result = query.execute()

        # Aggregate counts by doc_type
        type_counts = {}
        for doc in result.data:
            dt = doc['doc_type']
            type_counts[dt] = type_counts.get(dt, 0) + 1

        return {
            "total": result.count,
            "by_type": type_counts,
            "month": month,
        }

    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(500, f"Stats error: {str(e)}")


# ─── LIST DOCUMENTS ───────────────────────────────────────────
@router.get("")
async def list_documents(
    job_id: Optional[int] = Query(None),
    customer_id: Optional[int] = Query(None),
    doc_type: Optional[str] = Query(None),
    month: Optional[str] = Query(None, description="YYYY-MM"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    current_user: dict = Depends(get_current_user),
):
    """List documents with optional filters."""
    try:
        client = get_supabase()
        query = client.table('documents').select(
            '*, jobs(job_no, customer_id, customers(short_name, company_name)), uploader:users!documents_uploaded_by_fkey(user_id, full_name, user_code)',
            count='exact'
        )

        if job_id:
            query = query.eq('job_id', job_id)
        if doc_type:
            query = query.eq('doc_type', doc_type)
        if month:
            # Filter by uploaded_at month
            start = f"{month}-01T00:00:00"
            # Calculate end of month
            year, mon = month.split('-')
            if int(mon) == 12:
                end = f"{int(year)+1}-01-01T00:00:00"
            else:
                end = f"{year}-{int(mon)+1:02d}-01T00:00:00"
            query = query.gte('uploaded_at', start).lt('uploaded_at', end)
        if customer_id:
            # Filter via job's customer_id
            job_ids_result = client.table('jobs').select('job_id').eq(
                'customer_id', customer_id
            ).execute()
            if job_ids_result.data:
                ids = [j['job_id'] for j in job_ids_result.data]
                query = query.in_('job_id', ids)
            else:
                return {"data": [], "total": 0}

        query = query.order('uploaded_at', desc=True).range(offset, offset + limit - 1)
        result = query.execute()

        return {"data": result.data, "total": result.count}
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(500, f"Error listing documents: {str(e)}")


# ─── DOWNLOAD SINGLE FILE ────────────────────────────────────
@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Download a document file. Fetches from Telegram API or redirects to external URL."""
    try:
        client = get_supabase()
        result = client.table('documents').select('*').eq('id', document_id).limit(1).execute()

        if not result.data:
            raise HTTPException(404, "Document not found")

        doc = result.data[0]

        # Handle different storage types
        if doc['storage_type'] in ('telegram', 'web_upload') and doc.get('telegram_file_id'):
            # Download from Telegram
            file_data = await telegram_downloader.download_telegram_file(doc['telegram_file_id'])
            if not file_data:
                raise HTTPException(502, "Failed to download file from Telegram")

            file_bytes, _ = file_data
            content_type = doc.get('mime_type', 'application/octet-stream')

            return StreamingResponse(
                io.BytesIO(file_bytes),
                media_type=content_type,
                headers={
                    'Content-Disposition': f'attachment; filename="{doc["file_name"]}"',
                    'Content-Length': str(len(file_bytes)),
                }
            )

        elif doc.get('external_url'):
            # Fetch from external URL (Supabase Storage etc.) and stream with proper filename
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                r = await http_client.get(doc['external_url'])
                if r.status_code != 200:
                    raise HTTPException(502, f"Failed to fetch external file: HTTP {r.status_code}")
                file_bytes = r.content
            content_type = doc.get('mime_type') or r.headers.get('content-type') or 'application/octet-stream'
            return StreamingResponse(
                io.BytesIO(file_bytes),
                media_type=content_type,
                headers={
                    'Content-Disposition': f'attachment; filename="{doc["file_name"]}"',
                    'Content-Length': str(len(file_bytes)),
                }
            )

        else:
            raise HTTPException(404, "No file source available for this document")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error for {document_id}: {e}")
        raise HTTPException(500, f"Download error: {str(e)}")


# ─── PDF CONVERT (image → cleaned scan PDF) ──────────────────
@router.get("/{document_id}/pdf")
async def download_document_as_pdf(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Convert an image document to a cleaned scan-style PDF.
    - Filename theo invoice ref (giữ file_name gốc, đổi ext → .pdf)
    - Crop viền, tăng contrast, nền trắng
    """
    import os
    try:
        client = get_supabase()
        result = client.table('documents').select('*').eq('id', document_id).limit(1).execute()
        if not result.data:
            raise HTTPException(404, "Document not found")
        doc = result.data[0]

        mime = (doc.get('mime_type') or '').lower()
        if not mime.startswith('image/'):
            raise HTTPException(400, "PDF convert chỉ hỗ trợ file ảnh")

        # Get raw bytes
        if doc.get('external_url'):
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                r = await http_client.get(doc['external_url'])
                if r.status_code != 200:
                    raise HTTPException(502, f"Failed to fetch external file: HTTP {r.status_code}")
                raw = r.content
        elif doc.get('telegram_file_id'):
            file_data = await telegram_downloader.download_telegram_file(doc['telegram_file_id'])
            if not file_data:
                raise HTTPException(502, "Failed to download file from Telegram")
            raw, _ = file_data
        else:
            raise HTTPException(404, "No file source available")

        # Scan-clean pipeline
        from PIL import Image, ImageOps, ImageEnhance
        import numpy as np
        img = Image.open(io.BytesIO(raw)).convert('RGB')
        w, h = img.size
        # Auto-crop 2% viền
        margin = int(min(w, h) * 0.02)
        img = img.crop((margin, margin, w - margin, h - margin))
        # Auto-contrast + boost brightness/contrast
        img = ImageOps.autocontrast(img, cutoff=2)
        img = ImageEnhance.Contrast(img).enhance(1.4)
        img = ImageEnhance.Brightness(img).enhance(1.1)
        # Nền trắng: pixel gần trắng → trắng thuần
        arr = np.array(img)
        white_mask = (arr[:, :, 0] > 200) & (arr[:, :, 1] > 200) & (arr[:, :, 2] > 200)
        arr[white_mask] = [255, 255, 255]
        img = Image.fromarray(arr)

        # Wrap PDF (fit A4)
        buf = io.BytesIO()
        img.save(buf, 'PDF', resolution=150.0)
        buf.seek(0)

        # Filename: giữ ref, đổi ext
        base = os.path.splitext(doc['file_name'])[0]
        pdf_name = f"{base}.pdf"

        return StreamingResponse(
            buf,
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{pdf_name}"',
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF convert error for {document_id}: {e}")
        raise HTTPException(500, f"PDF convert error: {str(e)}")


# ─── WEB UPLOAD (FALLBACK) ───────────────────────────────────
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    job_id: int = Form(...),
    doc_type: str = Form(...),
    notes: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload document via web UI (fallback for non-Telegram uploads).
    Sends file to Telegram storage chat to get file_id, then inserts DB record.
    """
    import os

    # Validate file extension
    ext = os.path.splitext(file.filename or '')[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type {ext} not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    # Validate doc_type
    valid_types = ['AN', 'DEBIT', 'DO', 'CD', 'CO', 'INVOICE', 'AWB', 'BL', 'PACKING_LIST', 'OTHER']
    if doc_type not in valid_types:
        raise HTTPException(400, f"Invalid doc_type. Must be one of: {', '.join(valid_types)}")

    # Validate job exists
    client = get_supabase()
    job_result = client.table('jobs').select('job_id, job_no').eq('job_id', job_id).limit(1).execute()
    if not job_result.data:
        raise HTTPException(404, f"Job {job_id} not found")

    try:
        file_bytes = await file.read()

        # Check file size
        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(400, f"File too large. Max {MAX_FILE_SIZE // (1024*1024)}MB")

        mime_type = MIME_MAP.get(ext, 'application/octet-stream')

        # Send to Telegram storage chat to get file_id
        telegram_file_id = None
        storage_chat = settings.TELEGRAM_STORAGE_CHAT_ID
        if storage_chat and settings.TELEGRAM_BOT_TOKEN:
            telegram_file_id = await telegram_downloader.send_file_to_telegram(
                chat_id=storage_chat,
                file_bytes=file_bytes,
                filename=file.filename,
                caption=f"Web upload: {job_result.data[0]['job_no']} {doc_type}",
            )

        # Insert document record
        doc_data = {
            'job_id': job_id,
            'doc_type': doc_type,
            'file_name': file.filename,
            'file_size': len(file_bytes),
            'mime_type': mime_type,
            'storage_type': 'web_upload',
            'telegram_file_id': telegram_file_id,
            'uploaded_by': current_user.get('user_id'),
            'cloud_backup_status': 'pending',
            'notes': notes,
        }
        result = client.table('documents').insert(doc_data).execute()

        if result.data:
            return {"success": True, "document": result.data[0]}
        raise HTTPException(500, "Failed to save document record")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(500, f"Upload error: {str(e)}")


# ─── DELETE DOCUMENT ──────────────────────────────────────────
@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a document. Admin can delete any, staff can only delete own uploads."""
    try:
        client = get_supabase()
        result = client.table('documents').select('id, uploaded_by').eq('id', document_id).limit(1).execute()

        if not result.data:
            raise HTTPException(404, "Document not found")

        doc = result.data[0]
        user_role = current_user.get('role', '')
        user_id = current_user.get('user_id')

        # Permission check: admin can delete any, others only own uploads
        if user_role != 'ADMIN' and doc.get('uploaded_by') != user_id:
            raise HTTPException(403, "You can only delete your own uploads")

        # Delete from DB (file stays on Telegram — no cost to keep)
        client.table('documents').delete().eq('id', document_id).execute()
        return {"success": True, "deleted_id": document_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error for {document_id}: {e}")
        raise HTTPException(500, f"Delete error: {str(e)}")


# ─── BATCH DOWNLOAD AS ZIP ───────────────────────────────────
@router.post("/batch-download")
async def batch_download(
    request: BatchDownloadRequest,
    current_user: dict = Depends(get_current_user),
):
    """Download multiple documents as a ZIP file."""
    if len(request.document_ids) > 50:
        raise HTTPException(400, "Max 50 files per batch download")

    try:
        client = get_supabase()
        result = client.table('documents').select('*').in_('id', request.document_ids).execute()

        if not result.data:
            raise HTTPException(404, "No documents found")

        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for doc in result.data:
                if doc.get('telegram_file_id'):
                    file_data = await telegram_downloader.download_telegram_file(
                        doc['telegram_file_id']
                    )
                    if file_data:
                        file_bytes, _ = file_data
                        # Use doc_type/filename to organize in ZIP
                        zip_path = f"{doc['doc_type']}/{doc['file_name']}"
                        zf.writestr(zip_path, file_bytes)

        zip_buffer.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"documents_{timestamp}.zip"

        return StreamingResponse(
            zip_buffer,
            media_type='application/zip',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch download error: {e}")
        raise HTTPException(500, f"Batch download error: {str(e)}")


