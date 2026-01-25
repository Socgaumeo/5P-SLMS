# Hướng dẫn Import Dữ liệu lên Supabase

## Tổng quan

Dự án có các script để import dữ liệu từ các file SQL và Excel lên Supabase:

1. **import_to_supabase.py** - Import customers, vendors, drivers từ file SQL
2. **import_vendor_rates_supabase.py** - Import vendor rates và vendor surcharges từ Excel

## Cấu hình

Đảm bảo file `.env` đã được cấu hình với các thông tin Supabase:

```env
SUPABASE_URL=https://vpmsytbbsxmtdicnkytv.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
GOOGLE_GEMINI_API_KEY=AIzaSyAVIKiaMnRNOGw9_Vn9bWYJxz4knHYxBrI
```

## Script 1: Import Customers, Vendors, Drivers

### Chạy import tất cả

```bash
cd backend
python scripts/import_to_supabase.py
```

### Chạy từng loại riêng lẻ

Script sẽ tự động import theo thứ tự:
1. **Customers** - Từ file `import_kh_ncc.sql`
2. **Vendors** - Từ file `import_kh_ncc.sql`
3. **Drivers** - Từ file `import_drivers_tambao.sql`
4. **Vendor Rates** - Từ file SQL (nếu có)
5. **Vendor Surcharges** - Từ file SQL (nếu có)

### Kết quả

Script sẽ hiển thị:
- Số lượng records đã import thành công
- Số lượng records thất bại
- Chi tiết lỗi (nếu có)

## Script 2: Import Vendor Rates & Surcharges từ Excel

### Cú pháp

```bash
cd backend
python scripts/import_vendor_rates_supabase.py <file_path> [vendor_name]
```

### Ví dụ

Import rates cho vendor Tam Bảo:

```bash
python scripts/import_vendor_rates_supabase.py ../vendor_rates/Tam_bảo_092025.xlsx "Tam Bảo"
```

### Chức năng

Script sẽ:
1. Đọc file Excel
2. Sử dụng AI (Gemini) để parse dữ liệu từ Excel
3. Import rates cho từng sheet (trừ sheet phụ phí)
4. Import surcharges từ các sheet có tên chứa "Phụ Phí" hoặc "Phụ phí"
5. Tự động tạo routes trong bảng `master_routes` nếu chưa tồn tại
6. Update hoặc insert rates/surcharges tùy theo dữ liệu đã tồn tại

### Cấu trúc Excel

File Excel nên có các sheet:
- **Sheet rates**: Chứa thông tin về giá vận chuyển
  - Điểm đi, Điểm đến
  - Loại xe (1.25T, 1.5T, 2.5T, 3.5T, 5T, 8T, 15T)
  - Giá (VND)
  - Mã giá (TB18, TB20, TB25, v.v.)

- **Sheet phụ phí**: Chứa thông tin về các loại phụ phí
  - Loại phụ phí (Phí cầu đường, Phí bến bãi, Phí chờ, v.v.)
  - Số tiền
  - Đơn vị tính
  - Điều kiện áp dụng

## Các bảng dữ liệu

### Customers

Bảng chứa thông tin khách hàng:
- `customer_code` - Mã khách hàng (unique)
- `company_name` - Tên công ty
- `short_name` - Tên viết tắt
- `tax_code` - Mã số thuế
- `address` - Địa chỉ
- `province` - Tỉnh/Thành phố
- `contact_name` - Người liên hệ
- `contact_phone` - Số điện thoại
- `contact_zalo` - Zalo
- `contact_email` - Email
- `payment_terms` - Điều kiện thanh toán (ngày)
- `credit_limit` - Hạn mức tín dụng
- `notes` - Ghi chú
- `is_active` - Trạng thái hoạt động

### Vendors

Bảng chứa thông tin nhà cung cấp:
- `vendor_code` - Mã nhà cung cấp (unique)
- `company_name` - Tên công ty
- `short_name` - Tên viết tắt
- `tax_code` - Mã số thuế
- `address` - Địa chỉ
- `province` - Tỉnh/Thành phố
- `vendor_type` - Loại nhà cung cấp (LOGISTICS, TRUCKING, v.v.)
- `contact_name` - Người liên hệ
- `contact_phone` - Số điện thoại
- `telegram_chat_id` - Telegram Chat ID
- `bank_name` - Tên ngân hàng
- `bank_account` - Số tài khoản
- `payment_terms` - Điều kiện thanh toán (ngày)
- `notes` - Ghi chú
- `is_active` - Trạng thái hoạt động

### Drivers

Bảng chứa thông tin lái xe:
- `driver_code` - Mã lái xe (unique)
- `employee_id` - Mã nhân viên
- `full_name` - Họ và tên
- `phone` - Số điện thoại
- `id_card` - Số CCCD/CMND
- `id_card_date` - Ngày cấp CCCD
- `id_card_place` - Nơi cấp CCCD
- `date_of_birth` - Ngày sinh
- `address` - Địa chỉ
- `vendor_id` - ID nhà cung cấp (foreign key)
- `license_plate` - Biển số xe
- `vehicle_type` - Loại xe
- `is_active` - Trạng thái hoạt động
- `notes` - Ghi chú

### Vendor Rates

Bảng chứa thông tin giá vận chuyển của nhà cung cấp:
- `vendor_id` - ID nhà cung cấp (foreign key)
- `route_id` - ID tuyến đường (foreign key)
- `vehicle_type` - Loại xe
- `price` - Giá (VND)
- `rate_code` - Mã giá
- `rate_type` - Loại giá (STANDARD, REFRIGERATED)
- `temperature_range` - Phạm vi nhiệt độ (cho xe lạnh)
- `origin_province` - Tỉnh đi
- `destination_province` - Tỉnh đến
- `effective_date` - Ngày hiệu lực
- `notes` - Ghi chú

### Vendor Surcharges

Bảng chứa thông tin phụ phí của nhà cung cấp:
- `vendor_id` - ID nhà cung cấp (foreign key)
- `surcharge_type` - Loại phụ phí
- `description` - Mô tả
- `amount` - Số tiền
- `unit` - Đơn vị tính (lượt, km, giờ, ngày)
- `conditions` - Điều kiện áp dụng
- `effective_date` - Ngày hiệu lực
- `notes` - Ghi chú

### Master Routes

Bảng chứa thông tin tuyến đường:
- `route_id` - ID tuyến đường (primary key)
- `route_code` - Mã tuyến đường (unique)
- `origin` - Điểm đi
- `destination` - Điểm đến
- `distance_km` - Khoảng cách (km)
- `travel_time_hours` - Thời gian di chuyển (giờ)
- `description` - Mô tả
- `is_active` - Trạng thái hoạt động

## Xử lý lỗi

### Lỗi kết nối Supabase

Nếu gặp lỗi kết nối, kiểm tra:
1. SUPABASE_URL và SUPABASE_SERVICE_ROLE_KEY trong `.env`
2. Kết nối internet
3. Quyền truy cập của service role key

### Lỗi parse SQL

Nếu gặp lỗi khi parse SQL:
1. Kiểm tra định dạng file SQL
2. Đảm bảo các câu INSERT đúng cú pháp
3. Kiểm tra encoding file (nên là UTF-8)

### Lỗi parse Excel với AI

Nếu gặp lỗi khi parse Excel:
1. Kiểm tra GOOGLE_GEMINI_API_KEY trong `.env`
2. Kiểm tra định dạng file Excel
3. Xem file debug được tạo (nếu có)

## Debug

### Xem log chi tiết

Script sẽ hiển thị log chi tiết trong quá trình import. Nếu cần debug thêm, có thể thêm print statements vào code.

### File debug

Khi parse Excel với AI gặp lỗi, script sẽ tạo file debug:
- `debug_STANDARD.txt` - Debug cho rates thường
- `debug_REFREGERATED.txt` - Debug cho rates lạnh

## Lưu ý quan trọng

1. **Thứ tự import**: Import theo thứ tự customers → vendors → drivers → rates → surcharges để đảm bảo các foreign key được tạo đúng.
2. **Backup**: Luôn backup dữ liệu trước khi import.
3. **Test**: Test trên môi trường development trước khi import vào production.
4. **AI Parsing**: AI parsing có thể không chính xác 100%, hãy kiểm tra lại dữ liệu sau khi import.
5. **Duplicate**: Script sẽ tự động update nếu record đã tồn tại, không tạo duplicate.

## Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra log chi tiết
2. Xem file debug (nếu có)
3. Kiểm tra cấu hình `.env`
4. Liên hệ team phát triển
