"""
Telegram Webhook Handler — receive Telegram updates, auto-capture documents.

Endpoint: POST /api/telegram/webhook
- Receives Telegram updates (messages with documents/photos)
- Parses caption for job_no + doc_type
- Validates job exists in DB
- Inserts document record with telegram_file_id
- Replies with confirmation or asks for missing info

Security:
- Verifies X-Telegram-Bot-Api-Secret-Token header
- Checks chat_id whitelist (configurable)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Header

import importlib
from app.core.config import settings
bot_svc = importlib.import_module("app.services.telegram-bot-service")

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/telegram", tags=["Telegram Webhook"])

# Supported file MIME types
ALLOWED_MIME_PREFIXES = [
    'application/pdf',
    'application/vnd.openxmlformats',  # xlsx, docx
    'application/vnd.ms-excel',        # xls
    'application/msword',              # doc
    'image/png', 'image/jpeg', 'image/jpg',
    'application/octet-stream',        # generic binary
]


def _extract_file_info(message: dict) -> Optional[dict]:
    """
    Extract file info from Telegram message.
    Handles both 'document' and 'photo' message types.
    Returns dict with file_id, file_name, file_size, mime_type or None.
    """
    # Document (PDF, Excel, Word, etc.)
    if 'document' in message:
        doc = message['document']
        return {
            'file_id': doc['file_id'],
            'file_name': doc.get('file_name', 'unnamed_file'),
            'file_size': doc.get('file_size'),
            'mime_type': doc.get('mime_type', 'application/octet-stream'),
        }

    # Photo (highest resolution = last in array)
    if 'photo' in message and message['photo']:
        photo = message['photo'][-1]  # Largest size
        return {
            'file_id': photo['file_id'],
            'file_name': f"photo_{photo.get('file_unique_id', 'unknown')}.jpg",
            'file_size': photo.get('file_size'),
            'mime_type': 'image/jpeg',
        }

    return None


def _get_sender_info(message: dict) -> str:
    """Extract sender username or name from message."""
    sender = message.get('from', {})
    username = sender.get('username')
    if username:
        return f"@{username}"
    first = sender.get('first_name', '')
    last = sender.get('last_name', '')
    return f"{first} {last}".strip() or 'unknown'


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None),
):
    """
    Receive Telegram webhook updates.
    Auto-captures documents and maps them to jobs.
    """
    # Verify webhook secret (if configured)
    if settings.TELEGRAM_WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
            raise HTTPException(403, "Invalid webhook secret")

    try:
        update = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON")

    message = update.get('message')
    if not message:
        return {"ok": True}  # Ignore non-message updates (edits, etc.)

    chat_id = str(message.get('chat', {}).get('id', ''))
    message_id = message.get('message_id')

    # Check chat whitelist
    if not bot_svc.is_allowed_chat(chat_id):
        logger.debug(f"Ignoring message from non-whitelisted chat: {chat_id}")
        return {"ok": True}

    # Extract file info
    file_info = _extract_file_info(message)
    if not file_info:
        # Not a file message — check if it's a bot command
        text = message.get('text', '')
        if text.startswith('/help'):
            await bot_svc.send_telegram_message(
                chat_id, bot_svc.format_missing_info_message(), message_id
            )
        return {"ok": True}

    # Get caption and sender
    caption = message.get('caption', '') or ''
    sender = _get_sender_info(message)

    # Extract job_no from caption
    job_no = bot_svc.extract_job_no(caption)
    if not job_no:
        # No job_no found — ask user
        await bot_svc.send_telegram_message(
            chat_id, bot_svc.format_missing_info_message(), message_id
        )
        return {"ok": True, "action": "asked_for_info"}

    # Validate job exists
    job = bot_svc.validate_job(job_no)
    if not job:
        await bot_svc.send_telegram_message(
            chat_id,
            f"❌ Không tìm thấy job <code>{job_no}</code> trong hệ thống.\n"
            f"Vui lòng kiểm tra lại số job.",
            message_id,
        )
        return {"ok": True, "action": "job_not_found"}

    # Detect doc_type
    doc_type = bot_svc.detect_doc_type(caption, file_info['file_name'])

    # Insert document record
    document = bot_svc.insert_document(
        job_id=job['job_id'],
        doc_type=doc_type,
        file_name=file_info['file_name'],
        file_size=file_info.get('file_size'),
        mime_type=file_info.get('mime_type'),
        telegram_file_id=file_info['file_id'],
        telegram_message_id=message_id,
        telegram_chat_id=chat_id,
        uploaded_by_telegram=sender,
        notes=caption if caption else None,
    )

    if document:
        # Send confirmation reply
        confirm_msg = bot_svc.format_confirm_message(
            file_info['file_name'], job_no, doc_type
        )
        await bot_svc.send_telegram_message(chat_id, confirm_msg, message_id)
        return {"ok": True, "action": "captured", "document_id": document['id']}
    else:
        await bot_svc.send_telegram_message(
            chat_id,
            "❌ Lỗi hệ thống khi lưu chứng từ. Vui lòng thử lại.",
            message_id,
        )
        return {"ok": True, "action": "error"}
