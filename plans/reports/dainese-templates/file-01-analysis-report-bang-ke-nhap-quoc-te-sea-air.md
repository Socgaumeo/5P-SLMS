# Phân tích File 1: `Bảng kê nhập tháng 3.2026.sea.air.xlsx`

**Loại bảng kê:** Bảng kê chi tiết hàng nhập quốc tế (SEA + AIR)
**Khách hàng:** Công ty TNHH Dainese Việt Nam
**Tháng:** 03/2026
**Số dòng dữ liệu thực:** 16 jobs (rows 13-28)

---

## 1. Tổng quan workbook

| Sheet | Vai trò | Range thực | Ghi chú |
|---|---|---|---|
| `NHẬP` | Bảng kê chính trình bày cho KH | 44 rows × 30 cols (A..AD) | Có logo, header công ty, header KH, table data, totals, info chuyển khoản |
| `Sheet1` | Sheet phụ (legacy mapping) | 27 rows × 11 cols | Có vẻ là mapping fields cũ (S_OF, S_THC, S_CFSO…) - **bỏ qua, không cần generate** |

---

## 2. Layout sheet `NHẬP` (sheet chính)

### 2.1 Header công ty (rows 1-4)
- **Logo:** 1 image (anchor khoảng B1:B4) - file `5P star logo` xanh-cam
- `C1`: `CÔNG TY TNHH THƯƠNG MẠI VÀ DỊCH VỤ 5P VIỆT NAM` — Times New Roman 12pt Bold
- `C2`: Address — `Số nhà 02 Ngõ 1H Phố Trần Quang Diệu, Phường Đống Đa, Thành phố Hà Nội, Việt Nam`
- `C3`: `MST: 0110523309`
- Row heights: r1-r4 = 23pt, r5 = 67pt

### 2.2 Title row (row 5, merged A5:AD5)
- Text: `BẢNG KÊ CHI TIẾT HÀNG NHẬP QUỐC TẾ THÁNG 02 NĂM 2026`
- Font: **Times New Roman 26pt Bold, center**
- Row height: 67pt

### 2.3 Recipient block (rows 7-9)
- `B7`: `KÍNH GỬI :  CÔNG TY TNHH DAINESE VIỆT NAM` (TNR 14pt Bold)
- `B8`: `Địa chỉ : Lô CN13, Lô CN18, Khu Công nghiệp Yên Bình, Phường Vạn Xuân, Tỉnh T...`
- `B9`: `Attn:   Ms. Phương Anh - Ms. Dương`

### 2.4 Table headers (rows 11-12, hai dòng header)

**Row 11 — group headers (merged):**
| Range | Label |
|---|---|
| A11:G11 | Thông tin chung |
| H11:I11 | Khổi lượng (sic - "Khối") |
| J11:J12 | Note |
| K11:V11 | Phí dịch vụ làm hàng (VND) |
| W11:Z11 | Phí trả hộ |
| AA11:AA12 | Tổng tiền phải trả |
| AB11:AB12 | Số hóa đơn trả hộ |
| AC11:AD12 | Số hóa đơn của forwarder |

**Row 12 — column headers:**
| Col | Header |
|---|---|
| A | No. |
| B | Tờ khai |
| C | Hóa đơn thương mại |
| D | Vận đơn/Note |
| E | Ngày tờ khai |
| F | Tuyến đường |
| G | Loại hình vận chuyển (SEA/AIR) |
| H | Kgs |
| I | No. Cont (LCL/20'GP/AIR) |
| K | Phí mở tờ khai hải quan |
| L | Phí kiểm hóa |
| M | Phí vận chuyển |
| N | Phí làm hàng |
| O | Phí phát sinh khác |
| P | Phí đầu nước ngoài |
| Q | Cước vận tải quốc tế |
| R | Phí xếp dỡ (THC) |
| S | Phí gom hàng lẻ (CFS)/CIC/LSS |
| T | Phí lấy lệnh (DO) |
| U | Phí đại lý |
| **V** | **Tổng** (formula `=SUM(K:U)`) |
| W | Local charge |
| X | CSHT, thuế, vé bãi |
| Y | Lưu kho giao nhận bốc xếp, nâng hạ |
| **Z** | **Tổng phí trả hộ** (formula `=SUM(W:Y)`) |
| **AA** | **Tổng tiền phải trả** (formula `=V+Z`) |
| AB | Số hóa đơn trả hộ |
| AC | Số hóa đơn của forwarder |
| AD | (extra số hóa đơn) |

**Style rows 11-12:**
- Font Times New Roman 10-12pt **Bold Italic**, center+wrap
- Number format: `_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)`

### 2.5 Data rows (rows 13-28, 16 jobs)
- Font: **Times New Roman 10pt Bold**
- All cells **center+wrap**, **with thin border**
- Có cell có background fill (zebra/highlight rows)
- Date format: `mm-dd-yy` hoặc `d-mmm`
- Number format: `#,##0.00` cho fees, `#,##0` cho totals

### 2.6 Totals (rows 29-31)
- `A29:J29` merged label `Tổng` (TNR 12pt Bold Italic, center wrap)
- `K29..AA29`: `=SUM(K13:K28)` cho từng cột (formula tự động cộng)
- `A30:J30` merged label `VAT` — hiện tại data row VAT toàn = 0 (KH này không xuất VAT?)
- `A31:J31` merged — likely "Tổng cộng" với `=SUM(K29:K30)` cho mỗi cột (same SUM pattern repeated row 31)

### 2.7 Footer (rows 41-44) — Thông tin chuyển khoản
- `A41`: `Thông tin chuyển khoản:`
- `A42`: `Tài khoản: Công Ty TNHH Thương mại và dịch vụ 5P Việt Nam`
- `A43`: `Số tài khoản: 346886`
- `A44:F44` merged: `Tại Ngân hàng: Ngân hàng TMCP Kỹ thương Việt Nam - Techcombank Chi nhánh Đông...`
- Font: TNR 12pt (không bold), wrap

---

## 3. Column widths chuẩn (sheet NHẬP)

```
A=5.4   B=13.6  C=19.6  D=19.9  E=16.6  F=26.3  G=11.4
H=13.5  I=9.5   J=18.5  K=15.3  L=14.5  M=16.4  N=15.2
O=14.2  P=18.8  Q=17.9  R=13.7  S=12.6  T=13.8  U=11.0
V=15.7  W=12.5  X=11.5  Y=20.4  Z=15.7  AA=18.5 AB=21.8
AC=8.2  AD=8.0
```

---

## 4. Công thức Excel (chính xác)

| Cell | Formula | Mục đích |
|---|---|---|
| `V{r}` | `=SUM(K{r}:U{r})` | Tổng phí dịch vụ làm hàng (per row) |
| `Z{r}` | `=SUM(W{r}:Y{r})` | Tổng phí trả hộ (per row) |
| `AA{r}` | `=+V{r}+Z{r}` | Tổng tiền phải trả (per row) |
| Row 29 (Tổng) | `=SUM(K13:K28)` mỗi cột K..AA | Tổng cộng theo cột |
| Row 31 | `=SUM(K29:K30)` mỗi cột | Sum row 29 + row 30 (Tổng + VAT) |

---

## 5. Style summary

| Element | Font | Size | Style | Align |
|---|---|---|---|---|
| Company name C1 | Times New Roman | 12 | Bold | Left |
| Title A5 | Times New Roman | **26** | Bold | Center+Center |
| Recipient B7-9 | Times New Roman | 14 | Bold | Left |
| Group headers row 11 | Times New Roman | 12 | Bold Italic | Center+Center+Wrap |
| Column headers row 12 | Times New Roman | 10 | Bold | Center+Center+Wrap |
| Data rows | Times New Roman | 10 | Bold | Center+Center+Wrap |
| Totals labels | Times New Roman | 12 | Bold Italic | Center+Wrap |
| Footer info | Times New Roman | 12 | Regular | Left+Wrap |

**Borders:** Thin border quanh tất cả cells trong table (rows 11-31, A:AD).

**Background fill:** Data rows có pattern fill nhẹ để zebra (cần check kỹ hơn — thấy `bg#'str'>` trong style summary nhưng RGB bị truncate).

---

## 6. Dữ liệu mẫu (rows 13-14)

```
Row 13:
  No=1, Tờ khai=108021404521, HĐTM=2025S0217, Vận đơn=2025CA0000102644
  Ngày=05/03/2026, Tuyến=Genoa, Italy - Thái Nguyên, Loại=SEA, Kgs=5890, Cont=LCL
  Phí mở TK=943,830, Vận chuyển=4,561,845, Làm hàng=4,089,930, PS khác=849,447
  Đầu NN=19,568,742, Cước QT=60,216,354, THC=20,462,234, DO=1,258,440
  Tổng V=111,950,822, X=94,240, Y=13,013,670, Z=13,107,910, AA=125,058,732
  HĐ trả hộ=2985, 1148965, HĐ FWD=152, 183, 184

Row 14:
  Tương tự, có công thức =1153600+44550 trong Y14 (KH ghi gộp 2 phí)
```

---

## 7. Mapping với schema 5P-SLMS

Phân tích cột → field DB:

| Excel col | Mapped DB field | Source table |
|---|---|---|
| Tờ khai | `service_details.cd_no` | `job_services` |
| HĐ thương mại | `job.invoice_number` hoặc `service_details.commercial_invoice` | `jobs` / JSONB |
| Vận đơn | `service_details.bill_of_lading` / `note` | JSONB |
| Ngày tờ khai | `service_details.cd_date` hoặc `service.scheduled_date` | |
| Tuyến đường | `service.origin_address → dest_address` | `job_services` |
| SEA/AIR | `service.service_type_code` (SEA_FCL/SEA_LCL/AIR…) | `job_services` |
| Kgs | `service_details.weight_kg` | JSONB |
| Cont | `service_details.container_size` | JSONB |
| Phí mở TK | `service_details.fee_declaration` (cost+revenue split) | JSONB |
| Vận chuyển | `service_details.fee_transport` | JSONB |
| Local charges | `vendor_surcharges` rows | `vendor_surcharges` |
| Cước QT | `service_details.fee_international` | JSONB |
| THC | `vendor_surcharges` (THC code) | |

---

## 8. Quirks / điểm cần lưu ý khi generate

1. **Title hiện ghi "THÁNG 02"** dù file là tháng 3 → KH có lỗi, mình generate dynamic theo tháng.
2. **Sheet1 là legacy mapping**, không cần generate.
3. **Logo 5P** là PNG transparent, kích thước nhỏ — embed vào A1.
4. **VAT row hiện = 0** cho mọi cell → có thể KH này không tính VAT trực tiếp ở bảng kê này (tính riêng ở bảng kê CO/TT).
5. **Có cells dùng formula inline `=1153600+44550`** thay vì giá trị đơn — giữ nguyên cách: nếu data có 2 nguồn cộng lại thì tạo formula, nếu không thì set giá trị.
6. **Cột D "Vận đơn/Note"** đôi khi chứa "Note" tự do (như `Elantas`, `EGI PROJECT`).
7. **Background fill** rows data (zebra) cần xác nhận màu cụ thể qua RGB - **cần đọc lại sâu hơn** ở phase implement.
8. **Có 13 merged ranges** ở row 11 (group headers), rows 29/30/31 (label Tổng/VAT), row 5 (title), row 44 (bank info).

---

## 9. Câu hỏi chưa giải

- [ ] Background fill RGB chính xác (parser bị truncate `#'str'>`)? → Cần check trực tiếp
- [ ] Row 31 có phải `=SUM(row29+row30)` hay phải tính khác? → Cần verify với KH
- [ ] Cách identify SEA vs AIR từ DB hiện tại (có service_type_code nào)?
- [ ] Cột AC vs AD vốn là 1 group `Số hóa đơn của forwarder` merged AC11:AD12 — tại sao tách 2 cột? Có phải 1 cột hóa đơn, 1 cột số series?
- [ ] DAINESE có customer_code chính xác là gì trong DB?
