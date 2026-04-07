# Phase 1 — Database Schema + Telegram Bot Setup

## Context Links
- [Supabase client](../../backend/app/db/supabase_client.py)
- [Existing schema](../../SQL/module1_foundation.sql)
- [vendors table has telegram_chat_id](../../SQL/init.sql)

## Overview
- **Priority:** Critical (blocker for all other phases)
- **Status:** Pending
- **Description:** Create `documents` table + setup Telegram Bot for auto-capture chứng từ

## Key Insights
- `vendors` table already has `telegram_chat_id` → Telegram đã được dùng trong hệ thống
- `n8n_workflows` directory exists → team đã dùng n8n automation
- Telegram Bot API: free, file lưu vĩnh viễn, getFile API để download khi cần
- Bot có thể add vào group chat hiện tại → CS không đổi workflow

## Requirements

### Functional
- `documents` table lưu metadata + `telegram_file_id` + `external_url`
- Telegram Bot nhận file + caption → auto-extract job_no → insert vào DB
- Bot reply confirm khi nhận thành công
- Bot hỏi lại nếu thiếu job_no hoặc doc_type
- Hỗ trợ cả upload qua web UI (fallback)

### Non-functional
- Bot respond < 3s
- Hỗ trợ file types: PDF, Excel, Word, images (PNG/JPG)
- Max 20MB/file (Telegram limit)
- Bot token lưu trong env var, không hardcode

## Architecture

### Documents Table

```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id INTEGER REFERENCES jobs(job_id) ON DELETE CASCADE,
  doc_type TEXT NOT NULL CHECK (doc_type IN (
    'AN', 'DEBIT', 'DO', 'CD', 'CO', 'INVOICE', 'AWB', 'BL', 'PACKING_LIST', 'OTHER'
  )),
  file_name TEXT NOT NULL,
  file_size INTEGER,
  mime_type TEXT,

  -- Multi-tier storage
  storage_type TEXT NOT NULL DEFAULT 'telegram'
    CHECK (storage_type IN ('telegram', 'gdrive', 'onedrive', 'web_upload', 'external_link')),
  telegram_file_id TEXT,            -- Telegram Bot API file_id (primary)
  telegram_message_id INTEGER,      -- trace lại message gốc
  telegram_chat_id TEXT,            -- group/chat nào gửi
  external_url TEXT,                -- Google Drive / OneDrive / manual link
  cloud_backup_path TEXT,           -- path trên cloud backup (nếu đã sync)
  cloud_backup_status TEXT DEFAULT 'pending'
    CHECK (cloud_backup_status IN ('pending', 'synced', 'failed', 'skipped')),

  -- Audit
  uploaded_by INTEGER REFERENCES users(user_id),
  uploaded_by_telegram TEXT,        -- telegram username (nếu upload qua bot)
  uploaded_at TIMESTAMPTZ DEFAULT NOW(),
  notes TEXT,
  metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_documents_job_id ON documents(job_id);
CREATE INDEX idx_documents_doc_type ON documents(doc_type);
CREATE INDEX idx_documents_uploaded_at ON documents(uploaded_at DESC);
CREATE INDEX idx_documents_storage_type ON documents(storage_type);
CREATE INDEX idx_documents_cloud_backup_status ON documents(cloud_backup_status);
```

### Telegram Bot Architecture

```
Telegram Group (CS gửi file)
  │
  ▼
Telegram Bot (@5pslms_bot)
  │  webhook: POST /api/telegram/webhook
  ▼
FastAPI Endpoint
  ├─ Parse caption → extract job_no (regex: LG\d{4}/\d{3} hoặc TRK-\d{4}-\d{4})
  ├─ Extract doc_type từ caption keyword hoặc filename
  ├─ Validate job_no exists in DB
  ├─ Insert document metadata vào DB (với telegram_file_id)
  ├─ Queue cloud backup (Phase 3)
  └─ Reply confirm message qua Telegram
```

### Caption Parsing Rules

```
Input examples:
  "LG2604/001 AN"          → job_no=LG2604/001, doc_type=AN
  "TRK-1903-0004 debit"    → job_no=TRK-1903-0004, doc_type=DEBIT
  "#LG2604001 DO"           → job_no=LG2604/001, doc_type=DO
  "hoa don LG2604/001"      → job_no=LG2604/001, doc_type=INVOICE
  [no caption, just file]   → Bot hỏi: "Job nào? Loại chứng từ gì?"

Keywords → doc_type mapping:
  AN, arrival notice     → AN
  debit, debit note      → DEBIT
  DO, delivery order     → DO
  CD, customs dec        → CD
  CO, certificate        → CO
  invoice, hóa đơn       → INVOICE
  AWB, air waybill       → AWB
  BL, bill of lading     → BL
  packing list           → PACKING_LIST
```

### Bot Commands

```
/start          — Welcome + hướng dẫn sử dụng
/help           — Hướng dẫn format caption
/search LG2604  — Tìm documents theo job_no
/status         — Thống kê documents tháng hiện tại
```

## Related Code Files
- **Create:** `SQL/documents-table-migration.sql`
- **Create:** `backend/app/api/telegram-webhook-handler.py` — Webhook endpoint
- **Create:** `backend/app/services/telegram-bot-service.py` — Bot logic (parse, validate, reply)
- **Create:** `backend/app/services/telegram-file-downloader.py` — Download file from Telegram API
- **Modify:** `backend/main.py` — Register webhook router
- **Modify:** `backend/app/core/config.py` — Add TELEGRAM_BOT_TOKEN env var

## Implementation Steps

1. **Create Telegram Bot** via @BotFather → get token
2. **Write SQL migration** `documents-table-migration.sql`
3. **Run migration** on Supabase
4. **Add config** — `TELEGRAM_BOT_TOKEN` to `config.py` Settings class
5. **Create `telegram-bot-service.py`**:
   - `parse_caption(text)` → extract job_no + doc_type
   - `validate_job(job_no)` → check exists in DB, return job_id
   - `detect_doc_type(caption, filename)` → infer doc_type from keywords
   - `send_reply(chat_id, message)` → reply via Telegram API
6. **Create `telegram-webhook-handler.py`**:
   - `POST /api/telegram/webhook` — receive Telegram updates
   - Handle document/photo messages → extract file_id, caption
   - Call bot service → insert document record
   - Reply with confirmation or ask for missing info
7. **Create `telegram-file-downloader.py`**:
   - `download_file(file_id)` → call Telegram getFile API → return bytes
   - Used by Document API (Phase 2) when kế toán downloads
8. **Register webhook** with Telegram API (setWebhook)
9. **Register router** in `main.py`

## Todo List
- [ ] Create Telegram Bot via @BotFather
- [ ] Write + run SQL migration
- [ ] Add TELEGRAM_BOT_TOKEN to config
- [ ] Create telegram-bot-service.py (parse + validate)
- [ ] Create telegram-webhook-handler.py (FastAPI endpoint)
- [ ] Create telegram-file-downloader.py
- [ ] Register webhook URL with Telegram
- [ ] Test: send file in group → bot captures + inserts DB

## Success Criteria
- Bot nhận file trong group → auto-insert vào documents table
- Caption parse chính xác job_no + doc_type
- Bot reply confirm message < 3s
- Missing info → bot hỏi lại
- file_id lưu đúng trong DB → có thể download lại qua API

## Risk Assessment
- **Bot rate limits**: Telegram allows 30 msg/sec per bot → đủ cho team nhỏ
- **File expiry**: Telegram file_id KHÔNG expire (confirmed by Telegram docs)
- **File size**: 20MB limit → đủ cho PDF/Excel chứng từ, quá lớn → báo lỗi
- **Webhook HTTPS**: Railway có HTTPS → dùng trực tiếp. Nếu dev local → cần ngrok

## Security Considerations
- Webhook endpoint verify `X-Telegram-Bot-Api-Secret-Token` header
- Bot token lưu trong env var only
- Only process messages từ authorized group(s) (whitelist chat_id)
- Không log file content, chỉ log metadata
