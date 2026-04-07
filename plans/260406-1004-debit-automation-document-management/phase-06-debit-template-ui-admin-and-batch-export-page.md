# Phase 6 — Debit Template UI — Admin + Batch Export Page

## Context Links
- [Phase 5 — Template Engine Backend](phase-05-debit-template-engine-backend.md)
- [AdminPanel tabs](../../frontend/src/components/admin/AdminPanel.jsx)

## Overview
- **Priority:** Medium
- **Status:** Pending
- **Description:** Admin UI for template management + batch export wizard page

## Requirements

### Part A: Template Management (Admin tab)
- New "Debit Templates" tab in AdminPanel
- List, create, edit, delete templates
- Field mapping: JSON textarea (v1), visual editor (v2 future)

### Part B: Batch Export Page
- NavItem "Xuất Debit" in sidebar
- Wizard: select month → customer → template → preview jobs → generate ZIP
- Progress indicator during generation

## Related Code Files
- **Modify:** `frontend/src/components/admin/AdminPanel.jsx` — Add tab
- **Create:** `frontend/src/components/admin/debit-template-manager-panel.jsx`
- **Create:** `frontend/src/components/debit/debit-batch-export-wizard-page.jsx`
- **Create:** `frontend/src/components/debit/debit-job-preview-table.jsx`
- **Modify:** `frontend/src/App.jsx` — NavItem + routing
- **Modify:** `frontend/src/App.css` — Styles

## Implementation Steps

1. Create `debit-template-manager-panel.jsx` — CRUD list + modal form
2. Add tab in AdminPanel: "Debit Templates"
3. Create `debit-batch-export-wizard-page.jsx` — step wizard
4. Create `debit-job-preview-table.jsx` — preview jobs before generation
5. Add NavItem + routing in App.jsx
6. Add CSS styles

## Todo List
- [ ] Create debit-template-manager-panel.jsx
- [ ] Add tab in AdminPanel
- [ ] Create debit-batch-export-wizard-page.jsx
- [ ] Create debit-job-preview-table.jsx
- [ ] Add NavItem + routing
- [ ] Add CSS styles

## Success Criteria
- Admin manages templates from AdminPanel
- Batch export wizard → select → preview → generate → download ZIP
- UI matches existing app style
