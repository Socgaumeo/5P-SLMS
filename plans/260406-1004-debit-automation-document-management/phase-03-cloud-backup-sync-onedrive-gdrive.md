# Phase 3 — Cloud Backup Sync (OneDrive / Google Drive)

## Context Links
- [Phase 1 — DB & Telegram Bot](phase-01-database-and-telegram-bot-setup.md)
- [Phase 2 — Document API](phase-02-document-api-endpoints.md)

## Overview
- **Priority:** Medium
- **Status:** Pending
- **Description:** Auto-sync documents from Telegram → OneDrive/Google Drive as backup. Configurable, runs async after capture.

## Key Insights
- Google Drive: Service Account (no user OAuth needed) → share folder with service account email
- OneDrive: Microsoft Graph API → OAuth2 app registration → app-only access
- Sync is async (background task) — không block capture flow
- `cloud_backup_status` column in `documents` table tracks sync state
- Can run as cron job to retry failed syncs

## Requirements

### Functional
- After Telegram capture → queue file for cloud backup
- Download file from Telegram → upload to cloud drive
- Organized folder structure: `5P-SLMS/{year}/{month}/{customer_name}/{job_no}/`
- Track sync status per document (pending/synced/failed/skipped)
- Retry failed syncs (manual trigger or cron)
- Support both Google Drive and OneDrive (configurable)

### Non-functional
- Async — không block main flow
- Retry max 3 times with exponential backoff
- Configurable: enable/disable per cloud provider
- Folder auto-creation if not exists

## Architecture

### Sync Flow
```
Document captured (Phase 1/2)
  → Insert DB record (cloud_backup_status='pending')
  → Queue background task: sync_to_cloud(document_id)
    ├─ Download file bytes from Telegram getFile API
    ├─ Build cloud path: 5P-SLMS/2026/04/MEIKO/LG2604-001/AN_hoadan.pdf
    ├─ Upload to configured cloud provider(s)
    ├─ Update documents.cloud_backup_path + cloud_backup_status='synced'
    └─ On error: cloud_backup_status='failed', log error, retry later
```

### Cloud Folder Structure
```
5P-SLMS/                          # Root folder (shared/configured)
├── 2026/
│   ├── 04/
│   │   ├── MEIKO/
│   │   │   ├── LG2604-001/
│   │   │   │   ├── AN_arrival-notice.pdf
│   │   │   │   ├── DEBIT_debit-note.xlsx
│   │   │   │   └── DO_delivery-order.pdf
│   │   │   └── LG2604-002/
│   │   │       └── ...
│   │   └── SAMSUNG/
│   │       └── ...
│   └── 05/
│       └── ...
```

### Provider Configuration
```python
# .env
CLOUD_BACKUP_ENABLED=true
CLOUD_BACKUP_PROVIDER=gdrive          # 'gdrive' | 'onedrive' | 'both'

# Google Drive
GDRIVE_SERVICE_ACCOUNT_JSON=path/to/service-account.json
GDRIVE_ROOT_FOLDER_ID=1abc...xyz      # Shared folder ID

# OneDrive
ONEDRIVE_CLIENT_ID=xxx
ONEDRIVE_CLIENT_SECRET=xxx
ONEDRIVE_TENANT_ID=xxx
ONEDRIVE_ROOT_FOLDER_PATH=/5P-SLMS    # Path in OneDrive
```

## Google Drive Setup (Service Account)
1. Create Google Cloud project
2. Enable Google Drive API
3. Create Service Account → download JSON key
4. Create shared folder in Google Drive
5. Share folder with service account email (xxx@xxx.iam.gserviceaccount.com)
6. Set `GDRIVE_ROOT_FOLDER_ID` in .env

## OneDrive Setup (App Registration)
1. Register app in Azure AD (portal.azure.com)
2. Add Microsoft Graph `Files.ReadWrite.All` application permission
3. Grant admin consent
4. Set client_id, client_secret, tenant_id in .env

## Related Code Files
- **Create:** `backend/app/services/cloud-backup-gdrive-service.py` — Google Drive upload/folder
- **Create:** `backend/app/services/cloud-backup-onedrive-service.py` — OneDrive upload/folder
- **Create:** `backend/app/services/cloud-backup-orchestrator.py` — Queue + retry logic
- **Create:** `backend/app/api/cloud-backup-admin-endpoints.py` — Manual retry, status check
- **Modify:** `backend/app/core/config.py` — Cloud backup env vars
- **Modify:** `backend/main.py` — Register admin endpoints

## Implementation Steps

1. **Add config vars** to `config.py`:
   - `CLOUD_BACKUP_ENABLED`, `CLOUD_BACKUP_PROVIDER`
   - Google Drive: `GDRIVE_SERVICE_ACCOUNT_JSON`, `GDRIVE_ROOT_FOLDER_ID`
   - OneDrive: `ONEDRIVE_CLIENT_ID`, `ONEDRIVE_CLIENT_SECRET`, `ONEDRIVE_TENANT_ID`

2. **Create `cloud-backup-gdrive-service.py`**:
   - `ensure_folder_path(year, month, customer, job_no)` → create nested folders
   - `upload_file(folder_id, filename, file_bytes, mime_type)` → return file URL
   - Uses `google-api-python-client` + `google-auth`

3. **Create `cloud-backup-onedrive-service.py`**:
   - `get_access_token()` → client credentials flow
   - `ensure_folder_path(path)` → create nested folders
   - `upload_file(folder_path, filename, file_bytes)` → return share URL
   - Uses `httpx` + Microsoft Graph API

4. **Create `cloud-backup-orchestrator.py`**:
   - `sync_document(document_id)` — main sync function
   - Download from Telegram → build path → upload to cloud → update DB
   - `retry_failed_syncs()` — query failed documents → retry
   - Background task execution (FastAPI BackgroundTasks)

5. **Create `cloud-backup-admin-endpoints.py`**:
   ```
   GET  /api/admin/cloud-backup/status    # Sync stats (pending/synced/failed counts)
   POST /api/admin/cloud-backup/retry     # Retry all failed syncs
   POST /api/admin/cloud-backup/sync/{id} # Retry single document
   ```

6. **Integrate with Phase 1**: After Telegram capture → call `sync_document()` as background task

## Todo List
- [ ] Add cloud backup config vars
- [ ] Create Google Drive service module
- [ ] Create OneDrive service module
- [ ] Create backup orchestrator (queue + retry)
- [ ] Create admin endpoints (status, retry)
- [ ] Integrate with Telegram webhook (background task)
- [ ] Test GDrive sync end-to-end
- [ ] Test OneDrive sync end-to-end

## Success Criteria
- File captured via Telegram → auto-appears in Google Drive/OneDrive within 30s
- Correct folder structure (year/month/customer/job)
- Failed syncs tracked in DB → manual retry works
- Admin can see sync status dashboard
- Disabling backup (env var) → no errors, documents still captured normally

## Risk Assessment
- **Google Drive API quotas**: 12,000 requests/min → more than enough
- **OneDrive Graph API limits**: 10,000 requests/10min → sufficient
- **Large files**: 20MB (Telegram limit) → both Drive APIs handle easily
- **Service account key security**: JSON key must be in .env or secret manager, not committed
- **Network failures**: Retry logic with exponential backoff handles transient errors

## Security Considerations
- Service account keys stored as env vars only
- Cloud folders should have restricted sharing (only team members)
- OneDrive: app-only permission, no user impersonation
- No sensitive file content logged, only metadata
