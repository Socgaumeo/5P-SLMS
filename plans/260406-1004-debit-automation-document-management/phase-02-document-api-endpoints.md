# Phase 2 — Document API (Telegram Download + Web Upload + List/Delete)

## Context Links
- [Phase 1 — DB & Telegram Bot](phase-01-database-and-telegram-bot-setup.md)
- [Existing upload pattern](../../backend/app/api/rate_file_upload.py)
- [Auth middleware](../../backend/app/api/dependencies.py)

## Overview
- **Priority:** High
- **Status:** Pending
- **Description:** REST API for documents: list, download (via Telegram API), web upload fallback, delete, batch ZIP

## Key Insights
- Download = call Telegram `getFile` API → get file bytes → stream to browser
- Web upload = accept multipart form → send file to bot's private chat → save file_id
- List = query `documents` table with filters
- Batch download = download multiple files → zip → stream

## Requirements

### Functional
- List documents by job_id, customer, month, doc_type
- Download single file (Telegram file_id → getFile → stream)
- Web upload fallback (multipart form → Telegram API → file_id)
- Delete document (admin or uploader)
- Batch download as ZIP

### Non-functional
- Download latency: ~1-3s (Telegram API round-trip)
- Max batch ZIP: 50 files
- Auth required for all endpoints

## Endpoints

```
GET    /api/documents                     # List (filter: job_id, customer_id, month, doc_type)
GET    /api/documents/{id}/download       # Download via Telegram getFile → stream
POST   /api/documents/upload              # Web upload fallback (multipart form)
DELETE /api/documents/{id}                # Delete (admin or uploader)
POST   /api/documents/batch-download      # Multiple files → ZIP stream
GET    /api/documents/stats               # Summary: count per doc_type, per month
```

## Architecture

### Download Flow
```
Browser request → GET /api/documents/{id}/download
  → Query DB for telegram_file_id
  → If telegram: call Telegram getFile API → get file_path
    → Download bytes from https://api.telegram.org/file/bot{token}/{file_path}
    → StreamingResponse with Content-Disposition
  → If external_url: redirect to URL
```

### Web Upload Flow (fallback for kế toán or admin)
```
Browser → POST /api/documents/upload (multipart: file + job_id + doc_type)
  → Validate file type/size
  → Send file to Telegram Bot API (sendDocument to a private storage chat)
  → Get file_id from response
  → Insert into documents table (storage_type='web_upload', telegram_file_id=...)
  → Return document metadata
```

## Related Code Files
- **Create:** `backend/app/api/document-crud-endpoints.py`
- **Modify:** `backend/main.py` — Register router
- **Depends on:** `backend/app/services/telegram-file-downloader.py` (Phase 1)

## Implementation Steps

1. Create `backend/app/api/document-crud-endpoints.py`:
2. `GET /api/documents` — list with filters (job_id, customer_id via job join, month, doc_type, pagination)
3. `GET /api/documents/{id}/download` — fetch file_id → Telegram getFile → stream bytes
4. `POST /api/documents/upload` — multipart form, send to Telegram storage chat, save file_id
5. `DELETE /api/documents/{id}` — permission check, delete DB record (file stays on Telegram — no cost)
6. `POST /api/documents/batch-download` — accept list of IDs, download each, create ZIP in memory, stream
7. `GET /api/documents/stats` — aggregate counts by doc_type and month
8. Register router in `main.py`

## Todo List
- [ ] Create document-crud-endpoints.py
- [ ] Implement list endpoint with filters + pagination
- [ ] Implement download via Telegram getFile
- [ ] Implement web upload fallback
- [ ] Implement delete with permissions
- [ ] Implement batch ZIP download
- [ ] Implement stats endpoint
- [ ] Register router in main.py

## Success Criteria
- List returns correct documents with filters
- Download streams correct file with proper filename/content-type
- Web upload saves file_id and DB record
- Delete works with permission check
- Batch ZIP contains all requested files

## Risk Assessment
- **Telegram download speed**: ~1-3s per file. Batch of 50 files could take 2+ min → use streaming ZIP
- **Telegram file_id from web upload**: Need a "storage chat" (private channel) for the bot to send files to
- **Large files**: 20MB Telegram limit. Reject > 20MB in web upload
