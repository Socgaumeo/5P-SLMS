# Customer Bảng Kê Verification Report — Generated vs Original

**Month**: 2026-03 | **Backend**: http://localhost:8000

| Customer | Template | Gen Rows | Gen Total | Orig File | Orig Rows | Orig Total | Status |
|---|---|---|---|---|---|---|---|
| BINHMINH | trucking | 3 | 0 | `Copy of Debit Note.Bình Minh. Mar.2026 L2.xlsx` | 1 | 5,253,500 | ❌ Revenue=0 (DB missing costs) |
| KK | trucking | 3 | 28,050,000 | `Debit Note.KK.MAR.2026. org.xlsx` | 16 | 341,200,000 | ⚠️ Partial-match |
| DONGSUNG | trucking | 0 | 0 | `BẢNG KÊ DỊCH VỤ KHO T3.2026 DONGSUNGrev.xlsx` | 6 | 236,418,669 | ❌ Data-gap (DB empty) |
| UPGAIN | trucking | 3 | 0 | `Copy of Debit Note.UPGAIN.MARCH.2026 (.xlsx` | 3 | 92,882,400 | ❌ Revenue=0 (DB missing costs) |
| UTRACON | trucking | 1 | 2,410,000 | `DebitNote_UTRACON_TRK1403_DRAFT (3).xlsx` | 1 | 2,410,000 | ✅ Match |
| TVC | trucking | 0 | 0 | `Debit Note. 5P. TVC. T03.2026.xlsx` | 1 | 720,000 | ❌ Data-gap (DB empty) |
| HUNGPHAT | handling | 2 | 4,025,000 | `Debit note HƯNG PHÁT-5P T3.2026 - L2.xlsx` | 1 | 2,538,000 | ⚠️ Partial-match |
| VINTECH | handling | 7 | 41,196,587 | `DebitNote_VINTECH_NGB637324_DRAFT.xlsx` | 3 | 31,400,953 | ⚠️ Partial-match |
| KTXL | handling | 1 | 500,000 | `Debit note XÂY LẮP VN-5P T3.2026.xlsx` | 1 | 540,000 | ✅ Match |
| LOGIMARKHN | handling | 2 | 1,300,000 | `Debit_LOGIMARK_T3_2026_updated (3).xlsx` | 1 | 702,000 | ⚠️ Partial-match |
| MESSERHP | handling | — | — | — | — | — | ❌ Missing-in-DB (404) |
| GANGTHEPTN | handling | 24 | 19,200,000 | `BangKe_GangThep_T3_2026_v10.xlsx` | 22 | 13,200,000 | ⚠️ Partial-match |
| LAS | handling | 7 | 9,244,800 | `DebitNote_LGZHPH260781_LAS_DRAFT (13).xlsx` | 3 | 5,658,370 | ⚠️ Partial-match |
| DAINESE | nhap_sea_air | 16 | 0 | `BẢNG KÊ PHÍ CO DAINESE T3.2026. 5P.xlsx` | 2 | 1,200,000 | ❌ Revenue=0 (DB missing costs) |
| DAINESE | tt | 10 | 0 | `BẢNG KÊ PHÍ CO DAINESE T3.2026. 5P.xlsx` | 2 | 1,200,000 | ❌ Revenue=0 (DB missing costs) |
| DAINESE | tc_cpn | 28 | 0 | `BẢNG KÊ PHÍ CO DAINESE T3.2026. 5P.xlsx` | 2 | 1,200,000 | ❌ Revenue=0 (DB missing costs) |
| DAINESE | phi_co | 2 | 1,200,000 | `BẢNG KÊ PHÍ CO DAINESE T3.2026. 5P.xlsx` | 2 | 1,200,000 | ✅ Match |
| DAINESE | xuat | 24 | 0 | `BẢNG KÊ PHÍ CO DAINESE T3.2026. 5P.xlsx` | 2 | 1,200,000 | ❌ Revenue=0 (DB missing costs) |
| MEIKO | - | 202 | 225,628,180 | `Copy of Bảng kê 5P -Meiko T3 total final.xlsx` | 0 | 0 | ⚠️ Partial-match |

## Summary

- ✅ Match / partial: **10**
- ❌ Data gap (DB missing revenue/costs): **8**
- ❌ DB has no jobs for month: **1**
- ⚠️ No original found: **0**

## Gap Analysis

For customers with 'Revenue=0' or 'Data-gap', the original Excel has real data
but the DB is incomplete. **This is a data-import issue, not a renderer bug.**
To fix: re-run/extend the import scripts in `backend/scripts/import-*` to
populate `job_costs` from the original customer Excel files.