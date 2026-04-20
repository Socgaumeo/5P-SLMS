# Customer Bảng Kê Templates — Strategy & Extraction Roadmap

**Scope**: 33 file Excel, 22 customer (trừ DAINESE + MEIKO đã làm xong).
**Source**: `/Users/bear1108/Library/CloudStorage/OneDrive-Personal/5P/DOANH THU/THÁNG 3/`
**Mục tiêu**: Xây dựng generator Excel nhanh từ DB cho mọi customer, giữ format chuẩn.

---

## 1. Điểm chung TẤT CẢ bảng kê (15 trên 22 customer dùng)

Mọi bảng kê đều có cấu trúc **"5P Vietnam Debit Note"** chung:

### 1.1 Header section (rows 1-11)
| Element | Vị trí điển hình | Bắt buộc |
|---|---|---|
| Logo 5P | A1 (anchor) | ✅ |
| Tên công ty 5P | C1 hoặc tương tự | ✅ |
| Địa chỉ 5P | C2 | ✅ |
| MST 5P (`0110523309`) | C3 | ✅ |
| Title bảng kê | A5/A6 merged, 14-26pt bold center | ✅ |
| `Họ tên người mua hàng (Customer): {NAME}` | A7-A9 | ✅ |
| `Địa chỉ (Address): {ADDR}` | | ✅ |
| `Mã số thuế (Tax-code): {MST}` | | ✅ |

### 1.2 Table data section
- **Header row**: row 11-13 (tùy template), bold + fill xanh nhạt + border
- **Data rows**: bắt đầu row 13-15
- **Font**: 100% dùng Times New Roman (chưa thấy ngoại lệ)

### 1.3 Totals block (cuối table)
| Pattern | Có ở | Cách dùng |
|---|---|---|
| `Tổng` row | 23/33 files | SUM cho từng cột số |
| `VAT` row | 17/33 | =Tổng × vat_rate (8% phổ biến) |
| `Tổng cộng / Tổng thanh toán` | 23/33 | =Tổng + VAT |
| `Tổng số tiền bằng chữ` | 13/33 | Vietnamese amount-in-words |
| Section "Phí trả hộ / Thu chi hộ" | 7/33 | Phí thu hộ tách riêng |

### 1.4 Footer (rows cuối)
| Element | Có ở | Nội dung |
|---|---|---|
| Bank info | 18/33 | Techcombank ĐĐ, STK 346886 |
| Signature blocks | 13/33 | KH bên trái, 5P bên phải |

---

## 2. Phân loại — 4 TEMPLATE FAMILY chính

Sau khi cluster, **4 family bao phủ 85% files**:

### **FAMILY A — Trucking nội địa (8 files / 7 customers)**

**Customers**: BÌNH MINH, DONSUNG/K+K, KK, PIPETREE, UPGAIN, UTRACORN, TVC (+ DAINESE TT đã làm)

**Cluster signature**: `hdr=[BKS,PT] feats=[bang_chu|tong|tong_cong|vat]`

**Cấu trúc cột (13-15 cols)**:
| Col | Header | DB source |
|---|---|---|
| A | STT | row index |
| B | Ngày dịch vụ | `js.scheduled_date` |
| C | Type | `js.service_type_code` (DOM/SHORT/LONG) |
| D | Điểm lấy hàng | `js.origin_address` (split city) |
| E | Điểm trả hàng | `js.dest_address` (split city) |
| F | Biển số | `service_details.vehicle_plate` |
| G | Số lượng | `service_details.quantity` |
| H | Đơn vị | `service_details.vehicle_type` |
| I | Đơn giá | job_costs `Cước vận chuyển` selling/qty |
| J | Thành tiền | =I×G formula |
| K | Chi phí khác / Phụ phí xăng dầu | job_costs `Phụ phí xăng dầu` |
| L | Tổng | =SUM(J:K) |
| M | JOB | `j.job_no` |
| N | Ghi chú | `service_details.note` |

**Filter**: `service_type_code LIKE 'TRUCKING_%'`

**Title**: `BẢNG KÊ DỊCH VỤ VẬN CHUYỂN ĐƯỜNG BỘ THÁNG MM/YYYY`

→ **Renderer hiện có ở DAINESE TT có thể tái sử dụng GẦN NGUYÊN VẸN cho cả 7 customer này.**

### **FAMILY B — Dịch vụ làm hàng (handling/customs declaration) (9 files / 7 customers)**

**Customers**: HƯNG PHÁT, VINTECH, XÂY LẮP VN, LOGIMARK, MESSER, GANG THÉP CPN, LAS (similar to DAINESE phi_co)

**Cluster signature**: `hdr=[INV] feats=[bank|tong_cong|vat]` (variants)

**Cấu trúc cột (12-19 cols)**:
| Col | Header | DB source |
|---|---|---|
| A | STT | row index |
| B | Ngày | `j.etd` |
| C | BKS / Loại xe | `service_details.vehicle_plate` / `vehicle_type` |
| D | Nội dung dịch vụ | `cost.cost_name` |
| E | Số lượng | `cost.quantity` |
| F | ĐVT | `cost.unit` |
| G | Đơn giá | `cost.selling_amount/quantity` |
| H | Thành tiền | =F×G |
| I | Tax/VAT | `cost.vat_rate` |
| J | Tổng tiền | =H+(H×I) |
| K | Số HĐ | `j.invoice_number` |
| (variant) Thu hộ | nếu có | reim costs |

**Filter**: thường mọi service-type, hoặc filter theo cost_name

**Title**: `BẢNG KÊ DỊCH VỤ LÀM HÀNG THÁNG MM/YYYY` hoặc `BẢNG KÊ DỊCH VỤ THÁNG MM/YYYY`

→ **1 renderer tổng quát có thể cover cả family này** (đơn giản hơn DAINESE phí CO vì layout cơ bản).

### **FAMILY C — Customs declaration với BKS+TK (Customs handling) (5 files / 3 customers)**

**Customers**: GLOREX (NHAP KHAU + XNK TAI CHO sheets), THÁI HOÀ, GANG THÉP TN

**Cluster signature**: `hdr=[BKS,TK] feats=[tong|tong_cong|vat]`

**Cấu trúc cột (16 cols)**:
```
STT | Ngày | Loại xe | Booking/Bill/BKS | Vận chuyển | Tờ khai |
Nội dung | Đơn vị | Số lượng | Đơn giá | Số tiền | VAT | Tổng tiền | Số GNT | Note
```

**Title**: `BẢNG KÊ THU CHI HỘ LỆ PHÍ HẢI QUAN THÁNG M/YYYY` hoặc tương tự

**Multi-sheet**: thường 2 sheet `NHAP KHAU` + `XNK TAI CHO` (giống DAINESE TC+CPN)

**Filter**: `service_type_code IN ('CUS_*')` + có cd_no

→ **Tái sử dụng được DAINESE tc_cpn renderer với điều chỉnh nhỏ.**

### **FAMILY D — International import/export (Multi-cost matrix) (4 files / 3 customers)**

**Customers**: GLOREX QUỐC TẾ, LKV BD, LKV MB (+ DAINESE nhap_sea_air đã có)

**Cấu trúc**: rộng (16-22 cols), nhiều cột phí chi tiết (mở TK, vận chuyển, làm hàng, THC, CFS, DO, đại lý...) + cột "Phí trả hộ" tách riêng.

**Title**: `BẢNG KÊ DỊCH VỤ LOGISTICS HÀNG NHẬP THÁNG MM/YYYY` hoặc tương tự

**Filter**: `service_type_code IN ('SEA_IMP','SEA_EXP','AIR_IMP','AIR_EXP','BORDER_*')`

→ **Tái sử dụng DAINESE nhap_sea_air renderer**, chỉ cần tham số hóa customer name + một số khác biệt nhỏ.

---

## 3. Khác biệt cần tham số hóa

Sau khi gom 4 family, các thông số cần biến hóa per-customer:

| Param | Nguồn | Ghi chú |
|---|---|---|
| `customer_name` | `customers.company_name` | Đã có |
| `customer_address` | `customers.address` | Đã có |
| `customer_tax_code` | `customers.tax_code` | Đã có |
| `customer_contact` | `customers.contact_name` | Optional |
| `title_prefix` | per-customer config | "BẢNG KÊ ..." |
| `vat_rate` | `service_details.vat_rate` hoặc default 8% | Per-cost |
| `currency` | per-customer | Mặc định VND |
| `signature_block_required` | per-customer | Bool |
| `bank_info_required` | per-customer | Bool |
| `bang_chu_required` | per-customer | Bool |
| `service_types_filter` | per-template-family | Mảng |

---

## 4. Đặc biệt — Customer cần custom code

| Customer | Lý do special |
|---|---|
| **TDI** | 3+ sheets song song (TDI 1, TDI 2, TDI THU CHI HỘ) → cần multi-sheet workbook |
| **DONSUNG / KCVN / NIPPON** (data sheets) | File "Kangatang" — không phải debit note, có vẻ là raw data dump → bỏ qua |
| **KWE** | Data sheet thuần (6 sheet, không có header chuẩn) → custom |
| **MESSER** | Format đặc biệt, khác hẳn debit thường |
| **MEIKO** (đã làm) | 3 sheets: IM + Truck + Debit |
| **DAINESE** (đã làm) | 5 sub-templates riêng |

---

## 5. STRATEGY — Roadmap triển khai (đề xuất)

### Phase 1: **Generic template engine** (cover 85% customers)

Tạo 1 module duy nhất `generic_customer_export_template.py` với:
- Builder pattern: `BangKeBuilder().with_header(...).with_table(...).with_totals(...).build()`
- 4 base templates A/B/C/D (trucking/handling/customs/intl)
- Tham số hóa hết: customer info, title, VAT, bank, sig blocks, columns

Code reuse từ DAINESE renderer:
- `dainese_template_renderer_thanh_toan_truck.py` → Family A base
- `dainese_template_renderer_phi_co.py` → Family B base
- `dainese_template_renderer_tc_cpn.py` → Family C base
- `dainese_template_renderer_nhap_sea_air.py` → Family D base

Tách helpers chung ra `common_bang_ke_styling_and_formatting.py`:
- `_font()`, `_apply_border_to_range()`, `_vn_money_words()`, color constants, NF_INT/NF_DEC, COMPANY_INFO, BANK_INFO

### Phase 2: **Customer registry config** (replace hardcoded templates)

Mở rộng `customer_export_template_registry.py`:
```python
CUSTOMER_TEMPLATES = {
    "BINHMINH":  {"family": "trucking", "title_suffix": "VẬN CHUYỂN ĐƯỜNG BỘ", "service_types": ["TRUCKING_*"]},
    "UPGAIN":    {"family": "trucking", "title_suffix": "VẬN CHUYỂN ĐƯỜNG BỘ", "needs_fuel_surcharge_col": True},
    "GLOREX":    {"family": "customs",  "title_suffix": "THU CHI HỘ LỆ PHÍ HẢI QUAN", "multi_sheet": ["NHAP KHAU", "XNK TAI CHO"]},
    "HUNGPHAT":  {"family": "handling", "title_suffix": "DỊCH VỤ LÀM HÀNG"},
    ...
    "DAINESE":   {"templates": [...]},  # giữ nguyên 5 sub-templates
    "MEIKO":     {"templates": [...]},  # giữ nguyên 3 sheets
}
```

→ **1 bảng config thay vì 22 file Python riêng.**

### Phase 3: **Special-case handling**

Custom renderer riêng cho:
- TDI (multi-sheet output)
- KWE (data dump format)
- MESSER (special)
- TDI BẢNG THEO DÕI (tracking sheet, không phải debit)

### Phase 4: **Frontend integration**

Auto-detect template family từ registry → hiển thị buttons tự động ở SearchBox panel (giống DAINESE 5 buttons hiện tại nhưng generated từ config).

---

## 6. Estimate effort

| Phase | Effort | Risk |
|---|---|---|
| Phase 1 Generic engine + 4 family bases | ~2-3 ngày | Low (đã có DAINESE renderer làm pattern) |
| Phase 2 Customer registry expand | ~1 ngày | Low |
| Phase 3 Special cases (TDI/KWE/MESSER) | ~2 ngày | Medium (cần phân tích kỹ từng file) |
| Phase 4 Frontend wire | ~0.5 ngày | Low |
| **Tổng** | **~5-7 ngày** | |

→ Sau khi xong, **bất kỳ customer nào cũng tạo bảng kê chỉ qua 1 entry trong registry** (trừ 4-5 customer special).

---

## 7. Quick wins (làm trước, ROI cao)

1. **Family A — Trucking** (8 files, 7 customers): tái sử dụng renderer DAINESE TT, chỉ cần map customer code → enable. **Ưu tiên #1**.
2. **Family B — Handling** (9 files, 7 customers): generic renderer mới, cover thêm 7 customer. **Ưu tiên #2**.
3. **Family C/D**: extend DAINESE renderers, customer code map. **Ưu tiên #3**.

---

## 8. Câu hỏi chưa giải

- TDI BẢNG THEO DÕI có phải bảng kê không hay là internal tracking sheet?
- KCVN/DONSUNG/NIPPON Kangatang sheets có cần generate không?
- Các customer chưa có file T3 (e.g. KWE format khác hẳn) có muốn dùng generator không?
- Multi-sheet output: 1 file workbook nhiều sheets vs nhiều file riêng — KH preference?
- Bank info có khác giữa các bảng kê hay luôn cùng (Techcombank ĐĐ STK 346886)?
- Vat rate: 8% phổ biến nhưng có file 0% (Bảng kê CO) → cần config theo loại dịch vụ.
