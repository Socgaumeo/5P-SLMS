# 🔧 HƯỚNG DẪN FIX AI PIPELINE - SLMS
## Các lỗi đã tìm thấy và cách khắc phục

**Ngày tạo:** 21/01/2026

---

## 🔴 VẤN ĐỀ ĐÃ TÌM THẤY

### 1. THIẾU METHOD `_extract_json` (CRITICAL)

**File:** `backend/app/ai/entity_extractor.py`

**Vấn đề:** Line 216 gọi `self._extract_json(response)` nhưng method **KHÔNG TỒN TẠI** trong class!

```python
# Line 212-219 trong file cũ:
def _parse_booking_response(self, response: Any, context: Dict) -> Dict:
    if isinstance(response, str):
        response = self._extract_json(response)  # ← METHOD NÀY KHÔNG TỒN TẠI!
    ...
```

**Hậu quả:**
- Khi AI trả về string thay vì dict → CRASH hoặc return empty
- Entity extraction FAIL
- Kết quả "lung tung"

---

### 2. JSON PARSING KHÔNG ROBUST

**File:** `backend/app/ai/gemini_client.py`

**Vấn đề:** `_parse_json` chỉ handle một số format cơ bản:

```python
# File cũ chỉ có:
def _parse_json(self, text: str) -> Dict[str, Any]:
    if "```json" in clean_text:
        clean_text = clean_text.split("```json")[1].split("```")[0]
    # Không handle: trailing commas, comments, nested structures
```

**Hậu quả:**
- AI trả về `{"intent": "CREATE_BOOKING",}` (trailing comma) → FAIL
- AI trả về `// comment\n{"intent": ...}` → FAIL

---

### 3. CONFIDENCE EXTRACTION SAI

**File:** `backend/app/ai/entity_extractor.py`

**Vấn đề:**
```python
# Line 115:
confidence = response.get("confidence", 0.7) if isinstance(response, dict) else 0.7
```

Nếu `_extract_json` fail → `response` vẫn là string → `confidence = 0.7` LUÔN
→ Không phản ánh đúng độ tin cậy của AI

---

### 4. ENCODING ISSUES (UTF-8)

**File:** `backend/app/ai/context_loader.py`

**Vấn đề:** Các ký tự tiếng Việt bị lỗi encoding:
```python
# Thấy trong file:
"KhÃ´ng cÃ³ dá»¯ liá»‡u khÃ¡ch hÃ ng"
# Thay vì:
"Không có dữ liệu khách hàng"
```

**Hậu quả:**
- Context trong prompt bị lỗi
- AI không hiểu đúng context

---

### 5. DUPLICATE AI PROCESSING LAYERS

**Files:** `ai_service.py` + `chat.py`

**Vấn đề:**
- `chat.py` có `ocr_and_extract()` xử lý image riêng
- `ai_service.py` wrap `pipeline.py`
- Hai layer có thể conflict

---

## ✅ CÁCH FIX

### Bước 1: Replace các files đã fix

Copy các file sau vào project:

```
backend/app/ai/
├── entity_extractor.py    ← THAY THẾ
├── context_loader.py      ← THAY THẾ
├── gemini_client.py       ← THAY THẾ

backend/app/services/
├── ai_service.py          ← THAY THẾ
```

### Bước 2: Kiểm tra encoding files

Đảm bảo tất cả files Python có encoding UTF-8:
```bash
# Check encoding
file -i backend/app/ai/*.py

# Nếu thấy không phải utf-8, convert:
iconv -f ISO-8859-1 -t UTF-8 old_file.py > new_file.py
```

### Bước 3: Test với logging

Bật logging DEBUG để theo dõi:

```python
# Thêm vào backend/main.py
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Bước 4: Restart server và test

```bash
# Stop và start lại
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🧪 TEST CASES

Test các input sau để verify fix hoạt động:

### Test 1: CREATE_BOOKING
```
Input: "Ngày mai 22h cần xe 1.25T cho DRT1"
Expected:
- intent: CREATE_JOB
- confidence: > 0.8
- entities: {customer_code: "DRT1", booking_date: "2026-01-22", pickup_time: "22:00", vehicle_type: "1.25T"}
```

### Test 2: ASSIGN_VEHICLE
```
Input: "BKS 29H 76514 - Nguyễn Văn A - 0912345678"
Expected:
- intent: ASSIGN_VEHICLE
- confidence: > 0.9
- entities: {license_plate: "29H 76514", driver_name: "Nguyễn Văn A", driver_phone: "0912345678"}
```

### Test 3: UPDATE_STATUS
```
Input: "job 089 đã giao xong"
Expected:
- intent: UPDATE_JOB
- confidence: > 0.8
- entities: {job_number: "089" hoặc full job_no, new_status: "COMPLETED"}
```

### Test 4: Input không chuẩn
```
Input: "anh ơi mai lấy hàng DRT nhé"
Expected:
- intent: CREATE_JOB
- confidence: 0.6-0.8 (lower vì thiếu thông tin)
- entities: {customer_code: "DRT1", booking_date: "tomorrow"}
```

---

## 📊 LOGGING ĐỂ DEBUG

Sau khi fix, log sẽ hiển thị:

```
[EntityExtractor] Starting extraction for intent: create_booking
[EntityExtractor] Input text: Ngày mai 22h cần xe 1.25T cho DRT1...
[EntityExtractor] Customers in context: 15
[EntityExtractor] Calling AI for booking extraction...
[GeminiClient] Generating with format: json, temp: 0.2
[GeminiClient] Raw response length: 234
[GeminiClient] Raw response preview: {"customer_code": "DRT1", ...
[GeminiClient] Direct JSON parse succeeded
[EntityExtractor] Booking extracted: ['customer_code', 'booking_date', 'pickup_time', 'vehicle_type'], confidence: 0.95
```

Nếu có lỗi:
```
[EntityExtractor] Failed to parse AI response to dict
[GeminiClient] JSON parse error after cleaning: ...
[GeminiClient] All JSON parsing strategies failed
```

---

## 🔍 CHECKLIST SAU KHI FIX

- [ ] Copy 4 files đã fix vào project
- [ ] Kiểm tra encoding UTF-8
- [ ] Restart server
- [ ] Test với các test cases
- [ ] Kiểm tra logs không còn lỗi JSON parsing
- [ ] Verify confidence phản ánh đúng (không phải luôn 0.7)
- [ ] Verify entities được extract đúng

---

## ⚠️ LƯU Ý QUAN TRỌNG

1. **Backup trước khi thay đổi:**
   ```bash
   cp -r backend/app/ai backend/app/ai_backup
   cp backend/app/services/ai_service.py backend/app/services/ai_service_backup.py
   ```

2. **Nếu vẫn còn lỗi sau khi fix:**
   - Kiểm tra GOOGLE_GEMINI_API_KEY trong .env
   - Kiểm tra database connection
   - Kiểm tra tables customers, jobs, vendors có data không

3. **Chi phí AI không đổi:**
   - Fix này không thêm API calls
   - Chỉ cải thiện parsing response
