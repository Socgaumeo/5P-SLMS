# Phase 3: Rewrite Import Script - Per-Customer Parsers

## Overview
- **Priority**: CRITICAL
- **Status**: Pending
- Complete rewrite of `backend/scripts/import-march-2026-jobs.py`

## Key Insights
- Previous script missed 14+ files, wrong revenue for many customers
- Must create MULTIPLE `job_costs` per job (service fees + thu/chi hộ separately)
- ALL amounts must be pre-VAT; VAT info stored in service_details JSONB
- Some sheets are old templates (Aug 2024 "XNK TAI CHO") — must be SKIPPED
- TDI's ZKL file has sheets for different years — only use "T3.2026" sheet

## Architecture

### Data Flow
```
Excel file → Parser → job_data dict → DB Inserter
                                         ├── jobs (1 row per shipment)
                                         ├── job_services (1 row with service_details JSONB)
                                         └── job_costs (N rows: service fees + thu/chi hộ)
```

### Job Data Structure
```python
{
  "customer_id": 20,
  "date": date(2026, 3, 12),
  "description": "Air import - Bill: 82818592630",
  "svc_type": "AIR_IMP",
  "cd_no": "308317694220",
  "bl_awb": "82818592630",
  "invoice": "00000215",
  "weight": 1085.5,
  "origin": "Nội Bài",
  "dest": "KCN Phúc Điền, Hải Dương",
  "costs": [
    {"name": "Phí dịch vụ làm hàng", "amount": 700000, "vat_rate": 0.08, "vat": 56000, "invoice": ""},
    {"name": "Vận chuyển NB - Hải Dương", "amount": 2123430, "vat_rate": 0.08, "vat": 169874, "invoice": ""},
    {"name": "Thu hộ: Phí cân hàng ACSV", "amount": 1957522, "vat_rate": 0, "invoice": "36308", "is_reimbursement": True},
  ],
  "customs_type": "IMPORT",
  "route": "Nội Bài → KCN Phúc Điền, Hải Dương",
}
```

## Per-Customer Parser Specifications

### 1. DAINESE (5 files, customer_id=46)

**File 1: BẢNG KÊ PHÍ CO DAINESE T3.2026. 5P.xlsx**
- Sheet: 'DỊCH VỤ'
- Service: CUS_CO (Certificate of Origin)
- Header R13: STT | NGÀY C/O | INVOICE | SỐ CO | FORM | SỐ LƯỢNG | ĐƠN GIÁ | THÀNH TIỀN | SỐ HÓA ĐƠN | GHI CHÚ | THU CHI HỘ
- Sub-header R14: NỘI DUNG | SỐ TIỀN | SỐ BIÊN LAI
- Data starts R15
- Revenue: C8 (THÀNH TIỀN) = pre-VAT service fee
- Thu chi hộ: C11=NỘI DUNG, C12=SỐ TIỀN (no VAT), C13=SỐ BIÊN LAI
- VAT: 0% (row R18 shows "VAT (0%)")
- Totals: R17 TỔNG TRƯỚC VAT=1,200,000, R19 THU CHI HỘ=60,000, R20 TỔNG=1,260,000
- Parse: 2 CO jobs, each with service fee cost + thu hộ cost

**File 2: Bảng kê nhập tháng 3.2026.sea.air.xlsx**
- Sheet: 'NHẬP' (203r x 228c)
- Service: SEA_IMP or AIR_IMP (detect from C7: SEA/AIR)
- Header R12: No. | Tờ khai | HĐTM | Vận đơn | Ngày TK | Tuyến đường | Loại hình | Kgs | No.Cont | Note
- Fee columns C11-C21: Phí mở TK, kiểm hóa, vận chuyển, làm hàng, phát sinh, nước ngoài, cước QT, THC, CFS, DO, đại lý
- Data starts R13
- Each row = 1 job with MULTIPLE costs (each fee column = 1 cost line)
- Skip rows where all fee columns are 0/empty
- Pre-VAT amounts (no explicit VAT column per fee)
- Sheet 'Sheet1' is a summary template — SKIP

**File 3: Bảng kê tháng 3.2026. tc.nhap cpn.xlsx**
- Sheet: 'tc, cpn' (224r x 229c)
- Service: CUS_EXPORT (XNK tại chỗ / CPN)
- Same header structure as File 2
- Data starts R13
- Loại hình = "DOM" (domestic/tại chỗ)
- Fee columns same as File 2
- Sheet 'Sheet1' = summary — SKIP

**File 4: Copy of (DAINESE-5PVN) BẢNG KÊ TT T3.2026 bs2.xlsx**
- Sheet: 'HĐ' (43r x 21c) — Trucking
- Service: TRUCKING_DOM
- Header R13: STT | Ngày | Điểm lấy (C3+C4) | Điểm trả (C5+C6) | BKS | Đơn vị | SL | Phát sinh | Cước VC | Phụ phí XD | Thành tiền | Tổng | Note | Yêu cầu | Số HĐ
- Data starts R15
- Revenue: C14 (Tổng) = post-VAT (NO — actually pre-VAT, no tax column visible)
- C10 = Phát sinh (extra charge)
- 2 costs per job if phát sinh > 0: main fee + phát sinh
- Sheet 'PurchPurchaseOrder' = PO template — SKIP

**File 5: Copy of Bảng kê xuất tháng 3.2026 final.xlsx**
- Sheet: 'XUẤT' (218r x 236c) — Export customs
- Service: CUS_EXPORT
- Same structure as File 2/3
- Data starts R13, multiple fee columns
- Sheet 'KMTCVN01104033' — individual shipment detail (per-booking breakdown)
  - Has phí dịch vụ + phí tại VN items
  - Parse as additional detail for specific shipments
- Sheet 'Sheet1' = summary — SKIP

### 2. DONSUNG (1 file, customer_id=58)

**File: BẢNG KÊ DỊCH VỤ KHO T3.2026 DONGSUNGrev.xlsx**
- Sheet: 'HDDT' or 'DNTT' (same data, use 'HDDT')
- Service: WHS_STORAGE / WHS_HANDLE
- Header R11: STT | Tên hàng hóa | ĐVT | SL | Đơn giá | Phí khác | Thành tiền chưa VAT | Thuế suất | Tiền thuế | Thành tiền có VAT
- Data: 3 rows (2 storage + 1 handling)
- Pre-VAT = C7, VAT rate = C8 (0.1 or 0.08), VAT = C9, Post-VAT = C10
- Create 3 job_costs: 2 storage + 1 handling, selling_rate = pre-VAT (C7)
- Sheets: 'Kangatang', 'Data lưu kho...', 'Báo giá', 'cfm', 'mail', 'Sheet1' = SKIP

### 3. GANG THÉP TN (2 files, customer_id=44)

**File 1: BangKe_GangThep_T3_2026_v10.xlsx**
- Sheet: 'BẢNG KÊ DỊCH VỤ' (52r)
- Service: CUS_EXPORT
- Header R13: STT | Ngày | ... | Nội dung | Số tờ khai | SL | ĐVT | Đơn giá | Thành tiền | Tổng
- Data starts R15, ~20 declarations
- Pre-VAT amounts (C9=Thành tiền=800,000 each, NO VAT column)
- NOTE: User said pre-VAT amounts. File shows 800,000/TK, no separate VAT line

**File 2: Debit_GangThep_CPN_T3_2026.xlsx**
- Sheet: 'GANG THÉP' (29r)
- Service: CUS_EXPORT + TRUCKING
- Header R12-13: STT | Ngày TK | Số TK/Bill | Dịch vụ | Service fee (Đơn giá, SL, ĐVT, Thành tiền, Tax, Tổng tiền, HĐ) | Chi hộ (Số HĐ, Số tiền, VAT, Thành tiền) | TỔNG CỘNG
- Grouped rows: R14-R16 = shipment 1 (customs + trucking + 2 chi hộ)
- Service fees: C8=pre-VAT, C9=Tax, C10=post-VAT
- Chi hộ: C13=amount, C14=VAT, C15=post-VAT (separate invoices in C12)
- TOTAL: Service=6,000,000 + tax=480,000 = 6,480,000. Chi hộ=0 (in this file). Grand=6,480,000

### 4. GLOREX (4 files, customer_id=18)

**File 1: Debit 5PVN_GLOREX 3.2026.QUỐC TẾ.xlsx**
- Sheet: 'GLOREX' — International logistics import
- Service: SEA_IMP / TRUCKING_DOM
- Header R12: STT | Ngày | Loại xe | Booking/Bill/BKS | VC (Lấy/Trả) | TK | Nội dung | ĐVT | SL | Đơn giá | Số tiền | VAT | Tổng tiền | Số HĐ | Note
- Grouped rows: shipment 1 = R15-R19 (5 cost lines: handling, trucking, giám sát, csht trả hộ, bốc xếp trả hộ)
- Pre-VAT = C12, VAT = C13, Post-VAT = C14
- "trả hộ" items: VAT may be 0 or included — check C13
- Sheet 'XNK TAI CHO' = OLD 2024 data — SKIP

**File 2: Debit 5PVN_GLOREX T3.2026 TẠI CHỖ.xlsx**
- Sheet: 'XNK TC' — Customs at-place (tại chỗ)
- Service: CUS_EXPORT
- Header R12: STT | Ngày | TK | Luồng | Note | Số HĐ/PXK | Phí mở TK | Phí KH | Phí phát sinh | Tổng tiền | Thu chi hộ (Vé bãi KH | Số tiền) | Số HĐ
- Data: 10 declarations, each 600,000 pre-VAT
- Total pre-VAT = 6,000,000, VAT 8% = 480,000, post-VAT = 6,480,000
- Thu chi hộ = 0 in this file
- Sheet 'XNK TAI CHO' = OLD 2024 — SKIP

**File 3: Debit_TCH_5PVN_GLOREX_T3_2026_full (4).xlsx**
- Sheet: 'NHAP KHAU' — Thu chi hộ for GLOREX
- Service: linked to GLOREX customs jobs
- Content: Lệ phí hải quan 20,000 x 10 TK = 200,000, no VAT
- Has GNT numbers (giấy nộp tiền)
- Create 10 thu hộ cost items at 20,000 each
- Sheet 'XNK TAI CHO' = OLD 2024 — SKIP

**File 4: Debit_TCH_5PVN_GLOBAL_T3_2026_full (4) - Copy.xlsx**
- Sheet: 'NHAP KHAU' — Thu chi hộ for GLOBAL (different customer!)
- WARNING: This file is NOT for GLOREX, it's for GLOBAL TRADE INVESTMENT
- Only 2 items: 20,000 x 2 = 40,000
- DECISION: Skip this file (GLOBAL is not in our customer list) OR create as misc cost under GLOREX if per user instruction
- Sheet 'XNK TAI CHO' = OLD 2024 — SKIP

### 5. HƯNG PHÁT (2 files, customer_id=63)

**File 1: Debit note HƯNG PHÁT-5P T3.2026.xlsx**
- Sheet: 'BẢNG KÊ CHI TIẾT'
- Service: TRUCKING_DOM
- Standard format: R14 data
- 1 job: 27/03, BKS=89H08537, 1.25T, 1,675,000 pre-VAT, tax=134,000, total=1,809,000
- VAT 8%

**File 2: Debit note HƯNG PHÁT-5P T3.2026 - L2.xlsx**
- Sheet: 'BẢNG KÊ CHI TIẾT'
- Service: TRUCKING_DOM
- 1 job: 07/03, BKS=15H 05933, 1.25T, 2,350,000 pre-VAT, tax=188,000, total=2,538,000
- VAT 8%

### 6. KCVN (1 file, customer_id=61)

**File: BangKe_KCIL_T3_2026_v14.xlsx**
- Sheet: 'Tháng 2.2026' (actually March data per title "BẢNG KÊ DỊCH VỤ THÁNG 03.2026")
- Service: CUS_EXPORT
- Header R17: STT | Invoice | SỐ TKHQ | Ngày TK | Bill | Note | SỐ KIỆN | Số cont | Trọng lượng | Invoice | Luồng | Đơn giá USD | Tỷ giá | Thành tiền USD | Tổng phí DV | VAT | Tổng thanh toán | Phát sinh | Phí chi hộ (Số HĐ | Nội dung | Số tiền)
- Data: 4 rows (4 TK), R19-R22
- Amounts in USD: rate=0.18 USD/kg, exchange rate=26,364
- Pre-VAT = C15, VAT = C16, Post-VAT = C17
- Total pre-VAT = 204,987,482, VAT = 16,398,999, Post-VAT = 221,386,480
- Chi hộ = 0
- Sheet 'Tháng 2.2026 ĐNTT (2)' = same data (payment request version) — SKIP
- Sheet 'Kangatang' — SKIP

### 7. KK (1 file, customer_id=NEW)

**File: Debit Note.KK.MAR.2026. org.xlsx**
- 3 sheets:

**Sheet 'TRUCKING VẢI'**: TRUCKING_DOM
- Header R13: STT | Ngày | Type | Điểm lấy | Điểm trả | Biển số | SL | ĐVT | Đơn giá | Thành tiền | Chi phí khác | Tổng | JOB | Ghi chú
- 3 jobs (R15-R17): Trảng Bàng → Chương Mỹ
- Pre-VAT totals, VAT 8% shown at bottom
- Total pre-VAT=28,050,000, VAT=2,244,000, Total=30,294,000

**Sheet 'TRUCKING CHỐNG ẨM'**: TRUCKING_DOM
- 1 job: Bình Hưng HCM → Chương Mỹ HN, 1,900,000 + 500,000 other = 2,400,000
- VAT 8%=192,000, Total=2,592,000

**Sheet 'SEA DOM'**: SEA_DOM
- 11 containers 40HC Trảng Bàng → Chương Mỹ
- Each 25,850,000 pre-VAT (last one + 550,000 phí khác)
- Total pre-VAT=284,900,000, VAT 8%=22,792,000, Total=307,692,000

### 8. KWE (1 file, customer_id=28)

**File: 5P in MAR.2026. KWE rev.xlsx**
- Sheet: 'Accountant Sheet' (282r, the BIG one)
- Service: WHS_STORAGE, WHS_HANDLE, TRUCKING_DOM
- Header R17: No. | Description | Amount (VND) | VAT (%) | VAT Amount | Total Amount
- Data R18-R21: 4 services
  - Storage = 61,795,500 pre-VAT, 8% VAT
  - Stevedore = 9,090,000 pre-VAT, 8% VAT
  - Inventory = 19,014,000 pre-VAT, 8% VAT
  - Trucking = 8,040,000 pre-VAT, 8% VAT
- Grand total: 97,939,500 pre-VAT, 7,835,160 VAT, 105,774,660 post-VAT
- 1 job with 4 cost lines
- Sheets: 'Accountant Sheet.' (old), 'Storage' (daily detail) — use for reference only

### 9. LAS (1 file, customer_id=6)

**File: DebitNote_LGZHPH260781_LAS_DRAFT (13).xlsx**
- Sheet: 'dịch vụ' (62r)
- Service: SEA_IMP
- Shipment info R13-R17: Bill=LGZHPH260781, TK=108048106940, 26 cartons, 560kg
- Section 1 (R20): Phí tại nước ngoài
  - 1.1 Cước VCQT = 1 USD (26,318 VND) — seems like $1 for 0.45 CBM
  - 1.2 Phí làm hàng = 214 USD = 5,632,052 VND
  - Total nước ngoài = 5,658,370
- Section 2 (R24): Chi phí tại Việt Nam
  - 2.1 Phí HQ = 30 USD = 789,540 + 8% VAT = 852,703
  - More items follow (needs full read of R25-R40+)
- Multiple cost lines per section, each with own VAT treatment
- Nước ngoài fees = no VAT; VN fees = 8% VAT
- This is the file user said was only partially extracted

### 10. LKV BD (1 file, customer_id=60)

**File: Debit note SX LỌC KHÍ VIỆT BD-5P T3.2026 REV1.xlsx**
- Sheet: 'LKV BẢNG KÊ CHI TIẾT' (30r)
- Service: TRUCKING_DOM
- Standard format: STT | Ngày | BKS | Loại xe | Dịch vụ | Đơn giá | SL | ĐVT | Thành tiền | Tax | Tổng tiền | HĐ
- 4 jobs (R14-R17)
- Pre-VAT = C9, Tax = C10 (8%), Total = C11

### 11. LKV MB (1 file, customer_id=53)

**File: Debit note SX LỌC KHÍ VIỆT MIỀN BẮC-5P T3.2026 rev14.xlsx**
- Sheet: 'LKV BẢNG KÊ CHI TIẾT' (39r)
- Service: TRUCKING_DOM
- Same format as LKV BD
- 12 jobs (R14-R25) — includes trucking + chờ giờ + hạ hàng
- Pre-VAT = C9, Tax = C10, Total = C11
- Some have time tracking (C13-C21)

### 12. LOGIMARK (2 files, customer_id=31)

**File 1: Debit_LOGIMARK_T3_2026 (2).xlsx**
- Sheet: 'LOGIMARK'
- Service: CUS_EXPORT
- 1 declaration: TK=308320129960, 12/03/2026, 650,000 pre-VAT, 52,000 tax, 702,000 total

**File 2: Debit_LOGIMARK_T3_2026_updated (3).xlsx**
- Sheet: 'LOGIMARK'
- Service: CUS_EXPORT
- 1 declaration: TK=308353503860, 23/03/2026, 650,000 pre-VAT, 52,000 tax, 702,000 total

### 13. MESSER (1 file, customer_id=22)

**File: Bảng kê MESSER 5P T3.2026.xlsx**
- Sheet: 'MESSER HẢI DƯƠNG' (35r x 31c)
- Service: CUS_IMPORT
- Header R12-13: Date | Ngày TK | Số TK | Dịch vụ | Service fee (Đơn giá, SL, ĐVT, Thành tiền, Tax, Tổng tiền, HĐ) | Chi hộ (Số HĐ, Số tiền, VAT, Thành tiền) | TỔNG CỘNG | Ghi chú
- Shipment 1 (R14-R17):
  - Custom clearance: 1,200,000 x 2 CD = 2,400,000 + tax 192,000 = 2,592,000
  - Trucking: 1,500,000 + tax 120,000 = 1,620,000
  - Chi hộ 1: 1,997,800 + VAT 159,824 = 2,157,624 (HĐ 00001144)
  - Chi hộ 2: 2,066,140 + VAT 165,291 = 2,231,431 (HĐ 00001143)
- Shipment 2 (R18): Custom clearance only: 1,200,000 + tax 96,000 = 1,296,000
- TOTALS: Service pre-VAT=5,100,000, tax=408,000, post-VAT=5,508,000
- Chi hộ total=4,063,940 + VAT 325,115 = 4,389,055
- GRAND TOTAL=9,897,055

### 14. NIPPON (2 files, customer_id=64)

**File 1: (THAI NGUYEN) BẢNG KÊ CHI PHÍ NIPPON THÁNG 3.2026.xls**
- Sheet: 'NIPPON' (41r) — .xls format (use xlrd)
- Service: CUS_EXPORT
- Header R17-R18: STT | Invoice | SỐ TKHQ | Ngày TK | Phân luồng | Phí mở TK | Phí khác | Phí C/O | Phí KH | Tổng phí DV | VAT | Tổng thanh toán | Phát sinh | Phí chi hộ (Số HĐ, Nội dung, Số tiền) | Tổng chi hộ | Nguồn | Ghi chú
- ~18 declarations, each 300,000 pre-VAT + 24,000 VAT = 324,000
- Some may have chi hộ items
- Dates are Excel serial numbers (use xlrd.xldate_as_datetime)

**File 2: BẢNG KÊ CHI PHÍ NIPPON THÁNG 3.2026 rv.xlsx**
- Sheet: 'NIPPON' (105r x 41c) — LARGE, multi-month data
- Title says "BẢNG KÊ DỊCH VỤ THÁNG 1.2026" but contains data across months
- Header R17: STT | Invoice | SỐ TKHQ | Ngày TK | Bill | Note | SỐ KIỆN | Số cont | Loại hình | Số invoice | (cont types) | Số vận đơn | Phí mở TK | Phí DV | Phí KH | Phí ngoài giờ | Phí ĐKDM | Tổng phí DV
- Data from R19, ~80+ rows across months
- MUST FILTER by date (March 2026 only)
- Pre-VAT fees in individual columns
- Sheet 'Kangatang' — SKIP

### 15. TDI (2 files, customer_id=20)

**File 1: Copy of BangKe_TDI_AirT3_2026_ final1.xlsx**
- 3 sheets:

**Sheet 'TDI LÊN HÓA ĐƠN 1'** (65r): Air import services
- Service: AIR_IMP
- Header R12-13: STT | Ngày | Số TK | Số Bill | Số REF | Trọng lượng | Dịch vụ | Nội dung (SL, Đơn giá, Phụ phí XD, ĐVT, Thành tiền, Tax, Tổng tiền, HĐ) | Chi hộ (Số HĐ, Thành tiền) | Tổng thanh toán | Ghi chú
- Grouped rows per shipment:
  - Row with STT = main shipment (Phí DV làm hàng + VC + chi hộ)
  - Sub-rows = additional services
- Service fee: C12=pre-VAT, C13=tax, C14=post-VAT
- Chi hộ: C16=Số HĐ, C17=Thành tiền (NO VAT on thu hộ)
- C18 = Tổng thanh toán per shipment
- 5 shipments with multiple cost lines each

**Sheet 'TDI LÊN HÓA ĐƠN 2'** (27r): Dangerous goods surcharge
- Service: linked to same shipments
- 5 rows: "Phí làm hàng nguy hiểm (PIN Li)" 1,800,000 each
- Pre-VAT=1,800,000, Tax=144,000, Total=1,944,000
- Grand total: 9,000,000 + 720,000 = 9,720,000
- These should be ADDITIONAL cost lines on the same jobs from Sheet 1

**Sheet 'TDI THU CHI HỘ1'** (38r): Reimbursement details
- All thu/chi hộ items for TDI shipments
- Header R12-13: STT | Ngày | Số Bill | Dịch vụ | Chi hộ (Số HĐ, Thành tiền) | Tổng thanh toán
- ~20 items: phí lưu kho, bốc xếp, cân hàng, lấy lệnh, etc.
- NO VAT on these items
- Must link to correct job by Bill number

**File 2: TDI of BẢNG THEO DÕI T03.2026 bs_ZKL.xlsx**
- Sheet: 'T3.2026' (54r x 30c) — Customs declarations
- Service: CUS_EXPORT
- Header R20: STT | Dịch vụ | Ngày | Số quyết toán | Số TK | Phân luồng | Phí thông quan | Kiểm hóa | Ngoài giờ | Chi phí khác | Số tiền | 8% VAT | Tổng thành tiền | Thu hộ trả hộ | Ghi chú
- Data from R21: ~25 declarations
- Pre-VAT = C11, VAT = C12, Post-VAT = C13
- Most: 600,000 (xanh) or 750,000 (vàng) pre-VAT
- OTHER SHEETS (T1-2023, T12-2022, etc.) = old data, SKIP

### 16. THÁI HOÀ (2 files, customer_id=45)

**File 1: Debit_5PVN_THAI_HOA_T3_2026 (9).xlsx**
- Sheet: 'XNK TC' — Customs tại chỗ
- Service: CUS_EXPORT
- 2 declarations: 600,000 pre-VAT each
- Total pre-VAT=1,200,000, VAT 8%=96,000, Total=1,296,000
- Sheet 'XNK TAI CHO' = OLD 2024 — SKIP

**File 2: Debit_TCH_5PVN_THÁI HÒA_T3_2026_full (4) - Copy.xlsx**
- Sheet: 'NHAP KHAU' — Thu chi hộ
- 2 items: Lệ phí hải quan 20,000 x 2 = 40,000 (no VAT)
- Sheet 'XNK TAI CHO' = OLD 2024 — SKIP

### 17. TVC (1 file, customer_id=59)

**File: Debit Note. 5P. TVC. T03.2026.xlsx**
- Sheet: 'BẢNG KÊ DỊCH VỤ'
- Service: WHS_HANDLE
- 1 job: 17/03, Nâng hạ hàng, 9 pallet x 80,000 = 720,000 pre-VAT
- VAT 8% = 57,600, Total = 777,600

### 18. UTRACORN (1 file, customer_id=56)

**File: DebitNote_UTRACON_TRK1403_DRAFT (3).xlsx**
- Sheet: 'TRUCKING'
- Service: TRUCKING_DOM
- 1 job: 14/03, Gia Sàng TN → Đông Anh HN, 8T, 2,410,000 pre-VAT
- VAT 8% = 192,800, Total = 2,602,800

### 19. VINTECH (2 files, customer_id=57)

**File 1: Debit note VINTECH-5P T3.2026.xlsx**
- Sheet: 'LKV BẢNG KÊ CHI TIẾT'
- Service: TRUCKING_DOM
- 1 job: 28/03, BKS=89H08537, Consol, 4,500,000 pre-VAT, tax=360,000, total=4,860,000

**File 2: DebitNote_VINTECH_NGB637324_DRAFT.xlsx**
- Sheet: 'AI' (42r) — Air import
- Service: AIR_IMP
- Shipment: NORD (China) → VINTECH, Bill=NGB637324, TK=108057770660, 562kg
- Section 1: Phí nước ngoài
  - Cước VCQT = 562 kg x 1.5 USD x 26,321 = 22,188,603
  - Phí làm hàng TQ = 350 USD = 9,212,350
- Section 2: Chi phí tại VN
  - Phí HQ = ~1,300,000 + 8% VAT
  - More items...
- Total = 36,959,757 (grand total of all sections)
- Multiple cost lines with different VAT treatments

### 20. XÂY LẮP VN (1 file, customer_id=2)

**File: Debit note XÂY LẮP VN-5P T3.2026.xlsx**
- Sheet: 'BẢNG KÊ CHI TIẾT'
- Service: TRUCKING_DOM
- 1 job: 30/03, BKS=20C-053.46, 1.25T, 500,000 pre-VAT, tax=40,000, total=540,000

## Implementation Steps

1. Delete all existing March 2026 jobs from DB
2. Create helper functions: s(), n(), d(), cell()
3. Implement per-customer parser functions returning list of job_data dicts
4. Each job_data has `costs` list (service fees + thu/chi hộ)
5. DB inserter: job → job_service (with service_details JSONB) → N x job_costs
6. Print summary per customer

## Important Rules
- SKIP sheets named "XNK TAI CHO" with 2024 dates
- SKIP sheets named "Kangatang", "Sheet1" (summary), "Báo giá", "cfm", "mail"
- SKIP "PurchPurchaseOrder" sheets
- For TDI ZKL file: ONLY use "T3.2026" sheet
- For NIPPON rv file: FILTER by March 2026 dates only
- For GLOREX GLOBAL file: confirm with user whether to include or skip

## Todo List
- [ ] Delete existing March 2026 data
- [ ] Create KK customer
- [ ] Implement all 20 customer parsers
- [ ] Test each parser individually
- [ ] Run full import
- [ ] Cross-check totals

## Success Criteria
- All 34 files parsed correctly
- Each job has multiple cost line items (not grouped)
- Service fees stored as pre-VAT in selling_rate
- Thu/chi hộ stored separately with is_reimbursement flag
- VAT info in service_details JSONB
- Total revenue matches Excel totals (pre-VAT service + thu/chi hộ)

## Risk Assessment
- Complex multi-sheet files (DAINESE, TDI) may have edge cases
- Currency conversion (KCVN, LAS, VINTECH) needs accurate exchange rates from file
- NIPPON rv file spans multiple months — date filtering critical
- GLOREX GLOBAL file may need user decision
