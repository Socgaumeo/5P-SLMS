"""
Telegram Bot Service — parse captions, validate jobs, detect doc types.

Handles the business logic for Telegram document capture:
- Extract job_no from message caption using regex patterns
- Detect doc_type from keywords in caption or filename
- Validate job exists in database
- Send reply messages via Telegram Bot API
"""

import re
import logging
from typing import Optional

import httpx

from app.core.config import settings
from app.db.supabase_client import get_supabase

logger = logging.getLogger(__name__)

# --- Job number patterns (match existing formats in DB) ---
# Format: PREFIX-CUSTID-YYMM-SEQ (e.g. SEA-46-2503-001, AIR-20-2503-015)
JOB_NO_PATTERNS = [
    re.compile(r'((?:SEA|AIR|CUS|TRK|WHS|IMP)-\d+-\d{4}-\d{3})', re.IGNORECASE),  # SEA-46-2503-001
    re.compile(r'(LG\d{4}/\d{3})', re.IGNORECASE),           # LG2604/001
    re.compile(r'#(LG\d{7})', re.IGNORECASE),                  # #LG2604001 → LG2604/001
]

# --- Doc type detection keywords (Vietnamese + English) ---
DOC_TYPE_KEYWORDS = {
    'AN': ['arrival notice', 'arrival', ' an ', 'giấy báo hàng đến'],
    'DEBIT': ['debit', 'debit note', 'phiếu ghi nợ'],
    'DO': ['delivery order', ' do ', 'lệnh giao hàng'],
    'CD': ['customs declaration', ' cd ', 'tờ khai', 'tờ khai hải quan'],
    'CO': ['certificate of origin', ' co ', 'c/o', 'giấy chứng nhận xuất xứ'],
    'INVOICE': ['invoice', 'hóa đơn', 'hoa don', 'hoá đơn'],
    'AWB': ['awb', 'air waybill', 'vận đơn hàng không'],
    'BL': ['bill of lading', ' bl ', 'b/l', 'vận đơn đường biển'],
    'PACKING_LIST': ['packing list', 'packing', 'phiếu đóng gói'],
}


def extract_job_no(text: str) -> Optional[str]:
    """
    Extract job number from caption text.
    Tries multiple patterns and normalizes format.
    Returns None if no match found.
    """
    if not text:
        return None

    for pattern in JOB_NO_PATTERNS:
        match = pattern.search(text)
        if match:
            job_no = match.group(1)
            # Normalize #LG2604001 → LG2604/001
            if job_no.startswith('LG') and '/' not in job_no and len(job_no) == 9:
                job_no = f"{job_no[:6]}/{job_no[6:]}"
            return job_no.upper()
    return None


def detect_doc_type(caption: str, filename: str = "") -> str:
    """
    Detect document type from caption keywords or filename.
    Returns doc_type string or 'OTHER' if no match.
    """
    search_text = f" {caption} {filename} ".lower()

    for doc_type, keywords in DOC_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in search_text:
                return doc_type
    return 'OTHER'


def validate_job(job_no: str) -> Optional[dict]:
    """
    Check if job_no exists in database.
    Returns job record dict with customer info or None.
    """
    try:
        client = get_supabase()
        result = client.table('jobs').select(
            'job_id, job_no, customer_id, status_code, customers(short_name)'
        ).eq('job_no', job_no).limit(1).execute()

        if result.data:
            row = result.data[0]
            customer = row.pop('customers', {}) or {}
            row['customer_name'] = customer.get('short_name', '')
            return row
        return None
    except Exception as e:
        logger.error(f"Error validating job {job_no}: {e}")
        return None


def insert_document(
    job_id: int,
    doc_type: str,
    file_name: str,
    file_size: Optional[int],
    mime_type: Optional[str],
    telegram_file_id: str,
    telegram_message_id: int,
    telegram_chat_id: str,
    uploaded_by_telegram: str,
    notes: Optional[str] = None,
) -> Optional[dict]:
    """Insert document record into database. Returns created record or None."""
    try:
        client = get_supabase()
        data = {
            'job_id': job_id,
            'doc_type': doc_type,
            'file_name': file_name,
            'file_size': file_size,
            'mime_type': mime_type,
            'storage_type': 'telegram',
            'telegram_file_id': telegram_file_id,
            'telegram_message_id': telegram_message_id,
            'telegram_chat_id': str(telegram_chat_id),
            'uploaded_by_telegram': uploaded_by_telegram,
            'cloud_backup_status': 'pending',
            'notes': notes,
        }
        result = client.table('documents').insert(data).execute()
        if result.data:
            logger.info(f"Document captured: {file_name} → job {job_id} ({doc_type})")
            return result.data[0]
        return None
    except Exception as e:
        logger.error(f"Error inserting document: {e}")
        return None


async def send_telegram_message(chat_id: str, text: str, reply_to_message_id: Optional[int] = None):
    """Send a message via Telegram Bot API."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping message send")
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
    }
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=10)
            if resp.status_code != 200:
                logger.error(f"Telegram sendMessage failed: {resp.text}")
    except Exception as e:
        logger.error(f"Telegram sendMessage error: {e}")


def is_allowed_chat(chat_id: str) -> bool:
    """Check if chat_id is in the whitelist. Empty whitelist = allow all."""
    allowed = settings.TELEGRAM_ALLOWED_CHAT_IDS.strip()
    if not allowed:
        return True  # No whitelist = allow all
    allowed_ids = [cid.strip() for cid in allowed.split(',')]
    return str(chat_id) in allowed_ids


def update_document_gdrive_url(doc_id: int, gdrive_url: str):
    """Update document record with Google Drive link."""
    try:
        client = get_supabase()
        client.table('documents').update({
            'external_url': gdrive_url,
            'cloud_backup_status': 'synced',
        }).eq('id', doc_id).execute()
    except Exception as e:
        logger.error(f"Error updating gdrive_url for doc {doc_id}: {e}")


def format_confirm_message(file_name: str, job_no: str, doc_type: str, gdrive_url: str = None) -> str:
    """Format a confirmation reply message."""
    type_labels = {
        'AN': 'Arrival Notice', 'DEBIT': 'Debit Note', 'DO': 'Delivery Order',
        'CD': 'Customs Declaration', 'CO': 'C/O', 'INVOICE': 'Hóa đơn',
        'AWB': 'Air Waybill', 'BL': 'Bill of Lading',
        'PACKING_LIST': 'Packing List', 'OTHER': 'Khác',
    }
    label = type_labels.get(doc_type, doc_type)
    msg = (
        f"✅ <b>Đã lưu chứng từ</b>\n"
        f"📄 {file_name}\n"
        f"📋 Job: <code>{job_no}</code>\n"
        f"🏷️ Loại: {label}"
    )
    if gdrive_url:
        msg += f"\n📁 <a href=\"{gdrive_url}\">Tải về từ Google Drive</a>"
    return msg


def format_missing_info_message() -> str:
    """Format a message asking for missing job_no."""
    return (
        "⚠️ <b>Thiếu thông tin!</b>\n\n"
        "Vui lòng gửi lại file kèm caption:\n"
        "<code>[Số Job] [Loại chứng từ]</code>\n\n"
        "Ví dụ:\n"
        "• <code>LG2604/001 AN</code>\n"
        "• <code>TRK-1903-0004 debit</code>\n"
        "• <code>LG2604/001 DO</code>\n\n"
        "Loại chứng từ: AN, DEBIT, DO, CD, CO, INVOICE, AWB, BL, PACKING_LIST"
    )
