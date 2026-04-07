---
title: "Fix bot quotation auth, vendor dropdown, RateFormModal UI, selling rate display"
description: "Fix 4 bugs: bot 401 on quotation create, vendor dropdown blur race, RateFormModal missing fields/categories, selling rate label clarity"
status: complete
priority: P1
effort: 4h
branch: main
tags: [bugfix, ui, backend, bot]
created: 2026-03-03
completed: 2026-03-03
---

# Fix Bot, Vendor Dropdown, RateFormModal & Selling Rate Display

## Overview

4 independent issues affecting quotation workflow:
1. Bot cannot create quotations (401 auth error)
2. Vendor dropdown in job edit fails due to blur/click race
3. RateFormModal missing categories, fields, labels
4. Selling rate display in quotation selector unclear

## Phases

| # | Phase | Status | Effort | Files |
|---|-------|--------|--------|-------|
| 1 | [Bot quotation direct DB insert](./phase-01-fix-bot-quotation-auth-direct-db-insert.md) | ✅ complete | 1h | `backend/app/ai/unified_processor.py` |
| 2 | [Vendor dropdown onMouseDown fix](./phase-02-fix-vendor-dropdown-blur-race-condition.md) | ✅ complete | 15m | `frontend/src/App.jsx` |
| 3 | [RateFormModal UI improvements](./phase-03-rateform-modal-ui-labels-categories-fields.md) | ✅ complete | 2h | `frontend/src/components/admin/RateFormModal.jsx` |
| 4 | [Selling rate quotation display](./phase-04-selling-rate-quotation-display-and-grouping.md) | ✅ complete | 30m | `frontend/src/App.jsx` |

## Dependencies

- Phase 1 independent (backend only)
- Phase 2 independent (frontend only)
- Phase 3 independent (frontend only)
- Phase 4 independent (frontend + backend)
- All 4 can be implemented in parallel

## Key Decisions

- **Phase 1**: Direct Supabase insert instead of HTTP call to admin API. Avoids auth complexity for internal bot operations.
- **Phase 3**: Store `min_charge`/`min_charge_amount` in existing `metadata` JSONB column. No DB migration needed.
- **Phase 4**: Return `service_type_code` from search API (already done), use it in frontend label.
