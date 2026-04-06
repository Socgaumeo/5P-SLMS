# Phase 4 — Document UI — Job Detail Tab + Management Page

## Context Links
- [Phase 2 — Document API](phase-02-document-api-endpoints.md)
- [App.jsx — JobDetailModal](../../frontend/src/App.jsx) (line 338)
- [AdminPanel tabs pattern](../../frontend/src/components/admin/AdminPanel.jsx)
- [auth-fetch utility](../../frontend/src/utils/auth-fetch.js)

## Overview
- **Priority:** High
- **Status:** Pending
- **Description:** (A) "Chứng từ" tab in JobDetailModal, (B) standalone Document Management page for kế toán

## Key Insights
- `JobDetailModal` at `App.jsx:338` — already has tabs, add new "Chứng từ" tab
- Frontend: React 19 + Vite, plain JSX, no TypeScript, `activeNav` state routing
- Upload via web UI = fallback (primary is Telegram bot auto-capture)
- Download = call `/api/documents/{id}/download` → blob → save file

## Requirements

### Part A: Job Detail "Chứng từ" Tab
- Document list for current job (from Telegram auto-capture + manual uploads)
- Web upload button (fallback for manual upload)
- Doc type badge (AN=blue, DEBIT=green, DO=orange, etc.)
- Download + delete buttons per document
- Show source icon (Telegram/Web/Cloud)

### Part B: Document Management Page (kế toán)
- NavItem "Chứng từ" in sidebar
- Filter bar: month, customer, doc_type
- Table: Job No | Customer | Type | File | Source | Uploaded By | Date | Actions
- Batch download (selected → ZIP)
- Summary: document count per type

## Related Code Files
- **Modify:** `frontend/src/App.jsx` — Add tab in JobDetailModal + NavItem + page routing
- **Create:** `frontend/src/components/documents/document-upload-zone.jsx`
- **Create:** `frontend/src/components/documents/document-list-table.jsx`
- **Create:** `frontend/src/components/documents/document-management-page.jsx`
- **Modify:** `frontend/src/App.css` — Document styles

## Implementation Steps

1. Create `document-upload-zone.jsx` — drag & drop + file picker + doc_type select
2. Create `document-list-table.jsx` — table with download/delete, source badge
3. Add "Chứng từ" tab in `JobDetailModal` (App.jsx)
4. Create `document-management-page.jsx` — filters + table + batch download
5. Add NavItem + routing in App.jsx
6. Add CSS styles

## Todo List
- [ ] Create document-upload-zone.jsx
- [ ] Create document-list-table.jsx
- [ ] Add tab in JobDetailModal
- [ ] Create document-management-page.jsx
- [ ] Add NavItem + routing
- [ ] Add CSS styles

## Success Criteria
- Documents from Telegram auto-capture show in job detail tab
- Manual upload works as fallback
- Kế toán can filter/search/batch download from management page
- Source badges distinguish Telegram vs Web vs Cloud uploads
