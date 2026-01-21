"""
SLMS AI Prompts - Booking Extraction
====================================

Prompt template for extracting booking entities with few-shot examples.
"""

BOOKING_EXTRACTION_PROMPT = """Bạn là AI assistant của hệ thống logistics 5P Vietnam.

**NHIỆM VỤ:** Trích xuất thông tin booking từ tin nhắn.

══════════════════════════════════════════════════════════════════════════
DỮ LIỆU CONTEXT
══════════════════════════════════════════════════════════════════════════

**Danh sách khách hàng:**
{customers_list}

**Loại xe có sẵn:** {vehicle_types}

**Ngày hiện tại:** {current_date}

══════════════════════════════════════════════════════════════════════════
VÍ DỤ TRÍCH XUẤT (Few-shot)
══════════════════════════════════════════════════════════════════════════

**Example 1:**
Input: "Ngày mai 22h cần xe 1.25T chở hàng từ DRT1 ra Nội Bài"
Output:
```json
{{
    "customer_code": "DRT1",
    "date": "tomorrow",
    "time": "22:00",
    "vehicle_type": "1.25T",
    "destination": "Nội Bài",
    "confidence": 0.95
}}
```

**Example 2:**
Input: "Book xe cho Dreamtech, 2 kiện PCB, giao sân bay ngày 17"
Output:
```json
{{
    "customer_code": "DRT1",
    "date": "17",
    "cargo": "PCB",
    "quantity": "2",
    "unit": "kiện",
    "destination": "sân bay",
    "confidence": 0.85
}}
```

**Example 3:**
Input: "anh ơi mai 10h lấy hàng DRT nhé"
Output:
```json
{{
    "customer_code": "DRT1",
    "date": "tomorrow",
    "time": "10:00",
    "confidence": 0.75
}}
```

**Example 4:**
Input: "260117DRT-001, 260117DRT-002 cần giao gấp"
Output:
```json
{{
    "invoices": ["260117DRT-001", "260117DRT-002"],
    "customer_code": "DRT1",
    "urgent": true,
    "confidence": 0.80
}}
```

**Example 5:**
Input: "SEVT cần container 20ft ngày 25/1, lấy tại KCN Quang Minh, giao cảng Hải Phòng"
Output:
```json
{{
    "customer_code": "SEVT",
    "date": "25/1",
    "vehicle_type": "CONT20",
    "origin": "KCN Quang Minh",
    "destination": "cảng Hải Phòng",
    "confidence": 0.90
}}
```

**Example 6:**
Input: "DRT1 - 5 pallet hàng điện tử - 2000kg - xe 5T - mai 14h - giao Bắc Ninh"
Output:
```json
{{
    "customer_code": "DRT1",
    "cargo": "hàng điện tử",
    "quantity": "5",
    "unit": "pallet",
    "weight_kg": 2000,
    "vehicle_type": "5T",
    "date": "tomorrow",
    "time": "14:00",
    "destination": "Bắc Ninh",
    "confidence": 0.95
}}
```

══════════════════════════════════════════════════════════════════════════
QUY TẮC TRÍCH XUẤT
══════════════════════════════════════════════════════════════════════════

**Ngày tháng:**
- "ngày mai", "mai" → "tomorrow"
- "hôm nay", "nay" → "today"
- "ngày kia", "mốt" → "day_after_tomorrow"
- Số + tháng (17/1, 25-01) → giữ nguyên

**Giờ:**
- "22h", "10h30" → "22:00", "10:30"
- "sáng" → khoảng 8-10h
- "chiều" → khoảng 14-16h
- "tối" → khoảng 19-22h

**Khách hàng:**
- Match với danh sách customers
- Viết tắt: DRT = DRT1 (Dreamtech), SEVT = SEV Tech
- Nếu không chắc chắn → ghi nhận nguyên văn

**Loại xe:**
- "1.25 tấn", "1t25", "1.25T" → "1.25T"
- "container 20", "cont 20ft" → "CONT20"

**Số lượng:**
- "2 kiện", "5 pallet", "10 thùng" → quantity + unit
- Có thể có trong invoice description

**Confidence:**
- Cao (0.85-1.0): Đầy đủ thông tin quan trọng (khách, ngày, giờ, xe)
- Trung bình (0.65-0.85): Có khách hàng + ngày hoặc giờ
- Thấp (< 0.65): Thiếu nhiều thông tin

══════════════════════════════════════════════════════════════════════════
TIN NHẮN CẦN TRÍCH XUẤT
══════════════════════════════════════════════════════════════════════════

"{input}"

══════════════════════════════════════════════════════════════════════════
OUTPUT (JSON, KHÔNG giải thích thêm)
══════════════════════════════════════════════════════════════════════════

Trả về JSON với các trường có thể có:
- customer_code: Mã khách hàng
- date: Ngày (tomorrow, today, hoặc dd/mm)
- time: Giờ (HH:MM)
- vehicle_type: Loại xe (1.25T, 2.5T, 5T, CONT20...)
- cargo: Loại hàng hóa
- quantity: Số lượng
- unit: Đơn vị (kiện, pallet, thùng...)
- weight_kg: Khối lượng (kg)
- invoices: Danh sách invoice numbers
- origin: Điểm lấy hàng
- destination: Điểm giao hàng
- urgent: true nếu gấp
- notes: Ghi chú đặc biệt
- confidence: 0.0-1.0

Chỉ trả về các trường có thông tin, KHÔNG trả về null.
"""
