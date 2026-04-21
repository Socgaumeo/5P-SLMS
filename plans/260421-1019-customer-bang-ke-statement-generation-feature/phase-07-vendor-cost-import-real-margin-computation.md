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

## Sources of vendor cost data

| Source | Format | Status |
|---|---|---|
| Vendor invoices PDF/Excel | Per-vendor format | Need import script |
| Vendor portal exports | Varies | Need API integration if exists |
| Manual entry via UI | Form-based | Need form |

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
3 entry points for buying_amount:

A. Bulk import (vendor invoice → DB)
   backend/scripts/import-vendor-invoices.py
     → reads vendor's invoice file
     → matches to job_services by svc_id or invoice number
     → UPDATE job_costs SET buying_amount = ... WHERE ...

B. Manual entry (UI)
   frontend/src/components/JobCostEditor.jsx (NEW)
     → opens for a service
     → user enters per-line buying_amount
     → POST /api/jobs/services/{svc_id}/costs/{cost_id}/buying
     → backend updates job_costs.buying_rate

C. Quotation-driven (existing)
   backend/app/api/jobs.py:_sync_quotation_to_job_costs already supports
   buying via ServiceQuotationRequest. Underused — wire into UI.
```

## Files to create

- `backend/scripts/import-vendor-invoices.py` (template)
- `backend/app/api/jobs.py` — add PATCH endpoint for cost.buying
- `frontend/src/components/JobCostEditor.jsx`

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

## Open questions

- Where do vendor invoices come from currently?
- Is there a vendor portal integration possibility?
- Audit trail required for buying_amount changes?
