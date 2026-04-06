# Debit Automation & Document Management — Implementation Plan

**Branch:** `claude/laughing-zhukovsky`
**Created:** 2026-04-06
**Updated:** 2026-04-06 (v2 — Telegram Bot + Cloud Backup)
**Status:** Draft

## Overview

Nâng cấp 5P SLMS với 3 module chính:
1. **Document Auto-Capture** — Telegram Bot tự nhận chứng từ từ CS, auto-map vào jobs
2. **Cloud Backup** — Sync file lên OneDrive/Google Drive làm backup
3. **Debit Note Template Engine** — Tự động hóa xuất debit note từ Excel templates

## Storage Strategy (Multi-tier)

```
┌─────────────┐     ┌──────────────┐     ┌───────────────────┐
│  PRIMARY     │     │  METADATA    │     │  BACKUP           │
│  Telegram    │     │  Supabase DB │     │  OneDrive/GDrive  │
│  file_id     │◄───►│  documents   │────►│  auto-sync        │
│  (free,      │     │  table       │     │  (optional)       │
│   permanent) │     │              │     │                   │
└─────────────┘     └──────────────┘     └───────────────────┘
```

- **Primary**: Telegram Bot API file_id (free, permanent, ≤20MB/file)
- **Metadata**: `documents` table in Supabase PostgreSQL
- **Backup**: OneDrive/Google Drive via API (configurable, optional)
- **Fallback**: Manual upload qua web UI → cũng lưu Telegram file_id hoặc external_url

## Phases

| # | Phase | Status | File |
|---|-------|--------|------|
| 1 | DB Schema + Telegram Bot Setup | Pending | [phase-01](phase-01-database-and-telegram-bot-setup.md) |
| 2 | Document API (Telegram Download + Web Upload) | Pending | [phase-02](phase-02-document-api-endpoints.md) |
| 3 | Cloud Backup (OneDrive / Google Drive) | Pending | [phase-03](phase-03-cloud-backup-sync-onedrive-gdrive.md) |
| 4 | Document UI — Job Detail Tab + Management Page | Pending | [phase-04](phase-04-document-ui-job-detail-tab-and-management-page.md) |
| 5 | Debit Template Engine — Backend | Pending | [phase-05](phase-05-debit-template-engine-backend.md) |
| 6 | Debit Template UI — Admin + Batch Export | Pending | [phase-06](phase-06-debit-template-ui-admin-and-batch-export-page.md) |
| 7 | Testing, Deployment & Integration | Pending | [phase-07](phase-07-testing-deployment-and-integration.md) |

## Key Dependencies

- Telegram Bot Token (create via @BotFather)
- `python-telegram-bot` or raw HTTP API
- `openpyxl` already in backend requirements
- OneDrive: Microsoft Graph API + OAuth2 app registration
- Google Drive: Service Account + Drive API

## Architecture Decisions

1. **Primary Storage**: Telegram file_id — $0, permanent, CS không đổi workflow
2. **Backup Storage**: OneDrive/Google Drive — configurable, auto-sync sau khi capture
3. **Template Storage**: Debit templates lưu trên Telegram (admin upload qua bot) hoặc server disk
4. **Template Engine**: openpyxl load_workbook → fill cells → FileResponse
5. **Frontend**: React+Vite SPA, plain JSX — no Next.js
6. **Auth**: Reuse JWT middleware (`get_current_user`)
7. **DB**: Supabase client (not raw psycopg2) for new endpoints
