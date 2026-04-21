# Phase 7 — Vendor Cost Import for Real Margin Computation

## Context links
- [plan.md](plan.md)
- Existing import scripts: `backend/scripts/import-meiko-t3-jobs.py`, `import-debit-binhminh-upgain-pipetree-t3.py`
- Bug context: All 211 cost rows had `buying_amount = selling_amount` (commit 863ec14 fixed code, set buying=0 for new imports)

## Overview
- Priority: High (financial reporting accuracy)
- Status: Pending
- Brief: Build vendor cost import workflow so `job_costs.buying_amount` reflects real vendor invoices. This unlocks accurate profit margin display.

## Key insights
- After commit 863ec14: import scripts now set `buying_rate=0` (placeholder, not duplicate of selling).
- Frontend correctly shows "—" for profit when cost=0 (commit 0f2421b).
- BUT: real margin can't be computed until vendor invoices imported.
- Vendor invoices come from a SEPARATE workflow (vendor side, not customer bảng kê).

## Sources of vendor cost data (chốt 2026-04-21)

3 input methods — tất cả đều triển khai:

| Source | Format | Priority |
|---|---|---|
| **Manual entry via UI** | Form per cost line | 1 (phổ biến nhất — nhân viên nhập tay) |
| **Upload file invoice** | PDF / Excel upload | 2 (batch entry, AI parse to extract amounts) |
| **Paste URL link** | HTTP(S) link tới invoice online | 3 (reference-only, lưu link vào `job_costs.invoice_url`) |

## Requirements

### Functional
- Import vendor invoices → populate `job_costs.buying_amount` for matching `(job_id, svc_id, cost_name)`.
- Match strategy: cost_name fuzzy match + svc_id/job_id exact.
- UI form for manual cost entry per service.
- Backfill historical jobs (T3 has 506 cost rows with buying=0, T4 has 2 rows).

### Non-functional
- Idempotent imports (no duplicate cost insertion).
- Audit log of cost changes (who/when/old vs new).

## Architecture

```
4 entry points for buying_amount:

A. Manual entry (UI) — PRIMARY
   frontend/src/components/JobCostEditor.jsx (NEW)
     → opens for a service
     → user enters per-line buying_amount + vendor_id + invoice_no
     → POST /api/jobs/services/{svc_id}/costs/{cost_id}/buying
     → backend updates job_costs.buying_rate

B. File upload (PDF/Excel invoice)
   frontend/src/components/VendorInvoiceUpload.jsx (NEW)
     → drag-drop invoice file
     → backend uploads to storage
     → Parse pipeline (REUSE existing):
         - Excel (.xlsx/.xls) → openpyxl + custom Excel parser script (đã có cho import scripts)
         - PDF / image / free-text Telegram forward → Claude Sonnet API (đã tích hợp qua telegram-webhook-handler + AI pipeline)
     → AI suggests cost-line mapping + amounts
     → user reviews + confirms → writes to job_costs

C. URL link reference
   job_costs.invoice_url column (NEW schema add)
     → user pastes link to online invoice (Drive, Onedrive, vendor portal)
     → stored as reference; buying_amount still entered via A

D. Bulk import script (per-vendor)
   backend/scripts/import-vendor-invoices-{VENDOR}.py
     → reads vendor's invoice format
     → matches to job_services by svc_id / invoice_no
     → UPDATE job_costs SET buying_amount = ... WHERE ...

E. Quotation-driven (existing)
   _sync_quotation_to_job_costs already supports buying via ServiceQuotationRequest.
```

## Files to create

- `backend/migrations/add_invoice_url_and_upload_fields_to_job_costs.sql` — schema add (invoice_url, invoice_file_id, vendor_id if missing)
- `backend/migrations/create_job_costs_audit_table_and_trigger.sql` — audit Level 2
- `backend/app/api/jobs.py` — add PATCH endpoint for cost.buying + invoice_url + GET history
- `backend/app/api/vendor_invoices.py` (NEW) — upload + parse endpoints
- `backend/scripts/import-vendor-invoices-template.py` — per-vendor parser starter
- `frontend/src/components/JobCostEditor.jsx` — manual entry form + history drawer
- `frontend/src/components/VendorInvoiceUpload.jsx` — drag-drop file upload
- `frontend/src/components/JobCostHistoryDrawer.jsx` — display audit trail per cost line

## Implementation steps

1. Survey existing vendor invoices — what format? Where are they?
2. Build template import script for 1 vendor (proof-of-concept).
3. Add PATCH endpoint for manual buying_amount update.
4. Build JobCostEditor frontend modal.
5. Test: open job → edit costs → enter buying for 1 line → save → verify profit shows correctly.
6. Bulk backfill if vendor data available.

## Todo list

- [ ] Survey vendor invoice sources (where stored, what format)
- [ ] Decide priority: bulk import vs manual UI entry
- [ ] Build PATCH endpoint for cost.buying
- [ ] Build JobCostEditor UI
- [ ] Test E2E with 1 sample
- [ ] Document vendor cost workflow

## Success criteria
- ≥1 vendor's invoices imported → buying_amount populated.
- Manual cost entry UI works.
- Profit column in SearchBox panel shows real numbers (not "—") for jobs with imported vendor data.

## Risk assessment
- **Risk**: vendor file formats vary widely. Mitigation: per-vendor parser modules.
- **Risk**: Cost name fuzzy matching false positives. Mitigation: require svc_id exact match.
- **Risk**: Manual entry slow for high-volume customers. Mitigation: bulk paste mode in UI.

## Resolved (2026-04-21)

- ✅ 3 input methods đều triển khai: manual form / file upload / URL link.
- ✅ Parse engine **tái sử dụng pipeline hiện có**: Excel → openpyxl + excel_parser; PDF/text/Telegram → Claude Sonnet (đã tích hợp qua telegram-webhook-handler).
- ✅ **Audit trail Level 2 — Full audit table**:
  - Tạo bảng `job_costs_audit` (audit_id, cost_id, job_id, svc_id, action [INSERT/UPDATE/DELETE], old_value JSONB, new_value JSONB, changed_by user_id, changed_at timestamp, reason text nullable)
  - Trigger: mỗi INSERT/UPDATE/DELETE trên `job_costs` tự động append 1 row audit.
  - API endpoint `GET /api/jobs/costs/{cost_id}/history` trả history để UI hiển thị khi cần.
  - UI: icon clock bên cạnh mỗi cost line → click mở drawer xem history.

## Open questions

- Vendor portal integration (future) — có vendor nào có API không?
