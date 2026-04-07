"""
Google Drive Upload Service — upload documents to company Google Drive.

Uses OAuth2 refresh token for authentication (no interactive login needed).
Auto-creates folder structure: 5P-Documents/{YYYY}/{MM}/{customer_name}/{job_no}/
Returns shareable download link after upload.
"""

import io
import logging
from typing import Optional
from datetime import datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from app.core.config import settings

logger = logging.getLogger(__name__)

# Cache the Drive service instance
_drive_service = None
_root_folder_id = None

GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
ROOT_FOLDER_NAME = "5P-Documents"


def _get_drive_service():
    """Get or create cached Google Drive service instance."""
    global _drive_service
    if _drive_service:
        return _drive_service

    if not all([settings.GDRIVE_REFRESH_TOKEN, settings.GDRIVE_CLIENT_ID, settings.GDRIVE_CLIENT_SECRET]):
        logger.error("Google Drive credentials not configured")
        return None

    try:
        creds = Credentials(
            token=None,
            refresh_token=settings.GDRIVE_REFRESH_TOKEN,
            token_uri=GOOGLE_TOKEN_URI,
            client_id=settings.GDRIVE_CLIENT_ID,
            client_secret=settings.GDRIVE_CLIENT_SECRET,
        )
        _drive_service = build('drive', 'v3', credentials=creds)
        logger.info("Google Drive service initialized")
        return _drive_service
    except Exception as e:
        logger.error(f"Failed to init Google Drive: {e}")
        return None


def _find_or_create_folder(service, name: str, parent_id: str) -> Optional[str]:
    """Find existing folder by name under parent, or create it."""
    try:
        # Search for existing folder
        query = (
            f"name='{name}' and mimeType='application/vnd.google-apps.folder' "
            f"and '{parent_id}' in parents and trashed=false"
        )
        results = service.files().list(q=query, fields="files(id)").execute()
        files = results.get('files', [])
        if files:
            return files[0]['id']

        # Create new folder
        metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id],
        }
        folder = service.files().create(body=metadata, fields='id').execute()
        logger.info(f"Created GDrive folder: {name}")
        return folder['id']
    except Exception as e:
        logger.error(f"Folder create/find error for '{name}': {e}")
        return None


def _get_root_folder_id(service) -> Optional[str]:
    """Get or create the root '5P-Documents' folder."""
    global _root_folder_id

    # Use configured folder ID if set
    if settings.GDRIVE_ROOT_FOLDER_ID:
        _root_folder_id = settings.GDRIVE_ROOT_FOLDER_ID
        return _root_folder_id

    if _root_folder_id:
        return _root_folder_id

    try:
        # Search in My Drive root
        query = (
            f"name='{ROOT_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' "
            f"and 'root' in parents and trashed=false"
        )
        results = service.files().list(q=query, fields="files(id)").execute()
        files = results.get('files', [])
        if files:
            _root_folder_id = files[0]['id']
            return _root_folder_id

        # Create root folder
        metadata = {
            'name': ROOT_FOLDER_NAME,
            'mimeType': 'application/vnd.google-apps.folder',
        }
        folder = service.files().create(body=metadata, fields='id').execute()
        _root_folder_id = folder['id']
        logger.info(f"Created root GDrive folder: {ROOT_FOLDER_NAME}")
        return _root_folder_id
    except Exception as e:
        logger.error(f"Root folder error: {e}")
        return None


def _build_folder_path(service, root_id: str, customer_name: str, job_no: str) -> Optional[str]:
    """
    Build nested folder structure and return target folder ID.
    Structure: 5P-Documents/{YYYY}/{MM}/{customer_name}/{job_no}/
    """
    now = datetime.now()
    year = str(now.year)
    month = f"{now.month:02d}"

    # Clean names for folder use
    customer_clean = (customer_name or "Unknown").strip().replace('/', '-')
    job_clean = (job_no or "Unknown").strip().replace('/', '-')

    # Create nested folders: year → month → customer → job
    year_id = _find_or_create_folder(service, year, root_id)
    if not year_id:
        return None
    month_id = _find_or_create_folder(service, month, year_id)
    if not month_id:
        return None
    cust_id = _find_or_create_folder(service, customer_clean, month_id)
    if not cust_id:
        return None
    job_id = _find_or_create_folder(service, job_clean, cust_id)
    return job_id


def upload_to_gdrive(
    file_bytes: bytes,
    file_name: str,
    mime_type: str,
    customer_name: str,
    job_no: str,
) -> Optional[str]:
    """
    Upload file to Google Drive with organized folder structure.
    Returns shareable web link or None on error.
    """
    if not settings.GDRIVE_ENABLED:
        return None

    service = _get_drive_service()
    if not service:
        return None

    try:
        root_id = _get_root_folder_id(service)
        if not root_id:
            return None

        # Build folder path
        target_folder_id = _build_folder_path(service, root_id, customer_name, job_no)
        if not target_folder_id:
            return None

        # Upload file
        metadata = {
            'name': file_name,
            'parents': [target_folder_id],
        }
        media = MediaIoBaseUpload(
            io.BytesIO(file_bytes),
            mimetype=mime_type or 'application/octet-stream',
            resumable=True,
        )
        uploaded = service.files().create(
            body=metadata, media_body=media, fields='id,webViewLink'
        ).execute()

        file_id = uploaded.get('id')
        web_link = uploaded.get('webViewLink')

        # Make file accessible via link (anyone with link can view)
        service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'},
        ).execute()

        # Get the direct download/view link
        logger.info(f"Uploaded to GDrive: {file_name} → {web_link}")
        return web_link

    except Exception as e:
        logger.error(f"GDrive upload error for {file_name}: {e}")
        return None
