# Plan: Verify & Fix All March 2026 Customer Jobs

## Overview
Systematic verification of all 20 customers' March 2026 jobs: job_no structure, document numbers, revenue/VAT, file coverage.

## Status: COMPLETED ✓

## Results Summary
- **282 total jobs** across 20 customers
- **Grand total revenue: 1,592,768,997 VND**
- **CUS- prefix**: ALL 194 customs jobs have correct CUS- prefix ✓
- **Revenue integrity**: ALL jobs pass (total_revenue = sum(selling_amounts)) ✓
- **Document coverage**: CD 78%, Invoice 64%, BL/AWB 53%
- **File coverage**: All 34 files across 20 folders processed ✓

## Fixes Applied
1. **CUS- prefix**: 135 customs jobs renamed across 9 customers
2. **NIPPON**: 59 jobs re-imported (Thai Nguyen 15 + rv.xlsx 44)
3. **DAINESE**: 82 document numbers filled (CO, BL, invoice)
4. **TDI**: 23 invoices + 15 BL numbers filled from Air + ZKL files
5. **MESSER**: 2 invoices filled
6. **KWE**: 1 invoice filled (00000190)
7. **LAS**: 1 invoice filled (00000158, 00000209)
8. **KCVN**: 4 invoices filled
9. **LOGIMARK**: 2 BL numbers verified

## Customer Status

| # | Customer | ID | Jobs | CD% | Inv% | BL% | Status |
|---|----------|----|------|-----|------|-----|--------|
| 1 | DAINESE | 46 | 97 | 82% | 84% | 93% | DONE |
| 2 | NIPPON | 64 | 59 | 100% | 100% | 0% | DONE |
| 3 | TDI | 20 | 37 | 100% | 62% | 40% | DONE* |
| 4 | GANG THÉP | 44 | 23 | 100% | 0% | 0% | DONE* |
| 5 | KK | 65 | 16 | 0% | 0% | 100% | DONE* |
| 6 | LKV MB | 53 | 13 | 0% | 0% | 100% | DONE* |
| 7 | GLOREX | 18 | 11 | 100% | 81% | 9% | DONE |
| 8 | KCVN | 61 | 4 | 100% | 100% | 75% | DONE |
| 9 | LKV BD | 60 | 4 | 0% | 0% | 100% | DONE* |
| 10 | DONGSUNG | 58 | 3 | 0% | 0% | 0% | DONE* |
| 11 | LOGIMARK | 31 | 2 | 100% | 0% | 100% | DONE* |
| 12 | HƯNG PHÁT | 63 | 2 | 0% | 0% | 100% | DONE* |
| 13 | VINTECH | 57 | 2 | 50% | 50% | 100% | DONE |
| 14 | MESSER | 22 | 2 | 100% | 100% | 0% | DONE |
| 15 | THÁI HOÀ | 45 | 2 | 100% | 50% | 0% | DONE |
| 16 | KWE | 28 | 1 | 0% | 100% | 0% | DONE |
| 17 | XÂY LẮP VN | 2 | 1 | 0% | 0% | 100% | DONE* |
| 18 | TVC | 59 | 1 | 0% | 0% | 0% | DONE* |
| 19 | UTRACORN | 56 | 1 | 0% | 0% | 100% | DONE* |
| 20 | LAS | 6 | 1 | 100% | 100% | 100% | DONE |

*DONE = all available data extracted. Invoice gaps are because Excel debit notes don't contain invoice numbers (added later during billing).

## Unresolved
- Invoice numbers for trucking-only customers (KK, LKV, HƯNG PHÁT, etc.) not in debit note files
- GANG THÉP: 23 customs jobs have no invoice data in Excel files
- TDI ZKL: 14 jobs have no invoice (quyết toán = TK number, not invoice)
- DONGSUNG/TVC: Warehouse services with no document reference numbers
