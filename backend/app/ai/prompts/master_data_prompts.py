"""
SLMS AI Prompts - Master Data Extraction
=========================================

Prompts for extracting customer, vendor, and quotation entities.
"""

CUSTOMER_EXTRACTION_PROMPT = """Bạn là AI assistant trích xuất thông tin khách hàng từ văn bản.

**NHIỆM VỤ:** Trích xuất thông tin khách hàng từ tin nhắn hoặc đăng ký kinh doanh.

══════════════════════════════════════════════════════════════════════════
CÁC TRƯỜNG CẦN TRÍCH XUẤT
══════════════════════════════════════════════════════════════════════════

1. **customer_code** - Mã khách hàng (viết tắt, VD: DRT, SEVT, SAMSUNG)
2. **company_name** - Tên công ty đầy đủ
3. **short_name** - Tên viết tắt/ngắn
4. **tax_code** - Mã số thuế (MST)
5. **address** - Địa chỉ
6. **contact_phone** - Số điện thoại liên hệ
7. **contact_email** - Email liên hệ
8. **contact_person** - Người liên hệ

══════════════════════════════════════════════════════════════════════════
VÍ DỤ TRÍCH XUẤT
══════════════════════════════════════════════════════════════════════════

**Input:** "Tạo khách hàng mới: Công ty TNHH Dreamtech Vietnam, MST 0101234567, KCN Yên Phong, Bắc Ninh"
**Output:**
{{
    "customer_code": "DRT",
    "company_name": "Công ty TNHH Dreamtech Vietnam",
    "short_name": "Dreamtech",
    "tax_code": "0101234567",
    "address": "KCN Yên Phong, Bắc Ninh",
    "confidence": 0.9
}}

**Input:** "thêm KH Samsung SEVT, điện thoại 0912345678, email ops@samsung.com"
**Output:**
{{
    "customer_code": "SEVT",
    "company_name": "Samsung Electronics Vietnam",
    "short_name": "Samsung SEVT",
    "contact_phone": "0912345678",
    "contact_email": "ops@samsung.com",
    "confidence": 0.85
}}

══════════════════════════════════════════════════════════════════════════
QUY TẮC TRÍCH XUẤT
══════════════════════════════════════════════════════════════════════════

1. **customer_code** - Tạo từ viết tắt tên công ty (chữ in hoa, 2-6 ký tự)
2. **tax_code** - 10-14 chữ số, có thể có dấu gạch
3. **address** - Thường chứa: KCN, tỉnh, quận, huyện, TP
4. Nếu thiếu thông tin, để null

══════════════════════════════════════════════════════════════════════════
TIN NHẮN CẦN TRÍCH XUẤT
══════════════════════════════════════════════════════════════════════════

"{input}"

══════════════════════════════════════════════════════════════════════════
OUTPUT (JSON only)
══════════════════════════════════════════════════════════════════════════
"""

VENDOR_EXTRACTION_PROMPT = """Bạn là AI assistant trích xuất thông tin nhà cung cấp từ văn bản.

**NHIỆM VỤ:** Trích xuất thông tin vendor/nhà cung cấp vận tải.

══════════════════════════════════════════════════════════════════════════
CÁC TRƯỜNG CẦN TRÍCH XUẤT
══════════════════════════════════════════════════════════════════════════

1. **vendor_code** - Mã NCC (viết tắt, VD: TAMBAO, THANHCONG)
2. **vendor_name** - Tên công ty đầy đủ
3. **short_name** - Tên viết tắt/ngắn
4. **tax_code** - Mã số thuế (MST)
5. **address** - Địa chỉ
6. **phone** - Số điện thoại
7. **email** - Email

══════════════════════════════════════════════════════════════════════════
VÍ DỤ TRÍCH XUẤT
══════════════════════════════════════════════════════════════════════════

**Input:** "Thêm nhà vận chuyển Tâm Bảo Logistics, SĐT 0987654321"
**Output:**
{{
    "vendor_code": "TAMBAO",
    "vendor_name": "Tâm Bảo Logistics",
    "short_name": "Tâm Bảo",
    "phone": "0987654321",
    "confidence": 0.9
}}

**Input:** "tạo NCC mới: Công ty Vận tải Thành Công, MST 0312345678, Hà Nội"
**Output:**
{{
    "vendor_code": "THANHCONG",
    "vendor_name": "Công ty Vận tải Thành Công",
    "short_name": "Thành Công",
    "tax_code": "0312345678",
    "address": "Hà Nội",
    "confidence": 0.85
}}

══════════════════════════════════════════════════════════════════════════
TIN NHẮN CẦN TRÍCH XUẤT
══════════════════════════════════════════════════════════════════════════

"{input}"

══════════════════════════════════════════════════════════════════════════
OUTPUT (JSON only)
══════════════════════════════════════════════════════════════════════════
"""

QUOTATION_EXTRACTION_PROMPT = """Bạn là AI assistant trích xuất thông tin báo giá vận tải.

**NHIỆM VỤ:** Trích xuất thông tin báo giá mua/bán từ tin nhắn.

══════════════════════════════════════════════════════════════════════════
CÁC TRƯỜNG CẦN TRÍCH XUẤT
══════════════════════════════════════════════════════════════════════════

1. **quote_type** - "buying" (giá mua từ NCC) hoặc "selling" (giá bán cho KH)
2. **vendor_name** - Tên NCC (nếu buying)
3. **customer_name** - Tên khách hàng (nếu selling)
4. **origin_province** - Tỉnh/TP xuất phát (VD: Hà Nội, Bắc Ninh)
5. **destination_province** - Tỉnh/TP đến
6. **sub_route** - Chi tiết tuyến (VD: Nội Bài -> KCN Thăng Long)
7. **vehicle_type** - Loại xe (1.25T, 2.5T, 5T, 10T, CONT20, CONT40)
8. **price** - Giá tiền (số)
9. **currency** - Đơn vị tiền (VND, USD)
10. **unit** - Đơn vị tính (TRIP, KG, CBM, CONT)
11. **service_type** - Loại dịch vụ (TRUCKING, CONTAINER, CUSTOMS, PACKING)
12. **rate_type** - Loại hàng (STANDARD, REFRIGERATED)
13. **notes** - Ghi chú

══════════════════════════════════════════════════════════════════════════
VÍ DỤ TRÍCH XUẤT
══════════════════════════════════════════════════════════════════════════

**Input:** "báo giá mua từ Tâm Bảo: tuyến HN-BN xe 5T = 1,200,000 VND/chuyến"
**Output:**
{{
    "quote_type": "buying",
    "vendor_name": "Tâm Bảo",
    "origin_province": "Hà Nội",
    "destination_province": "Bắc Ninh",
    "vehicle_type": "5T",
    "price": 1200000,
    "currency": "VND",
    "unit": "TRIP",
    "service_type": "TRUCKING",
    "rate_type": "STANDARD",
    "confidence": 0.95
}}

**Input:** "giá bán cho DRT: Nội Bài -> KCN Yên Phong 2.5T: 800k"
**Output:**
{{
    "quote_type": "selling",
    "customer_name": "DRT",
    "origin_province": "Hà Nội",
    "destination_province": "Bắc Ninh",
    "sub_route": "Nội Bài -> KCN Yên Phong",
    "vehicle_type": "2.5T",
    "price": 800000,
    "currency": "VND",
    "unit": "TRIP",
    "service_type": "TRUCKING",
    "rate_type": "STANDARD",
    "confidence": 0.90
}}

**Input:** "bảng giá container 40ft HCM-HN từ vendor ABC: 15,000,000"
**Output:**
{{
    "quote_type": "buying",
    "vendor_name": "ABC",
    "origin_province": "Hồ Chí Minh",
    "destination_province": "Hà Nội",
    "vehicle_type": "CONT40",
    "price": 15000000,
    "currency": "VND",
    "unit": "CONT",
    "service_type": "CONTAINER",
    "rate_type": "STANDARD",
    "confidence": 0.85
}}

══════════════════════════════════════════════════════════════════════════
QUY TẮC TRÍCH XUẤT
══════════════════════════════════════════════════════════════════════════

1. **quote_type**: "buying" nếu có từ: vendor, NCC, mua vào, từ NCC. "selling" nếu có từ: KH, khách, bán ra
2. **price**: Chuyển đổi k/K -> *1000 (800k = 800000), triệu/tr -> *1000000
3. **vehicle_type**: Chuẩn hóa về format XXT (1.25T, 2.5T, 5T, 10T) hoặc CONTXX
4. **origin_province/destination_province**: Chuẩn hóa tên tỉnh (HN -> Hà Nội, BN -> Bắc Ninh, HCM -> Hồ Chí Minh)
5. Nếu không xác định được quote_type, mặc định là "buying"

══════════════════════════════════════════════════════════════════════════
TIN NHẮN CẦN TRÍCH XUẤT
══════════════════════════════════════════════════════════════════════════

"{input}"

══════════════════════════════════════════════════════════════════════════
OUTPUT (JSON only)
══════════════════════════════════════════════════════════════════════════
"""
