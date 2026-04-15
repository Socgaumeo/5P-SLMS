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
tg_downloader = importlib.import_module("app.services.telegram-file-downloader")
gdrive_svc = importlib.import_module("app.services.google-drive-upload-service")

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
    # Document (PDF, Excel, Word, ZIP, etc.)
    if 'document' in message:
        doc = message['document']
        file_name = doc.get('file_name', 'unnamed_file')
        mime_type = doc.get('mime_type', 'application/octet-stream')
        # Detect ZIP/archive
        is_zip = (
            mime_type in ('application/zip', 'application/x-zip-compressed', 'application/x-rar-compressed')
            or file_name.lower().endswith(('.zip', '.rar', '.7z'))
        )
        return {
            'file_id': doc['file_id'],
            'file_name': file_name,
            'file_size': doc.get('file_size'),
            'mime_type': mime_type,
            'is_zip': is_zip,
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


async def _handle_text_command(text: str, message: dict, chat_id: str, message_id: int):
    """Handle text-only commands: /xoa, /job, /clearjob, /help"""
    text_lower = text.lower()

    # /xoa or /delete — delete document (must reply to original file message)
    if text_lower in ('/xoa', '/delete'):
        reply = message.get('reply_to_message')
        if not reply:
            await bot_svc.send_telegram_message(
                chat_id, "⚠️ Reply vào tin nhắn chứa file cần xoá rồi gõ /xoa", message_id
            )
            return {"ok": True}

        # Try to delete by the replied-to message's ID
        replied_msg_id = reply.get('message_id')
        deleted = bot_svc.delete_document_by_message(chat_id, replied_msg_id)
        if deleted:
            await bot_svc.send_telegram_message(
                chat_id, f"🗑️ Đã xoá chứng từ: <b>{deleted['file_name']}</b>", message_id
            )
        else:
            await bot_svc.send_telegram_message(
                chat_id, "❌ Không tìm thấy chứng từ để xoá.", message_id
            )
        return {"ok": True, "action": "delete"}

    # /job SEA-46-2503-001 — set active job for batch uploads
    if text_lower.startswith('/job'):
        job_no = bot_svc.extract_job_no(text)
        if not job_no:
            await bot_svc.send_telegram_message(
                chat_id, "⚠️ Cú pháp: <code>/job AI-1404-716</code> hoặc <code>/job SEA-46-2503-001</code>", message_id
            )
            return {"ok": True}

        job = bot_svc.validate_job(job_no)
        if not job:
            await bot_svc.send_telegram_message(
                chat_id, f"❌ Không tìm thấy job <code>{job_no}</code>", message_id
            )
            return {"ok": True}

        sender = _get_sender_info(message)
        bot_svc.set_chat_job(chat_id, job_no, job, sender)
        await bot_svc.send_telegram_message(
            chat_id,
            f"📌 <b>Đã set job: {job_no}</b> ({job.get('customer_name', '')})\n"
            f"Bây giờ gửi file không cần caption, tự động gán vào job này.\n"
            f"Gõ /clearjob khi xong.",
            message_id,
        )
        return {"ok": True, "action": "set_job"}

    # /clearjob — clear active job
    if text_lower.startswith('/clearjob'):
        bot_svc.clear_chat_job(chat_id)
        await bot_svc.send_telegram_message(
            chat_id, "✅ Đã xoá job đang active. Gửi file cần kèm caption.", message_id
        )
        return {"ok": True, "action": "clear_job"}

    # /help
    if text_lower.startswith('/help'):
        help_msg = (
            bot_svc.format_missing_info_message() +
            "\n\n<b>Lệnh khác:</b>\n"
            "• <code>/job SEA-46-2503-001</code> — Set job, gửi nhiều file không cần caption\n"
            "• <code>/clearjob</code> — Xoá job đang active\n"
            "• <code>/xoa</code> — Reply vào file cần xoá"
        )
        await bot_svc.send_telegram_message(chat_id, help_msg, message_id)
        return {"ok": True}

    return {"ok": True}


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

    # Handle text commands (not file messages)
    text = message.get('text', '').strip()
    if text and not _extract_file_info(message):
        return await _handle_text_command(text, message, chat_id, message_id)

    # Extract file info
    file_info = _extract_file_info(message)
    if not file_info:
        return {"ok": True}

    # Get caption and sender
    caption = message.get('caption', '') or ''
    sender = _get_sender_info(message)

    # Extract job_no from caption, fallback to chat session job
    job_no = bot_svc.extract_job_no(caption)
    session_job = bot_svc.get_chat_job(chat_id)

    if not job_no and session_job:
        # Use active session job (batch mode)
        job_no = session_job['job_no']

    if not job_no:
        # No job_no found — ask user
        await bot_svc.send_telegram_message(
            chat_id, bot_svc.format_missing_info_message(), message_id
        )
        return {"ok": True, "action": "asked_for_info"}

    # Validate job exists (use cached session job if same job_no)
    if session_job and session_job['job_no'] == job_no:
        job = {'job_id': session_job['job_id'], 'customer_name': session_job['customer_name'], 'job_no': job_no}
    else:
        job = bot_svc.validate_job(job_no)
    if not job:
        await bot_svc.send_telegram_message(
            chat_id,
            f"❌ Không tìm thấy job <code>{job_no}</code> trong hệ thống.\n"
            f"Vui lòng kiểm tra lại số job.",
            message_id,
        )
        return {"ok": True, "action": "job_not_found"}

    # Detect doc_type — ZIP bundle không cần caption, ghi notes là 'zip_bundle'
    if file_info.get('is_zip'):
        doc_type = 'OTHER'
        if not caption:
            caption = 'zip_bundle'
    else:
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
        # Upload to Google Drive (async background, non-blocking)
        gdrive_url = None
        if settings.GDRIVE_ENABLED:
            try:
                dl_result = await tg_downloader.download_telegram_file(file_info['file_id'])
                if dl_result:
                    file_bytes, _ = dl_result
                    gdrive_url = gdrive_svc.upload_to_gdrive(
                        file_bytes=file_bytes,
                        file_name=file_info['file_name'],
                        mime_type=file_info.get('mime_type', 'application/octet-stream'),
                        customer_name=job.get('customer_name', ''),
                        job_no=job_no,
                    )
                    if gdrive_url:
                        bot_svc.update_document_gdrive_url(document['id'], gdrive_url)
                else:
                    logger.warning(f"Could not download file from Telegram for GDrive backup")
            except Exception as e:
                logger.error(f"GDrive upload failed: {e}")

        # Send confirmation reply (with GDrive link if available)
        confirm_msg = bot_svc.format_confirm_message(
            file_info['file_name'], job_no, doc_type, gdrive_url
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
