# Phase 3: Cải thiện Parser Đọc File Báo Giá

## Context Links
- [Plan tổng](plan.md)
- [Báo cáo so sánh parser](../reports/test-260302-1005-rate-parser-comparison.md)
- [rate_file_upload.py](../../backend/app/api/rate_file_upload.py) — Regex parser + fallback logic
- [rate-sheet-ai-parser.py](../../backend/app/ai/excel/rate-sheet-ai-parser.py) — AI parser

## Tổng quan
- **Ngày**: 2026-03-02
- **Ưu tiên**: P1
- **Trạng thái**: completed
- **Mô tả**: Fix 2 vấn đề: (1) Regex đọc thiếu không phát hiện được, (2) Bỏ qua ghi chú và phụ phí

## Phát hiện quan trọng

### Vấn đề 1: Regex đọc thiếu nhưng hệ thống coi là đủ
- Fallback logic hiện tại (line 283): `if not result.get("parsed_rates"):`
- Chỉ gọi AI khi regex trả về **0 rates** → Nếu regex trả về 30/50 rates, hệ thống KHÔNG biết thiếu 20
- Bằng chứng từ test:
  - `real_ant`: Regex=54, Gemini=56 (thiếu 2)
  - `real_navf`: Regex=7, DeepSeek=10 (thiếu 3 — phụ phí bị bỏ)

### Vấn đề 2: Regex bỏ qua ghi chú và phụ phí hoàn toàn
- `_is_surcharge_row()` (line 79) filter hết dòng chứa: "chờ giờ", "phụ phí", "bốc xếp", "ghi chú"...
- `notes` luôn = `None` (line 176) — regex KHÔNG BAO GIỜ trả notes
- Phụ phí thực tế rất quan trọng: phí chờ giờ, bốc xếp, hủy chuyến — khách hàng cần biết

### Giải pháp đề xuất: Hybrid Confidence-Based

**Cách tiếp cận**: Regex (chính) → Đánh giá confidence → AI bổ sung nếu cần

1. Sau regex, tính tỷ lệ: `confidence = regex_rates / total_data_rows_in_sheet`
2. Nếu confidence < 60%: chạy AI thay thế hoàn toàn
3. Luôn trích xuất phụ phí/ghi chú riêng (regex hoặc AI)

## Yêu cầu

### Chức năng
- Phát hiện khi regex đọc thiếu và tự động gọi AI bổ sung
- Trả về phụ phí (surcharges) và ghi chú (notes) cùng với rates
- Frontend hiển thị surcharges riêng biệt trong preview

### Phi chức năng
- Chi phí AI bổ sung: ~$0.004/file (Gemini) — chấp nhận được
- Thời gian parse tăng thêm 3-10s khi cần AI — chấp nhận được cho upload file

## File liên quan

| File | Hành động | Mô tả |
|------|-----------|-------|
| `backend/app/api/rate_file_upload.py` | **SỬA** | Fix fallback logic, thêm confidence check, trích xuất surcharges |
| `backend/app/ai/excel/rate-sheet-ai-parser.py` | **SỬA** | Sửa prompt để AI cũng trả surcharges |
| `backend/app/core/config.py` | Giữ nguyên | AI_PROVIDER đã cấu hình |

## Kiến trúc

```
Upload Excel
    ↓
Regex Parser (nhanh, miễn phí)
    ↓
Tính confidence = regex_rates / total_data_rows
    ↓
confidence >= 60%?
    ├── CÓ → Dùng kết quả regex
    │         + Trích xuất surcharges từ surcharge rows
    └── KHÔNG → Gọi AI (Gemini) thay thế
                 + AI trả rates + surcharges + notes
    ↓
Trả về: { parsed_rates, surcharges, parse_method, confidence }
```

## Các bước thực hiện

### Bước 1: Thêm trích xuất surcharges trong regex parser

Sửa `_parse_pivot_sheet()` trong `rate_file_upload.py`:
- Thay vì bỏ qua surcharge rows, thu thập chúng riêng
- Trả về `{ rates: [...], surcharges: [...] }`

```python
def _parse_pivot_sheet(df: pd.DataFrame) -> dict:
    rates = []
    surcharges = []
    # ... existing logic ...
    for _, row in df.iterrows():
        if _is_surcharge_row(row.values):
            # Thu thập surcharge thay vì bỏ qua
            text = " | ".join(str(v) for v in row.values if pd.notna(v))
            # Tìm giá trong dòng surcharge
            for vc in vehicle_cols:
                price_val = row.get(vc)
                if pd.notna(price_val):
                    try:
                        price = float(price_val)
                        if price >= 10000:
                            surcharges.append({
                                "description": text.strip(),
                                "vehicle_type": str(vc).strip(),
                                "price": price,
                                "unit": "TRIP",
                            })
                    except (ValueError, TypeError):
                        continue
            continue
        # ... existing rate extraction ...
    return {"rates": rates, "surcharges": surcharges}
```

### Bước 2: Thêm confidence check trong upload endpoint

Sửa `upload_rate_file()` trong `rate_file_upload.py`:

```python
# Sau khi regex parse xong
regex_count = len(result.get("parsed_rates", []))
total_data_rows = sum(info.get("data_rows", 0) for info in result.get("sheet_info", []))

# Tính confidence
confidence = regex_count / max(total_data_rows, 1)

# Nếu regex tìm được ít hơn 60% dòng dữ liệu → gọi AI
if regex_count == 0 or confidence < 0.6:
    # Gọi AI parser (Gemini mặc định — rẻ nhất)
    ai_result = await ai_parser.parse_rates_with_ai(tmp_path, service_type_code)
    if ai_result.get("parsed_rates") and len(ai_result["parsed_rates"]) > regex_count:
        result = ai_result
        result["parse_method"] = "ai"
        result["confidence"] = 1.0
    else:
        result["confidence"] = confidence
        result["parse_method"] = "regex"
else:
    result["confidence"] = confidence
    result["parse_method"] = "regex"
```

### Bước 3: Đếm total_data_rows trong regex parser

Sửa `_find_header_row` và `parse_excel_rates` để trả về tổng số dòng dữ liệu:

```python
# Trong parse_excel_rates, sau khi tìm header:
data_rows_count = len(df)  # Tổng dòng dữ liệu (sau header)
sheet_info.append({
    "sheet": sheet_name,
    "type": "pivot",
    "count": len(rates),
    "data_rows": data_rows_count,  # THÊM MỚI
})
```

### Bước 4: Sửa AI prompt để trả surcharges

Sửa `RATE_EXTRACTION_PROMPT` trong `rate-sheet-ai-parser.py`:
- Bỏ rule "bỏ qua dòng ghi chú, phụ phí"
- Thêm: "Trả phụ phí (chờ giờ, bốc xếp, hủy chuyến...) trong field notes"

```python
RATE_EXTRACTION_PROMPT = """...
Quy tắc:
...
3. Giá phải > 0 và là số thực
4. Với phụ phí (chờ giờ, bốc xếp, hủy chuyến, lưu ca): vẫn trích xuất,
   đặt vào notes là "PHỤ PHÍ: <tên phụ phí>"
5. Ghi chú quan trọng (điều kiện thanh toán, thời gian áp dụng): đặt vào field notes
..."""
```

### Bước 5: Cập nhật RateRow model

Thêm trường `is_surcharge` vào model:
```python
class RateRow(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    vehicle_type: Optional[str] = None
    price: float
    unit: str = "TRIP"
    notes: Optional[str] = None
    is_surcharge: bool = False  # THÊM MỚI
```

## Checklist
- [x] Sửa `_parse_pivot_sheet` trả surcharges riêng
- [x] Thêm đếm `data_rows` trong `parse_excel_rates`
- [x] Thêm confidence check trong `upload_rate_file`
- [x] Sửa AI prompt để trả surcharges và notes
- [x] Thêm `is_surcharge` vào RateRow model
- [x] Test với file `real_ant` (54 rates → phải >= 54)
- [x] Test với file `real_navf` (7 rates + 3 surcharges)
- [x] Test với file customs/packing (phải trả notes)

## Tiêu chí thành công
- Regex + confidence check phát hiện được khi đọc thiếu
- Surcharges/phụ phí được trích xuất (không bỏ qua)
- Notes/ghi chú được trả về cùng rates
- `real_navf`: trả >= 7 rates + phụ phí riêng
- `real_ant`: trả >= 54 rates

## Đánh giá rủi ro
- **Trung bình**: Confidence threshold 60% có thể quá cao/thấp → điều chỉnh sau khi test
- **Thấp**: AI cost thêm ~$0.004/file — không đáng kể cho upload thủ công
- **Thấp**: Surcharges trong regex có thể không parse được giá chính xác → fallback AI

## Bước tiếp theo
- Chạy lại test comparison sau khi fix
- Frontend hiển thị surcharges riêng biệt trong preview modal (nếu cần)
