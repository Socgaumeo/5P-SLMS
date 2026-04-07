# Phase 7 — Testing, Deployment & Integration

## Overview
- **Priority:** Medium
- **Status:** Pending
- **Description:** End-to-end testing, deployment, integration verification

## Testing Scope

### Telegram Bot
- Send file with valid caption → document captured + bot confirms
- Send file without caption → bot asks for job_no
- Send file with invalid job_no → bot reports error
- Multiple files in one message → all captured
- File > 20MB → bot rejects gracefully

### Document API
- List/download/delete cycle
- Web upload fallback
- Batch ZIP download
- Permission check (admin vs staff)

### Cloud Backup
- Telegram capture → auto-sync to Drive
- Correct folder structure
- Failed sync → retry works
- Disable backup → no errors

### Debit Template Engine
- Single generate with correct cell filling
- Batch generate → ZIP
- Currency/date formatting preserved
- Template with merged cells → preserved

### Frontend
- Job detail "Chứng từ" tab
- Document Management page filters + batch download
- Debit template admin CRUD
- Batch export wizard flow

## Deployment Checklist
- [ ] Run SQL migration on Supabase (documents + debit_templates tables)
- [ ] Create Telegram Bot via @BotFather → get token
- [ ] Set TELEGRAM_BOT_TOKEN in Railway env vars
- [ ] Set webhook URL: `https://api.5pvietnam.com/api/telegram/webhook`
- [ ] Add bot to CS Telegram group
- [ ] Setup Google Drive service account (if using GDrive backup)
- [ ] Setup OneDrive app registration (if using OneDrive backup)
- [ ] Set cloud backup env vars in Railway
- [ ] Deploy backend to Railway
- [ ] Deploy frontend to Vercel
- [ ] Verify CORS for new endpoints
- [ ] Test Telegram bot in production group
- [ ] Monitor cloud backup sync status

## Success Criteria
- Full flow: CS sends file in Telegram → captured in DB → visible in web UI → downloadable by kế toán
- Cloud backup: file appears in Drive within 30s
- Debit export: correct Excel files generated
- No errors in production logs
