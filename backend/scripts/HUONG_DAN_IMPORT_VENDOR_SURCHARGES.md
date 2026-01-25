# Hướng dẫn Import Vendor Surcharges lên Supabase

## Bước 1: Tạo lại bảng vendor_surcharges

Do bảng vendor_surcharges hiện tại không có cột `amount`, bạn cần tạo lại bảng với cấu trúc đúng.

### Cách 1: Chạy SQL trên Supabase Dashboard (Khuyến nghị)

1. Truy cập: https://app.supabase.com/project/vpmsytbbsxmtdicnkytv
2. Vào **SQL Editor**
3. Copy nội dung file `create_vendor_surcharges_table.sql` và chạy

Nội dung SQL:
```sql
-- =============================================================================
-- TẠO LẠI BẢNG VENDOR_SURCHARGES VỚI CẤU TRÚC ĐÚNG
-- =============================================================================

-- Xóa bảng phụ thuộc trước (nếu có)
DROP TABLE IF EXISTS public.vendor_surcharge_prices CASCADE;

-- Xóa bảng vendor_surcharges cũ nếu tồn tại
DROP TABLE IF EXISTS public.vendor_surcharges CASCADE;

-- Tạo lại bảng vendor_surcharges với cấu trúc đúng
CREATE TABLE public.vendor_surcharges (
    id SERIAL PRIMARY KEY,
    vendor_id INTEGER NOT NULL REFERENCES vendors(vendor_id) ON DELETE CASCADE,
    surcharge_code VARCHAR(50) NOT NULL,
    description TEXT,
    amount DECIMAL(18,2),
    unit VARCHAR(20),
    conditions TEXT,
    effective_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index
CREATE INDEX idx_vendor_surcharges_vendor_id ON public.vendor_surcharges(vendor_id);
CREATE INDEX idx_vendor_surcharges_surcharge_code ON public.vendor_surcharges(surcharge_code);

-- Comment
COMMENT ON TABLE public.vendor_surcharges IS 'Bảng phụ phí của nhà vận chuyển';
```

### Cách 2: Sử dụng psql client

Nếu bạn đã cài đặt psql:

```bash
psql "postgresql://postgres.vpmsytbbsxmtdicnkytv:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres" -f create_vendor_surcharges_table.sql
```

## Bước 2: Chạy script import vendor_surcharges

Sau khi đã tạo lại bảng vendor_surcharges, chạy script import:

```bash
cd backend/scripts
python import_vendor_surcharges.py vendor_rates/Tam_bảo_092025.xlsx "Tam Bảo"
```

Nếu file Excel ở thư mục khác, hãy thay đổi đường dẫn tương ứng.

## Bước 3: Kiểm tra kết quả

Sau khi chạy script, kiểm tra dữ liệu trên Supabase:

1. Vào **Table Editor**
2. Chọn bảng `vendor_surcharges`
3. Kiểm tra số lượng records

Kết quả mong đợi:
- Khoảng 26 surcharge records (17 từ "Phụ Phí Cửa Khẩu Xe Thường" + 9 từ "Phụ Phí Cửa Kh Xe Lạnh")

## Cấu trúc bảng vendor_surcharges

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| vendor_id | INTEGER | Foreign key đến vendors |
| surcharge_code | VARCHAR(50) | Mã phụ phí (e.g. PHI_CAU_DUONG) |
| description | TEXT | Mô tả chi tiết |
| amount | DECIMAL(18,2) | Số tiền (VND) |
| unit | VARCHAR(20) | Đơn vị tính (lượt, km, giờ, ngày) |
| conditions | TEXT | Điều kiện áp dụng |
| effective_date | DATE | Ngày hiệu lực |
| created_at | TIMESTAMP | Thời gian tạo |
| updated_at | TIMESTAMP | Thời gian cập nhật |

## Lỗi thường gặp

### Lỗi: column "amount" does not exist

**Nguyên nhân**: Bảng vendor_surcharges cũ không có cột `amount`

**Giải pháp**: Chạy lại SQL để tạo lại bảng (Bước 1)

### Lỗi: vendor not found

**Nguyên nhân**: Vendor "Tam Bảo" không tồn tại trong database

**Giải pháp**: Chạy script `create_tambao_vendor.py` để tạo vendor

```bash
cd backend/scripts
python create_tambao_vendor.py
```

### Lỗi: AI không khả dụng

**Nguyên nhân**: GOOGLE_GEMINI_API_KEY không được cấu hình

**Giải pháp**: Thêm API key vào file `.env`

```env
GOOGLE_GEMINI_API_KEY=your_api_key_here
```

## Tổng kết quy trình import

1. ✅ Import customers (52 records) - Hoàn tất
2. ✅ Import vendors (88 records) - Hoàn tất
3. ✅ Import drivers (145 records) - Hoàn tất
4. ✅ Import vendor_rates (242 records) - Hoàn tất
5. ⏳ Import vendor_surcharges (đang thực hiện)
6. ⏸️ Kiểm tra và xác nhận dữ liệu đã import
