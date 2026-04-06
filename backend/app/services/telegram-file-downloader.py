"""
Telegram File Downloader — download files from Telegram Bot API.

Used when kế toán clicks "Download" in web UI:
1. Get file path from Telegram getFile API using file_id
2. Download file bytes from Telegram file server
3. Return bytes + metadata for streaming to browser
"""

import logging
from typing import Optional, Tuple

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Telegram Bot API file size limit for getFile: 20MB
MAX_FILE_SIZE = 20 * 1024 * 1024


async def get_telegram_file_path(file_id: str) -> Optional[str]:
    """
    Call Telegram getFile API to get the file_path for download.
    Returns file_path string or None on error.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not configured")
        return None

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getFile"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params={'file_id': file_id}, timeout=15)
            data = resp.json()
            if data.get('ok') and data.get('result', {}).get('file_path'):
                return data['result']['file_path']
            logger.error(f"getFile failed for {file_id}: {data}")
            return None
    except Exception as e:
        logger.error(f"getFile error for {file_id}: {e}")
        return None


async def download_telegram_file(file_id: str) -> Optional[Tuple[bytes, str]]:
    """
    Download file from Telegram by file_id.
    Returns (file_bytes, file_path) tuple or None on error.

    Two-step process:
    1. getFile → get file_path
    2. Download from https://api.telegram.org/file/bot{token}/{file_path}
    """
    file_path = await get_telegram_file_path(file_id)
    if not file_path:
        return None

    download_url = (
        f"https://api.telegram.org/file/bot"
        f"{settings.TELEGRAM_BOT_TOKEN}/{file_path}"
    )
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(download_url, timeout=30)
            if resp.status_code == 200:
                return (resp.content, file_path)
            logger.error(f"Download failed ({resp.status_code}): {download_url}")
            return None
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None


async def send_file_to_telegram(
    chat_id: str,
    file_bytes: bytes,
    filename: str,
    caption: Optional[str] = None,
) -> Optional[str]:
    """
    Upload a file to Telegram via sendDocument API.
    Used for web upload fallback — stores file on Telegram and returns file_id.
    Returns telegram file_id or None on error.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not configured")
        return None

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        async with httpx.AsyncClient() as client:
            files = {'document': (filename, file_bytes)}
            data = {'chat_id': chat_id}
            if caption:
                data['caption'] = caption

            resp = await client.post(url, files=files, data=data, timeout=30)
            result = resp.json()
            if result.get('ok'):
                doc = result['result'].get('document', {})
                return doc.get('file_id')
            logger.error(f"sendDocument failed: {result}")
            return None
    except Exception as e:
        logger.error(f"sendDocument error: {e}")
        return None
