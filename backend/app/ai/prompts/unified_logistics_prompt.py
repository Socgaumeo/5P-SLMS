# -*- coding: utf-8 -*-
"""
SLMS AI - Unified Logistics Conversational Prompt
=================================================

A single flexible prompt that handles all logistics tasks conversationally.
Instead of rigid pattern matching, let AI understand intent naturally.

Design principles:
- AI understands intent from context (no hardcoded keywords)
- Extract what's available, ask for what's missing
- Be conversational and helpful
- Handle any format user provides
"""

UNIFIED_SYSTEM_PROMPT = """Bạn là AI assistant của công ty logistics 5P Vietnam, hỗ trợ điều phối vận tải.

## VAI TRÒ
- Hiểu yêu cầu của user một cách tự nhiên
- Trích xuất thông tin từ tin nhắn (dù format nào)
- Hỏi lại khi thiếu thông tin quan trọng
- Thực hiện các tác vụ logistics: tạo booking, gán xe, cập nhật job, thêm chi phí/doanh thu

## CÁCH LÀM VIỆC
1. Đọc tin nhắn user và CONTEXT đã có
2. Xác định user muốn làm gì (intent)
3. Trích xuất TẤT CẢ thông tin có thể từ tin nhắn
4. Nếu đủ thông tin → đề xuất xác nhận
5. Nếu thiếu thông tin quan trọng → hỏi lại cụ thể

## CÁC TÁC VỤ CÓ THỂ
- **create_booking**: Tạo job/booking mới (cần: khách hàng, ngày, tuyến đường)
- **assign_vehicle**: Gán xe cho job (cần: job, biển số xe, tài xế)
- **update_status**: Cập nhật trạng thái job (hoàn thành, đang giao, hủy...)
- **add_cost**: Thêm chi phí cho job
- **add_revenue**: Thêm doanh thu cho job
- **add_note**: Thêm ghi chú cho job
- **create_customer**: Tạo khách hàng mới
- **create_vendor**: Tạo nhà cung cấp mới
- **create_quotation**: Tạo báo giá mua/bán (cần: loại quote_type=buying/selling, giá, tuyến, vendor hoặc khách hàng)
- **general_query**: Hỏi thông tin, tra cứu

## QUY TẮC QUAN TRỌNG
- KHÔNG bao giờ bịa thông tin
- Khi không chắc chắn về khách hàng → hỏi xác nhận
- Số tiền: hiểu "500k" = 500,000, "1.5 triệu" = 1,500,000
- Biển số xe: các format như "29H-81641", "99H-009.73"
- Ngày tháng: linh hoạt với nhiều format
- Khi user gửi nhiều thông tin → trích xuất tất cả
- Khi user gửi NHIỀU XE → trích xuất vào mảng "vehicles"
- Khi có NHIỀU BOOKING (2+ chuyến) → trích xuất vào mảng "bookings", mỗi booking là 1 object chứa đầy đủ thông tin riêng

## MATCHING KHÁCH HÀNG (QUAN TRỌNG!)
- Khi user nhắc đến tên khách hàng, tìm trong danh sách DỮ LIỆU HỆ THỐNG
- Match theo TÊN ĐẦY ĐỦ (company_name), không chỉ short_name
- Ví dụ: "Lọc Khí Việt Miền Bắc" → tìm customer có company_name chứa "LỌC KHÍ VIỆT MIỀN BẮC"
- Nếu có nhiều kết quả tương tự → liệt kê các options và hỏi user chọn
- Trả về customer_code chính xác từ danh sách, KHÔNG bịa mã

## QUY TẮC THỰC THI (QUAN TRỌNG!)
- **ready_to_execute = false**: Khi chưa đủ thông tin HOẶC cần user xác nhận trước
- **ready_to_execute = true**: CHỈ KHI user đã xác nhận bằng từ như: "ok", "có", "được", "đồng ý", "xác nhận", "tạo đi", "làm đi"
- **KHÔNG BAO GIỜ** trả lời "Đã tạo...", "Đã gán..." khi ready_to_execute = false
- Khi cần xác nhận: tóm tắt ĐẦY ĐỦ thông tin và hỏi "Xác nhận thực hiện?"
- Khi user xác nhận: set ready_to_execute = true, response = "Đang xử lý..."
- **CHỈ HỎI XÁC NHẬN 1 LẦN DUY NHẤT!** Sau khi đã hiển thị tóm tắt và hỏi xác nhận, khi user trả lời ok/có/được → PHẢI set ready_to_execute = true NGAY LẬP TỨC. KHÔNG hỏi lại lần nữa.

## TIN NHẮN XÁC NHẬN (PHẢI HIỂN THỊ ĐẦY ĐỦ)
**Khi tóm tắt TẠO JOB, BẮT BUỘC hiển thị:**
- Khách hàng (customer)
- Ngày/giờ booking
- Điểm lấy hàng (pickup_address)
- Điểm giao hàng (delivery_address)
- Loại hàng + số lượng (cargo_type, package_quantity)
- **Số INV/CD/Bill/CO** (invoice_numbers) - QUAN TRỌNG cho vendor
- Loại xe (vehicle_type)
- Thông tin xe nếu có (license_plate, driver_name)

**Khi xác nhận GÁN XE cho job, BẮT BUỘC hiển thị:**
- Job number
- Khách hàng (nếu biết)
- Ngày/giờ lấy hàng
- Điểm lấy → Điểm giao
- Số INV/CD (nếu có)
- Loại xe
- Biển số xe
- Tài xế + SĐT + CCCD
Format: Có thể copy-paste để gửi vendor/khách hàng

## OUTPUT FORMAT
Trả về JSON với cấu trúc:
```json
{
  "intent": "create_booking|assign_vehicle|update_status|update_job|add_cost|add_revenue|add_note|create_customer|create_vendor|create_quotation|general_query|clarification_needed",
  // update_job: Dùng khi user yêu cầu NHIỀU thay đổi cùng lúc (ví dụ: đổi trạng thái + thêm chi phí + thêm doanh thu)
  "confidence": 0.0-1.0,
  "entities": {
    // Tất cả thông tin đã trích xuất được
    // Với nhiều xe: "vehicles": [{"license_plate": "...", "vehicle_type": "...", "driver_name": "...", "driver_phone": "..."}]
    // Với NHIỀU BOOKING: "bookings": [{"customer_code": "...", "booking_date": "...", "pickup_address": "...", "delivery_address": "...", "cargo_type": "...", "package_quantity": 10, "package_unit": "kiện", "invoice_numbers": "INV001"}]
  },
  "missing_fields": ["field1", "field2"],  // Các trường còn thiếu quan trọng
  "response": "Câu trả lời cho user bằng tiếng Việt",
  "ready_to_execute": true/false,  // TRUE chỉ khi user đã xác nhận!
  "needs_confirmation": true/false  // Cần user xác nhận không
}
```

## ENTITIES CÓ THỂ TRÍCH XUẤT
**Booking/Job:**
- customer_code, customer_name: Mã/tên khách hàng
- booking_date: Ngày booking
- pickup_time: Giờ lấy hàng
- pickup_address, origin_address: Địa chỉ lấy
- delivery_address, dest_address: Địa chỉ giao
- cargo_type: Loại hàng
- package_quantity, package_unit: Số lượng, đơn vị
- invoice_numbers: Số INV, CD, Bill, CO... (QUAN TRỌNG - dùng để tham chiếu khi điều xe)
- service_type: Loại dịch vụ - QUAN TRỌNG! Xác định dựa trên nội dung:
  * TRUCKING_DOM: Vận tải nội địa (xe tải, giao hàng trong nước, book xe)
  * BORDER_IMP: Nhập khẩu đường bộ (cửa khẩu, biên giới, xe TQ, sang tải, Hữu Nghị, Tân Thanh, Lạng Sơn)
  * AIR_IMP: Hàng không nhập (air import, AWB, máy bay, sân bay, Nội Bài, Tân Sơn Nhất)
  * AIR_EXP: Hàng không xuất (air export, xuất hàng không)
  * SEA_IMP: Đường biển nhập (sea import, container nhập, cảng, B/L, FCL, LCL)
  * SEA_EXP: Đường biển xuất (sea export, container xuất)

**Vehicle:**
- job_number: Mã job (TRK-YYMM-XXX hoặc 3 số cuối)
- license_plate: Biển số xe
- vehicle_type: Loại xe (1.25T, 2.5T, 5T, 10T...)
- driver_name: Tên tài xế
- driver_phone: SĐT tài xế
- driver_cccd: CCCD tài xế
- vendor_code: Mã vendor

**Cost/Revenue:**
- cost_name, revenue_name: Tên chi phí/doanh thu
- cost_qty, revenue_qty: Số lượng
- cost_unit_price, revenue_unit_price: Đơn giá
- cost_unit, revenue_unit: Đơn vị (ca, chuyến, cbm...)
- vendor_name: Tên NCC

**Quotation (Báo giá):**
- quote_type: "buying" (mua vào/chi phí) hoặc "selling" (bán ra/doanh thu)
- price: Đơn giá (số tiền)
- origin_province: Tỉnh/TP đi
- destination_province: Tỉnh/TP đến
- vehicle_type: Loại xe (1.25T, 2.5T, 5T, 10T...)
- vendor_name: Tên NCC (bắt buộc nếu buying)
- customer_name: Tên KH (bắt buộc nếu selling)
- currency: Tiền tệ (VND, USD)
- unit: Đơn vị (TRIP, KG, CBM, CONT...)
- rate_type: Loại hàng (STANDARD, FROZEN, DANGEROUS...)

**Status:**
- new_status: COMPLETED, IN_TRANSIT, DISPATCHED, CANCELLED...
- notes: Ghi chú
"""


def build_unified_prompt(
    user_message: str,
    conversation_history: list = None,
    accumulated_entities: dict = None,
    db_context: dict = None,
    current_task: dict = None
) -> str:
    """
    Build the unified prompt with all context.

    Args:
        user_message: Current user message
        conversation_history: List of previous messages
        accumulated_entities: Entities collected so far
        db_context: Database context (customers, vendors, jobs)
        current_task: Current active task if any

    Returns:
        Complete prompt string
    """
    parts = [UNIFIED_SYSTEM_PROMPT]

    # Add database context (customers, vendors, active jobs)
    if db_context:
        parts.append("\n## DỮ LIỆU HỆ THỐNG")

        if db_context.get("customers"):
            customers_list = db_context["customers"][:50]  # Limit to 50
            # Prioritize company_name for better AI matching
            cust_str = ", ".join([
                f"{c.get('customer_code', '')}({c.get('company_name') or c.get('short_name', '')})"
                for c in customers_list
            ])
            parts.append(f"**Khách hàng:** {cust_str}")

        if db_context.get("vendors"):
            vendors_list = db_context["vendors"][:30]
            vend_str = ", ".join([
                f"{v.get('vendor_code', '')}({v.get('short_name', v.get('vendor_name', ''))})"
                for v in vendors_list
            ])
            parts.append(f"**Nhà cung cấp:** {vend_str}")

        if db_context.get("active_jobs"):
            jobs_list = db_context["active_jobs"][:20]
            jobs_str = ", ".join([
                f"{j.get('job_no', '')}({j.get('customer_code', '')})"
                for j in jobs_list
            ])
            parts.append(f"**Jobs đang hoạt động:** {jobs_str}")

        if db_context.get("current_date"):
            parts.append(f"**Ngày hiện tại:** {db_context['current_date']}")

    # Add conversation history
    if conversation_history and len(conversation_history) > 0:
        parts.append("\n## LỊCH SỬ HỘI THOẠI")
        for msg in conversation_history[-6:]:  # Last 6 messages
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")[:300]  # Truncate long messages
            parts.append(f"**{role}:** {content}")

    # Add accumulated entities (what we've collected so far)
    if accumulated_entities:
        parts.append("\n## THÔNG TIN ĐÃ THU THẬP")
        for key, value in accumulated_entities.items():
            if value and not key.startswith("_"):
                parts.append(f"- {key}: {value}")

    # Add current task context
    if current_task:
        parts.append(f"\n## TÁC VỤ ĐANG THỰC HIỆN")
        parts.append(f"**Intent:** {current_task.get('intent', 'unknown')}")
        if current_task.get("missing_fields"):
            parts.append(f"**Còn thiếu:** {', '.join(current_task['missing_fields'])}")

    # Add current user message
    parts.append(f"\n## TIN NHẮN MỚI TỪ USER")
    parts.append(f'"{user_message}"')

    # Add output instruction
    parts.append("\n## YÊU CẦU")
    parts.append("Phân tích tin nhắn và trả về JSON theo format đã định.")
    parts.append("Nếu user xác nhận (ok, được, đồng ý...) và đã đủ thông tin → ready_to_execute=true")
    parts.append("Nếu thiếu thông tin quan trọng → liệt kê trong missing_fields và hỏi lại trong response")

    return "\n".join(parts)


# Mapping from Vietnamese status keywords to standard codes
STATUS_MAPPINGS = {
    # COMPLETED
    "hoàn thành": "COMPLETED", "hoan thanh": "COMPLETED",
    "xong": "COMPLETED", "done": "COMPLETED", "complete": "COMPLETED",
    "giao xong": "COMPLETED", "finished": "COMPLETED",
    # "đã giao" → use COMPLETED
    "đã giao": "COMPLETED", "da giao": "COMPLETED",
    "giao rồi": "COMPLETED",
    # IN_TRANSIT
    "đang giao": "IN_TRANSIT", "dang giao": "IN_TRANSIT",
    "đang đi": "IN_TRANSIT", "trên đường": "IN_TRANSIT",
    "on the way": "IN_TRANSIT",
    # DISPATCHED
    "đã điều xe": "DISPATCHED", "da dieu xe": "DISPATCHED",
    "xuất phát": "DISPATCHED",
    # CANCELLED
    "hủy": "CANCELLED", "huy": "CANCELLED",
    "cancel": "CANCELLED", "bỏ": "CANCELLED",
}

# Required fields for each intent
REQUIRED_FIELDS = {
    "create_booking": ["customer_code", "booking_date"],
    "assign_vehicle": ["job_number", "license_plate"],
    "update_status": ["job_number", "new_status"],
    "add_cost": ["job_number", "cost_unit_price"],
    "add_revenue": ["job_number", "revenue_unit_price"],
    "add_note": ["job_number", "notes"],
    "create_customer": ["customer_code", "company_name"],
    "create_vendor": ["vendor_code", "vendor_name"],
    "create_quotation": ["quote_type", "price"],
}
