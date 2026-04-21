# Phase 8 — Frontend UX Polish + Admin Config UI

## Context links
- [plan.md](plan.md)
- Existing: `frontend/src/components/SearchBox.jsx`, `frontend/src/components/admin/AdminPanel.jsx`

## Overview
- Priority: Low-Medium
- Status: Pending
- Brief: Polish customer-export panel UX + add admin UI to manage customer template registry without code edits.

## UX issues to fix

| Issue | Fix |
|---|---|
| Buttons có icon emoji nhỏ, label dài cắt | Tooltip cho long labels, icon size +2pt |
| Date range pre-fills empty | Default to current month start/end |
| Service-type filter list dài | Group by family (Trucking / Customs / Sea / Air / Warehouse) |
| Loading state khi xuất xuất hiện chậm | Skeleton on button, progress bar |
| File download tên không chuẩn | `{CUSTOMER}_{TEMPLATE}_{YYYYMM}.xlsx` |
| Khi 0 jobs: hiện "Không có job" lờ mờ | Banner explaining gap (date range? service type? data import?) |
| Không thấy error backend | Toast với chi tiết error |

## Admin Config UI (new)

### Page: `/admin/customer-export-templates`
**Permission**: ADMIN role only.

**CRUD operations**:
- List all customers in registry + their template families
- Add new customer → auto-detect customer code from `customers` table
- Pick family (trucking/handling/customs/international)
- Set per-customer overrides (sheet name, title, VAT, options)
- Disable/enable templates

**Backend endpoints needed**:
- `GET /api/admin/customer-templates` — list
- `POST /api/admin/customer-templates` — create
- `PUT /api/admin/customer-templates/{code}` — update
- `DELETE /api/admin/customer-templates/{code}` — disable

### Storage decision
- **Option A**: Keep registry in `customer_export_template_registry.py` Python file (current). Simple but requires deploy to add customer.
- **Option B**: Move to DB table `customer_template_configs`. Allows runtime add via UI without deploy.

**Recommend Option B** for true admin self-service.

## Files to create / modify

**Modify**:
- `frontend/src/components/SearchBox.jsx` — UX polish
- `frontend/src/components/SearchBox.css` — visual polish

**Create**:
- `backend/migrations/add_customer_template_configs_table.sql`
- `backend/app/api/admin.py` — add CRUD endpoints
- `frontend/src/pages/admin/CustomerTemplatesPage.jsx`
- `frontend/src/components/admin/CustomerTemplateForm.jsx`

## Implementation steps

1. UX polish (1-2 hours).
2. Decide A vs B for storage.
3. If B: create DB table + migration + API CRUD.
4. Build admin frontend page.
5. Migrate existing registry entries to DB.
6. Update `customer_export_template_registry.py` to read from DB (with file fallback).

## Todo list

- [ ] UX polish SearchBox
- [ ] Decide storage A vs B
- [ ] If B: create migration + CRUD endpoints
- [ ] Build admin page
- [ ] Migrate existing entries
- [ ] Test admin can add customer without code change

## Success criteria
- Admin can register new customer in 30 seconds via UI (no Python edit + deploy).
- UX feels polished (no rough edges).

## Risk assessment
- **Risk**: Schema migration on production requires planning. Mitigation: backward-compatible (file fallback).
- **Risk**: Admin UI without RBAC can break things. Mitigation: ADMIN role required + audit log.

## Next steps
After Phase 8 → Phase 9 (E2E testing + rollout).
