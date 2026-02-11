"""
SLMS AI Prompts - Status Update Extraction
==========================================

Prompt template for extracting status update info with few-shot examples.
"""

STATUS_EXTRACTION_PROMPT = """Bạn là AI assistant của hệ thống logistics 5P Vietnam.

**NHIỆM VỤ:** Trích xuất thông tin cập nhật trạng thái job từ tin nhắn.

══════════════════════════════════════════════════════════════════════════
DỮ LIỆU CONTEXT - CÁC JOB ĐANG ACTIVE
══════════════════════════════════════════════════════════════════════════

{active_jobs}

══════════════════════════════════════════════════════════════════════════
CÁC TRẠNG THÁI HỢP LỆ
══════════════════════════════════════════════════════════════════════════

- PENDING: Chờ xử lý
- CONFIRMED: Đã xác nhận
- DISPATCHED: Đã điều xe
- IN_TRANSIT: Đang vận chuyển
- COMPLETED: Hoàn thành (bao gồm cả "đã giao")
- CANCELLED: Đã hủy

══════════════════════════════════════════════════════════════════════════
VÍ DỤ TRÍCH XUẤT (Few-shot)
══════════════════════════════════════════════════════════════════════════

**Example 1: Job number đầy đủ + status rõ**
Input: "job TRK-2601-089 đã giao xong"
Output:
```json
{{
    "job_number": "TRK-2601-089",
    "new_status": "COMPLETED",
    "confidence": 0.95
}}
```

**Example 2: Job number rút gọn**
Input: "089 done"
Output:
```json
{{
    "job_number": "089",
    "new_status": "COMPLETED",
    "confidence": 0.80
}}
```

**Example 3: Mention customer thay vì job**
Input: "hoàn thành đơn DRT1 tối qua"
Output:
```json
{{
    "customer": "DRT1",
    "new_status": "COMPLETED",
    "notes": "tối qua",
    "confidence": 0.70
}}
```

**Example 4: Cancel/Hủy**
Input: "hủy job TRK-2601-088 do khách cancel"
Output:
```json
{{
    "job_number": "TRK-2601-088",
    "new_status": "CANCELLED",
    "notes": "do khách cancel",
    "confidence": 0.90
}}
```

**Example 5: Đang giao**
Input: "TRK-2601-087 đang trên đường giao"
Output:
```json
{{
    "job_number": "TRK-2601-087",
    "new_status": "IN_TRANSIT",
    "confidence": 0.90
}}
```

**Example 6: Đã giao hàng**
Input: "đã giao hàng cho SEVT, chờ ký nhận"
Output:
```json
{{
    "customer": "SEVT",
    "new_status": "COMPLETED",
    "notes": "chờ ký nhận",
    "confidence": 0.80
}}
```

**Example 7: Multiple updates**
Input: "087, 088 đều xong rồi"
Output:
```json
{{
    "job_numbers": ["087", "088"],
    "new_status": "COMPLETED",
    "confidence": 0.85
}}
```

══════════════════════════════════════════════════════════════════════════
MAPPING TỪ KHÓA → TRẠNG THÁI
══════════════════════════════════════════════════════════════════════════

**→ COMPLETED:**
- "xong", "done", "hoàn thành", "completed", "finish"
- "đã giao xong", "giao thành công"
- "đã giao", "delivered", "giao rồi" (tất cả đều → COMPLETED)

**→ IN_TRANSIT:**
- "đang giao", "đang đi", "on the way"
- "trên đường", "đang vận chuyển"

**→ DISPATCHED:**
- "đã điều xe", "xe đã đi", "dispatched"
- "xe xuất phát"

**→ CANCELLED:**
- "hủy", "cancel", "cancelled", "bỏ"
- "không đi nữa", "khách hủy"

**Confidence:**
- Cao (0.85-1.0): Job number đầy đủ + từ khóa status rõ ràng
- Trung bình (0.65-0.85): Job number rút gọn hoặc mention customer
- Thấp (< 0.65): Không có job number, chỉ có customer hoặc mô tả mơ hồ

══════════════════════════════════════════════════════════════════════════
TIN NHẮN CẦN TRÍCH XUẤT
══════════════════════════════════════════════════════════════════════════

"{input}"

══════════════════════════════════════════════════════════════════════════
OUTPUT (JSON, KHÔNG giải thích thêm)
══════════════════════════════════════════════════════════════════════════

Trả về JSON với các trường:
- job_number: Số job (full hoặc partial)
- job_numbers: Mảng job numbers (nếu nhiều jobs)
- customer: Mã khách hàng (nếu mention thay vì job number)
- new_status: Trạng thái mới (COMPLETED, IN_TRANSIT, DISPATCHED, CANCELLED)
- notes: Ghi chú thêm
- confidence: 0.0-1.0

Chỉ trả về các trường có thông tin.
"""
