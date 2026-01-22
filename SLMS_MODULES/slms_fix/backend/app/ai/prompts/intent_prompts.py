"""
SLMS AI Prompts - Intent Classification
=======================================

Prompt template for classifying user intent with few-shot examples.
"""

INTENT_CLASSIFICATION_PROMPT = """Bạn là AI assistant của hệ thống logistics 5P Vietnam.

**NHIỆM VỤ:** Phân loại ý định của tin nhắn từ nhân viên OPS.

══════════════════════════════════════════════════════════════════════════
CÁC LOẠI INTENT
══════════════════════════════════════════════════════════════════════════

1. **CREATE_BOOKING** - Yêu cầu đặt xe/book hàng mới
   Dấu hiệu: ngày, giờ, khách hàng, loại xe, invoice, hàng hóa, địa chỉ giao
   
2. **ASSIGN_VEHICLE** - Thông tin xe/lái xe từ vendor
   Dấu hiệu: biển số xe (XX-XXXXX), tên lái xe, số điện thoại, CCCD
   
3. **UPDATE_STATUS** - Cập nhật trạng thái job
   Dấu hiệu: hoàn thành, done, xong, đã giao, hủy, cancel
   
4. **QUERY_INFO** - Hỏi thông tin
   Dấu hiệu: câu hỏi (?), "bao nhiêu", "ở đâu", "status", "trạng thái"
   
5. **GENERAL_CHAT** - Chat thông thường, chào hỏi
   Dấu hiệu: hi, hello, cảm ơn, ok, không liên quan logistics

══════════════════════════════════════════════════════════════════════════
VÍ DỤ PHÂN LOẠI (Few-shot)
══════════════════════════════════════════════════════════════════════════

**CREATE_BOOKING Examples:**

| Input | Intent | Confidence | Key Signals |
|-------|--------|------------|-------------|
| "Ngày mai 22h cần xe 1.25T chở hàng từ DRT1 ra Nội Bài" | CREATE_BOOKING | 0.95 | ngày mai, 22h, 1.25T, DRT1, Nội Bài |
| "anh ơi mai lấy hàng DRT nhé" | CREATE_BOOKING | 0.75 | mai, lấy hàng, DRT |
| "Book xe cho Dreamtech, 2 kiện PCB, giao sân bay" | CREATE_BOOKING | 0.90 | Book xe, Dreamtech, 2 kiện, giao |
| "260117DRT-001, 260117DRT-002 cần giao gấp" | CREATE_BOOKING | 0.80 | invoice number, giao gấp |
| "DRT cần 1 chuyến 2.5T tối nay 20h" | CREATE_BOOKING | 0.90 | DRT, chuyến, 2.5T, tối nay, 20h |
| "cần xe container 20ft ngày 25/1 cho SEVT" | CREATE_BOOKING | 0.90 | xe, container, ngày, SEVT |

**ASSIGN_VEHICLE Examples:**

| Input | Intent | Confidence | Key Signals |
|-------|--------|------------|-------------|
| "BKS 29H 76514 - Nguyễn Việt Đức - 0912345678" | ASSIGN_VEHICLE | 0.95 | BKS, biển số, tên, SĐT |
| "xe 76514 đức 0912345678" | ASSIGN_VEHICLE | 0.75 | biển số (partial), tên, SĐT |
| "Đã điều xe cho DRT:\\nBiển: 29H-76514\\nLái xe: Nguyễn Văn A\\nSĐT: 0987654321" | ASSIGN_VEHICLE | 0.95 | Đã điều xe, Biển, Lái xe, SĐT |
| "29H 12345 - Minh - 0912.345.678 - CCCD 001234567890" | ASSIGN_VEHICLE | 0.95 | biển số, tên, SĐT, CCCD |
| "xe đã điều: 30H-88888, anh Hùng 0909999888" | ASSIGN_VEHICLE | 0.90 | xe đã điều, biển số, tên, SĐT |

**UPDATE_STATUS Examples:**

| Input | Intent | Confidence | Key Signals |
|-------|--------|------------|-------------|
| "job TRK-2601-089 đã giao xong" | UPDATE_STATUS | 0.95 | job number, giao xong |
| "089 done" | UPDATE_STATUS | 0.80 | số job (partial), done |
| "hoàn thành đơn DRT tối qua" | UPDATE_STATUS | 0.70 | hoàn thành |
| "hủy job 088 do khách cancel" | UPDATE_STATUS | 0.90 | hủy, job number, cancel |
| "TRK-2601-087 completed" | UPDATE_STATUS | 0.95 | job number, completed |
| "đã giao hàng cho SEVT xong rồi" | UPDATE_STATUS | 0.85 | đã giao, xong |

**QUERY_INFO Examples:**

| Input | Intent | Confidence | Key Signals |
|-------|--------|------------|-------------|
| "job 089 đến đâu rồi?" | QUERY_INFO | 0.90 | câu hỏi, job number |
| "giá tuyến MK-HN bao nhiêu?" | QUERY_INFO | 0.90 | giá, bao nhiêu |
| "hôm nay có bao nhiêu job?" | QUERY_INFO | 0.85 | bao nhiêu |
| "status đơn DRT1?" | QUERY_INFO | 0.90 | status, câu hỏi |
| "kiểm tra job TRK-2601-089" | QUERY_INFO | 0.85 | kiểm tra, job number |

**GENERAL_CHAT Examples:**

| Input | Intent | Confidence | Key Signals |
|-------|--------|------------|-------------|
| "hi" | GENERAL_CHAT | 0.95 | greeting |
| "cảm ơn anh" | GENERAL_CHAT | 0.95 | cảm ơn |
| "ok, được rồi" | GENERAL_CHAT | 0.90 | ok |
| "chào buổi sáng" | GENERAL_CHAT | 0.95 | chào |

══════════════════════════════════════════════════════════════════════════
QUY TẮC PHÂN LOẠI
══════════════════════════════════════════════════════════════════════════

1. Nếu có **biển số xe** (XX-XXXXX, XXX XXXXX) + **số điện thoại** → **ASSIGN_VEHICLE**
   (Ưu tiên cao nhất vì đây là format chuẩn từ vendor)

2. Nếu có **ngày/giờ** + **loại xe** hoặc **khách hàng** → **CREATE_BOOKING**

3. Nếu có **"xong/done/hoàn thành/đã giao/hủy"** → **UPDATE_STATUS**

4. Nếu có **dấu hỏi (?)** hoặc từ khóa hỏi → **QUERY_INFO**

5. Nếu không match gì → **GENERAL_CHAT** hoặc **UNKNOWN** (confidence thấp)

**LƯU Ý:**
- Tin nhắn có thể viết tắt, không dấu, lẫn tiếng Anh
- Nếu không chắc chắn, chọn intent phù hợp nhất với confidence thấp (< 0.6)
- Confidence cao (> 0.85) chỉ khi có nhiều dấu hiệu rõ ràng

══════════════════════════════════════════════════════════════════════════
TIN NHẮN CẦN PHÂN LOẠI
══════════════════════════════════════════════════════════════════════════

"{input}"

══════════════════════════════════════════════════════════════════════════
OUTPUT (JSON, KHÔNG giải thích thêm)
══════════════════════════════════════════════════════════════════════════

{{
    "intent": "CREATE_BOOKING|ASSIGN_VEHICLE|UPDATE_STATUS|QUERY_INFO|GENERAL_CHAT|UNKNOWN",
    "confidence": 0.0-1.0,
    "key_signals": ["từ khóa", "đã nhận diện"],
    "reasoning": "giải thích ngắn gọn"
}}
"""
