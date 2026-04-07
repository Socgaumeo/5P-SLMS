# Session 1 Handoff — Debit Automation & Document Management

**Date:** 2026-04-06
**Branch:** `claude/laughing-zhukovsky`
**Commits:** 7 commits pushed

## Completed

### Phase 1 — DB + Telegram Bot ✅
- `documents` + `debit_templates` tables created in Supabase
- Telegram bot `@slmsdoc_bot` configured, webhook set
- Group "5P Documents" (chat_id: `-5106803771`) created, bot added
- Privacy mode OFF, `can_read_all_group_messages: true`
- Files: `telegram-bot-service.py`, `telegram-file-downloader.py`, `telegram-webhook-handler.py`
- **Note:** Webhook currently pointing to Railway production but code not deployed yet. For local test: delete webhook + use polling.

### Phase 2 — Document CRUD API ✅
- `document-crud-endpoints.py`: list, download (via Telegram getFile), web upload, delete, batch ZIP, stats
- Auth required for all endpoints

### Phase 4 — Document UI ✅
- `document-upload-zone.jsx`: drag & drop + doc_type selector
- `document-list-table-with-download-delete.jsx`: table with type badges
- `document-management-page-with-filters.jsx`: month/customer/type filters + batch ZIP
- NavItem "Chứng từ" in sidebar
- Job detail modal has "📄 Chứng từ" section

### Phase 5+6 — Debit Template Engine + UI ✅ (partially working)
- `debit-note-generator-service.py`: load template → fill cells → export
- `debit-template-and-generation-endpoints.py`: CRUD + generate + batch-generate
- `debit-batch-export-wizard-page.jsx`: date range picker, customer, template selector
- `debit-template-manager-admin-panel.jsx`: CRUD in AdminPanel tab
- NavItem "Xuất Debit" in sidebar

### Fixes Applied
- Customer dropdown: API returns `{customers: [...]}` not `{data: [...]}`
- White screen crash: stale `month` variable removed (replaced with `dateFrom`/`dateTo`)
- MergedCell: skip merged cells when writing
- Column-based fill: rewrote `fill_template` for DAINESE table format
- Template paths: fixed to absolute paths for local testing

## Remaining Work (Session 2)

### 1. Clean DAINESE Templates (HIGH)
All 5 templates contain old data that must be cleaned:
- `DAINESE_CO_template.xlsx` — Sheet "DỊCH VỤ", data rows 15-16
- `DAINESE_NHAP_SEA_AIR_template.xlsx` — Sheet "NHẬP", data rows 13-28 (26 columns!)
- `DAINESE_XUAT_template.xlsx` — Sheet "XUẤT", data rows similar
- `DAINESE_TC_NHAP_CPN_template.xlsx` — Sheet "tc, cpn", data rows
- `DAINESE_VAN_CHUYEN_template.xlsx` — Sheet "HĐ" rows 15-25, Sheet "PurchPurchaseOrder" has cross-ref formulas

### 2. Update Field Mappings (HIGH)
Current mappings need updating for actual column structure:
- **NHẬP Sea/Air**: 26+ columns (K-V = phí dịch vụ, W-Z = phí trả hộ)
- **CO**: columns A-M + formula H=F*G
- **Vận chuyển**: HĐ sheet ↔ PurchPurchaseOrder cross-sheet formulas
- Each row needs formulas (e.g., `V=SUM(K:U)`, `Z=SUM(W:Y)`)

### 3. Generator V2 Improvements (HIGH)
- Copy formulas from template reference row and adjust row numbers
- Handle cross-sheet references (HĐ → PurchPurchaseOrder)
- Insert rows dynamically (shift totals row down)
- Preserve all cell formatting, merged cells, borders

### 4. Filter by scheduled_date (MEDIUM)
- Change `jobs-for-export` endpoint to filter by `job_services.scheduled_date` instead of `jobs.created_at`
- Frontend already sends date range

### 5. Phase 3 — Cloud Backup (DEFERRED)
- Google Drive / OneDrive sync after Telegram capture
- Not blocking, can implement later

### 6. Deploy to Production
- Create PR from `claude/laughing-zhukovsky` → `main`
- Set `TELEGRAM_DOC_BOT_TOKEN` in Railway env (already done)
- Set webhook URL after deploy

## Key Files

```
Backend:
  backend/app/core/config.py                              (modified: +Telegram config)
  backend/app/services/telegram-bot-service.py             (NEW)
  backend/app/services/telegram-file-downloader.py         (NEW)
  backend/app/services/debit-note-generator-service.py     (NEW — needs v2 rewrite)
  backend/app/api/telegram-webhook-handler.py              (NEW)
  backend/app/api/document-crud-endpoints.py               (NEW)
  backend/app/api/debit-template-and-generation-endpoints.py (NEW)
  backend/main.py                                          (modified: +3 routers)

Frontend:
  frontend/src/components/documents/document-upload-zone.jsx
  frontend/src/components/documents/document-list-table-with-download-delete.jsx
  frontend/src/components/documents/document-management-page-with-filters.jsx
  frontend/src/components/debit/debit-batch-export-wizard-page.jsx
  frontend/src/components/debit/debit-template-manager-admin-panel.jsx
  frontend/src/App.jsx  (modified: +imports, +NavItems, +page routing)
  frontend/src/App.css  (modified: +document/debit styles)

SQL:
  SQL/migrations/003_documents_and_debit_templates.sql

Templates:
  stored_files/templates/DAINESE/*.xlsx (5 files — need cleaning)
```

## Credentials (from .env)
- Supabase URL: `https://ooixntyflwmjaryxwakx.supabase.co`
- Telegram Bot Token: `8654310178:AAEEA6vfgkIQVM6MV7kx-E6gsAasjMltHV0`
- Telegram Group: `-5106803771` ("5P Documents")
- DAINESE customer_id: `46`

## Local Dev
- Backend: `cd backend && python3 -m uvicorn main:app --port 8000`
- Frontend: `cd frontend && npm run dev -- --port 5173`
- Need `.env` copied to worktree root
