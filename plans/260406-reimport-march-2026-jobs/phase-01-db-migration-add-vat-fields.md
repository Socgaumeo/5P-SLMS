# Phase 1: DB Schema Migration - Add VAT Fields

## Overview
- **Priority**: HIGH
- **Status**: DONE
- Add `vat_rate` and `is_reimbursement` columns to `job_costs` table

## Architecture Decision: Add Real Columns

Per user request, VAT rate must be editable per cost line (policy changes 8%→10%→5%).

### New columns on `job_costs`:
| Column | Type | Default | Purpose |
|--------|------|---------|---------|
| `vat_rate` | `numeric(5,2)` | 8 | VAT % (8=8%). Editable by staff |
| `is_reimbursement` | `boolean` | false | true = thu/chi hộ (vat_rate forced to 0) |

### How it works:
- `selling_rate` = pre-VAT amount (unchanged)
- `selling_amount` = quantity * selling_rate (GENERATED, unchanged)
- VAT amount = `selling_amount * vat_rate / 100` (computed at frontend/report level)
- Thu/chi hộ rows: `is_reimbursement = true`, `vat_rate = 0`
- Service fee rows: `is_reimbursement = false`, `vat_rate = 8` (default)
- Trigger `update_job_totals()` unchanged — still sums selling_amount (pre-VAT)

### SQL executed:
```sql
ALTER TABLE job_costs ADD COLUMN IF NOT EXISTS vat_rate numeric(5,2) DEFAULT 8;
ALTER TABLE job_costs ADD COLUMN IF NOT EXISTS is_reimbursement boolean DEFAULT false;
```

## Success Criteria
- [x] `vat_rate` column added with DEFAULT 8
- [x] `is_reimbursement` column added with DEFAULT false
- [x] Existing trigger still works (no generated columns changed)
- [x] Backwards compatible (existing rows get default values)
