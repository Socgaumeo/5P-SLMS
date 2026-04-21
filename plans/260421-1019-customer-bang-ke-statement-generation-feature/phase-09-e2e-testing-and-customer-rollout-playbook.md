# Phase 9 — E2E Testing + Customer Rollout Playbook

## Context links
- [plan.md](plan.md)
- Existing: `scripts/dainese/verify-all-customer-bang-ke-exports-vs-originals-side-by-side.py`

## Overview
- Priority: High (release readiness)
- Status: Pending
- Brief: Comprehensive E2E test suite + documented playbook to onboard new customer in <30 min.

## E2E test scope

### Per-customer regression suite
For each registered customer:
1. Fetch template list via `/api/exports/templates/{code}`
2. Call export endpoint with month=current
3. Validate Excel output:
   - Has 5P logo at A1
   - Title contains customer name + month
   - At least 1 data row OR appropriate "no jobs" response
   - Totals row present
   - VAT row present (if customer config requires)
   - Bank info footer present
4. Sum cell values manually (avoid openpyxl formula evaluation issue)
5. Compare against `jobs.total_revenue` from `/api/search/jobs-by-entity`
6. Diff < 1% acceptable

### Workflow tests (cross-feature)
- Telegram → create customs job → reject (no loai_hinh) → re-create with loai_hinh → bảng kê includes new job
- Quotation entry → cost auto-synced to job_costs → bảng kê reflects fee
- Date range vs month filter consistency
- Service type filter narrows correctly

### Performance tests
- Customer with 200+ jobs/month (MEIKO benchmark)
- Multi-sheet customer (TDI/DAINESE)
- Concurrent exports (5 users simultaneously)

## Customer rollout playbook

```markdown
## Onboard new customer X to bảng kê export

### Step 1: Identify template family
- Get T3 sample Excel from KH
- Run scan: `scripts/dainese/scan-all-customer-bang-ke-templates-and-cluster-by-signature.py`
- Match cluster signature → choose family (A trucking / B handling / C customs / D international / SPECIAL)

### Step 2: Verify DB has the customer + jobs
- Check `customers` table has matching customer_code
- Check there are job_services + job_costs for sample period
- If costs missing: backfill from sample Excel (use existing import-* script as template)

### Step 3: Register in registry
Edit `backend/app/api/exports/customer_export_template_registry.py`:
```python
"NEWCUST": {
    "name": "New Customer Vietnam",
    "module": "generic_customer_export",
    "supports_date_filter": True,
    "templates": [_trucking_template()],  # or _handling_template() etc.
},
```

### Step 4: Verify
- Restart backend
- Call `/api/exports/customer/NEWCUST?month=2026-MM&template=trucking`
- Open Excel → eyeball check vs original
- Run verification script with NEWCUST added to CUSTOMERS list

### Step 5: Special config if needed
- Custom title text → set `title_template` in template config
- Custom VAT rate → set `vat_rate`
- Custom sheet name → set `sheet_name`
- Hide bank info → `include_bank=False`

### Step 6: Notify customer + train
- Show user search → click button → download flow
- Document any data entry quirks (loai_hinh required for customs, etc.)
```

## Files to create

- `backend/tests/test_customer_export_per_customer_regression.py` — pytest suite
- `backend/tests/test_customer_export_e2e_workflows.py`
- `docs/customer-bang-ke-rollout-playbook.md` — for non-dev users
- `docs/customer-bang-ke-architecture.md` — for devs

## Implementation steps

1. Build pytest fixture: spin up test backend, seed customer + 1 job + 1 cost
2. Per-family parameterized tests
3. Per-customer regression test (loop over registry)
4. CI integration: GitHub Actions runs on every PR
5. Write playbook doc
6. Write architecture doc

## Todo list

- [ ] Build pytest fixtures (backend test client, seed data)
- [ ] Per-family parameterized E2E tests
- [ ] Per-customer regression loop
- [ ] Workflow tests (Telegram, quotation sync)
- [ ] Performance benchmark
- [ ] Rollout playbook doc in `docs/`
- [ ] Architecture doc in `docs/`
- [ ] CI integration
- [ ] Onboard 1 new customer using playbook (dry run)

## Success criteria
- 100% pass rate on regression suite
- Playbook adopted: non-dev can onboard new customer in <30 min
- Architecture doc gives new dev full context in <15 min reading
- CI catches regressions before merge

## Risk assessment
- **Risk**: Test backend setup complex (Supabase). Mitigation: use SQLite in-memory for unit tests, mock Supabase calls.
- **Risk**: Playbook decays without enforcement. Mitigation: link from CONTRIBUTING.md + auto-validate on PR.

## Final deliverables checklist

- [ ] All 22 customers have working bảng kê export
- [ ] Regression suite green
- [ ] Playbook published in `docs/`
- [ ] Architecture doc in `docs/`
- [ ] Admin can onboard customer 23+ via UI (Phase 8) without code change
