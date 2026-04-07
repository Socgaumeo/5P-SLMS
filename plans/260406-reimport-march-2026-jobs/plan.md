# Plan: Re-import March 2026 Jobs

## Overview
Complete rewrite of the March 2026 jobs import script to fix all parsing errors, handle ALL Excel files, implement proper cost line items separation (service fees vs thu/chi hộ), and standardize VAT handling.

## Status: PLANNING

## Key Requirements
1. **All 34 files** across 21 customers must be parsed (was: only ~20 files parsed)
2. **Multiple cost line items** per job: service fees + thu/chi hộ as separate `job_costs` rows
3. **Pre-VAT amounts** stored in `selling_rate`, VAT info stored in `service_details` JSONB
4. **Thu/chi hộ** fees have NO VAT (selling_rate = exact amount, is_reimbursement = true)
5. **Document numbers** captured: invoice, CD (tờ khai), BL/AWB, CO
6. New customer **KK** needs customer record created

## Phases

| # | Phase | Status |
|---|-------|--------|
| 1 | [DB Schema Migration](phase-01-db-migration.md) | Pending |
| 2 | [Customer KK Setup](phase-02-customer-kk.md) | Pending |
| 3 | [Rewrite Import Script](phase-03-rewrite-import.md) | Pending |
| 4 | [Cross-check Validation](phase-04-crosscheck.md) | Pending |

## Dependencies
- Supabase PostgreSQL (port 6543)
- openpyxl, xlrd in `.claude/skills/.venv`
- DB connection: `postgresql://postgres.ooixntyflwmjaryxwakx:%21%40kHanh0112@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres`

## File Inventory (34 files, 21 customers)

| Customer | Files | Service Types |
|----------|-------|---------------|
| DAINESE (5) | CO, nhập sea/air, tc/cpn, trucking, xuất | CUS_CO, SEA_IMP, AIR_IMP, CUS_EXPORT, CUS_IMPORT, TRUCKING_DOM |
| DONSUNG (1) | Warehouse storage | WHS_STORAGE, WHS_HANDLE |
| GANG THÉP TN (2) | Customs main + CPN | CUS_EXPORT, TRUCKING_DOM |
| GLOREX (4) | Quốc tế, tại chỗ, TCH GLOREX, TCH GLOBAL | CUS_EXPORT, CUS_IMPORT, TRUCKING_DOM |
| HƯNG PHÁT (2) | 2 debit notes | TRUCKING_DOM |
| KCVN (1) | Customs multi-sheet | CUS_EXPORT |
| KK (1) | Trucking vải + chống ẩm + sea dom | TRUCKING_DOM, SEA_DOM |
| KWE (1) | Warehouse debit | WHS_STORAGE, WHS_HANDLE, TRUCKING_DOM |
| LAS (1) | Sea import | SEA_IMP |
| LKV BD (1) | Trucking | TRUCKING_DOM |
| LKV MB (1) | Trucking | TRUCKING_DOM |
| LOGIMARK (2) | 2 customs declarations | CUS_EXPORT |
| MESSER (1) | Customs + trucking + chi hộ | CUS_IMPORT, TRUCKING_DOM |
| NIPPON (2) | Thai Nguyen .xls + rv.xlsx | CUS_EXPORT |
| TDI (2) | Air services + customs (ZKL T3.2026 sheet) | AIR_IMP, CUS_EXPORT |
| THÁI HOÀ (2) | Customs + thu chi hộ | CUS_EXPORT |
| TVC (1) | Handling fees | WHS_HANDLE |
| UTRACORN (1) | Trucking | TRUCKING_DOM |
| VINTECH (2) | Trucking + air import | TRUCKING_DOM, AIR_IMP |
| XÂY LẮP VN (1) | Trucking | TRUCKING_DOM |
