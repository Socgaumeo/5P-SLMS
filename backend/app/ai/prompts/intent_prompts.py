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

4. **UPDATE_JOB** - Sửa thông tin job (đổi khách hàng, thêm dịch vụ, sửa địa chỉ, ghi chú, phí phát sinh, chi phí, doanh thu)
   Dấu hiệu: đổi khách, sửa job, thay đổi KH, thêm dịch vụ, sửa địa chỉ, chuyển khách, ghi chú, yêu cầu, chờ hàng, phí chờ, phí huỷ, chi phí, doanh thu, định mức, giá mua, giá bán

4. **QUERY_INFO** - Hỏi thông tin
   Dấu hiệu: câu hỏi (?), "bao nhiêu", "ở đâu", "status", "trạng thái"

5. **CREATE_CUSTOMER** - Thêm khách hàng mới
   Dấu hiệu: tạo khách hàng, thêm KH, đăng ký kinh doanh, MST/mã số thuế, công ty mới, tên công ty

6. **CREATE_VENDOR** - Thêm nhà cung cấp mới
   Dấu hiệu: tạo NCC, thêm vendor, nhà vận chuyển mới, đối tác vận tải

7. **CREATE_QUOTATION** - Tạo báo giá mua/bán
   Dấu hiệu: báo giá, quotation, giá cước, giá vận chuyển, bảng giá, giá mua, giá bán, tuyến đường

8. **GENERAL_CHAT** - Chat thông thường, chào hỏi
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

**UPDATE_JOB Examples:**

| Input | Intent | Confidence | Key Signals |
|-------|--------|------------|-------------|
| "đổi khách hàng job TRK-2601-089 sang DRT2" | UPDATE_JOB | 0.95 | đổi khách hàng, job number, khách mới |
| "job 089 sửa lại khách thành Dreamtech" | UPDATE_JOB | 0.90 | sửa, khách, job number |
| "thêm 1 dịch vụ trucking cho job 085" | UPDATE_JOB | 0.90 | thêm dịch vụ, job number |
| "chuyển đơn DRT sang SEVT" | UPDATE_JOB | 0.85 | chuyển đơn, khách hàng |
| "sửa địa chỉ giao hàng job 087" | UPDATE_JOB | 0.85 | sửa địa chỉ, job number |
| "job 089 đổi KH sang LKV Miền Bắc" | UPDATE_JOB | 0.90 | đổi KH, job number |
| "khách yêu cầu không xếp chồng job TRK-0402-0002" | UPDATE_JOB | 0.90 | yêu cầu, ghi chú, job number |
| "chờ hàng từ 8h đến 12h TRK-0402-0002" | UPDATE_JOB | 0.85 | chờ hàng, thời gian, job number |
| "phí chờ giờ 500k job 089" | UPDATE_JOB | 0.90 | phí chờ, job number |
| "thêm phí huỷ chuyến 300k cho job 087" | UPDATE_JOB | 0.90 | phí huỷ, job number |
| "chi phí job 089 là 800k từ Tâm Bảo" | UPDATE_JOB | 0.90 | chi phí, job number, số tiền, vendor |
| "doanh thu job 089 là 1.5 triệu" | UPDATE_JOB | 0.90 | doanh thu, job number, số tiền |
| "job 085 chi phí 900k doanh thu 1.3 triệu" | UPDATE_JOB | 0.95 | chi phí, doanh thu, job number |
| "áp dụng định mức HN-BN xe 5T cho job 090" | UPDATE_JOB | 0.85 | định mức, tuyến, xe, job number |
| "giá mua vào job 092 theo NCC ABC" | UPDATE_JOB | 0.85 | giá mua, job number, NCC |

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

**CREATE_CUSTOMER Examples:**

| Input | Intent | Confidence | Key Signals |
|-------|--------|------------|-------------|
| "tạo khách hàng mới: Công ty ABC, MST 0123456789" | CREATE_CUSTOMER | 0.95 | tạo khách hàng, công ty, MST |
| "thêm KH Dreamtech VN, địa chỉ KCN Bắc Ninh" | CREATE_CUSTOMER | 0.90 | thêm KH, địa chỉ |
| "đăng ký kinh doanh công ty XYZ" | CREATE_CUSTOMER | 0.85 | đăng ký kinh doanh |
| "Công ty TNHH Samsung SEVT, MST: 0312345678, ĐC: KCN Yên Phong" | CREATE_CUSTOMER | 0.95 | công ty, MST, địa chỉ |

**CREATE_VENDOR Examples:**

| Input | Intent | Confidence | Key Signals |
|-------|--------|------------|-------------|
| "thêm nhà vận chuyển Tâm Bảo Logistics" | CREATE_VENDOR | 0.95 | thêm, nhà vận chuyển |
| "tạo NCC mới: Công ty Vận tải ABC" | CREATE_VENDOR | 0.90 | tạo NCC, vận tải |
| "thêm vendor đối tác Thành Công Express, SĐT 0912345678" | CREATE_VENDOR | 0.95 | thêm vendor, đối tác |

**CREATE_QUOTATION Examples:**

| Input | Intent | Confidence | Key Signals |
|-------|--------|------------|-------------|
| "báo giá tuyến HN-BN xe 5T: 1,200,000 VND/chuyến" | CREATE_QUOTATION | 0.95 | báo giá, tuyến, giá |
| "giá cước từ vendor Tâm Bảo: Hà Nội - Bắc Ninh 2.5T: 800k" | CREATE_QUOTATION | 0.95 | giá cước, vendor |
| "tạo giá bán cho khách DRT: tuyến Nội Bài-Bắc Ninh 1.25T = 600,000" | CREATE_QUOTATION | 0.90 | tạo giá bán, khách |
| "bảng giá mua vào từ NCC ABC" | CREATE_QUOTATION | 0.85 | bảng giá, mua vào, NCC |
| "cập nhật giá tuyến HN-HCM xe 10T" | CREATE_QUOTATION | 0.80 | giá, tuyến, xe |

══════════════════════════════════════════════════════════════════════════
QUY TẮC PHÂN LOẠI
══════════════════════════════════════════════════════════════════════════

1. Nếu có **biển số xe** (XX-XXXXX, XXX XXXXX) + **số điện thoại** → **ASSIGN_VEHICLE**
   (Ưu tiên cao nhất vì đây là format chuẩn từ vendor)

2. Nếu có **ngày/giờ** + **loại xe** hoặc **khách hàng** booking → **CREATE_BOOKING**

3. Nếu có **"xong/done/hoàn thành/đã giao/hủy"** → **UPDATE_STATUS**

4. Nếu có **"đổi khách/sửa job/thay đổi KH/thêm dịch vụ/sửa địa chỉ/ghi chú/yêu cầu/chờ hàng/phí chờ/phí huỷ/chi phí/doanh thu/định mức/giá mua"** + **job number** → **UPDATE_JOB**

5. Nếu có **dấu hỏi (?)** hoặc từ khóa hỏi → **QUERY_INFO**

5. Nếu có **"tạo khách hàng/thêm KH/đăng ký kinh doanh/công ty mới"** + **MST/địa chỉ** → **CREATE_CUSTOMER**

6. Nếu có **"thêm NCC/vendor/nhà vận chuyển/đối tác vận tải"** → **CREATE_VENDOR**

7. Nếu có **"báo giá/giá cước/bảng giá/giá mua/giá bán"** + **tuyến/giá tiền** → **CREATE_QUOTATION**

8. Nếu không match gì → **GENERAL_CHAT** hoặc **UNKNOWN** (confidence thấp)

**LƯU Ý:**
- Tin nhắn có thể viết tắt, không dấu, lẫn tiếng Anh
- Nếu không chắc chắn, chọn intent phù hợp nhất với confidence thấp (< 0.6)
- Confidence cao (> 0.85) chỉ khi có nhiều dấu hiệu rõ ràng
- Khi có thông tin công ty với MST, ưu tiên **CREATE_CUSTOMER** hơn **CREATE_BOOKING**

══════════════════════════════════════════════════════════════════════════
TIN NHẮN CẦN PHÂN LOẠI
══════════════════════════════════════════════════════════════════════════

"{input}"

══════════════════════════════════════════════════════════════════════════
OUTPUT (JSON, KHÔNG giải thích thêm)
══════════════════════════════════════════════════════════════════════════

{{
    "intent": "CREATE_BOOKING|ASSIGN_VEHICLE|UPDATE_STATUS|UPDATE_JOB|QUERY_INFO|CREATE_CUSTOMER|CREATE_VENDOR|CREATE_QUOTATION|GENERAL_CHAT|UNKNOWN",
    "confidence": 0.0-1.0,
    "key_signals": ["từ khóa", "đã nhận diện"],
    "reasoning": "giải thích ngắn gọn"
}}
"""
