#!/bin/bash
# Script tạo bảng vendor_surcharges trên Supabase sử dụng Supabase Management API
# Lưu ý: Cần có Supabase access token

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Kiểm tra biến môi trường
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo "❌ SUPABASE_URL và SUPABASE_SERVICE_ROLE_KEY phải được cấu hình trong .env"
    exit 1
fi

# URL cho Supabase SQL Editor API
# Lưu ý: Supabase không cung cấp public API để thực thi SQL trực tiếp
# Bạn cần thực hiện thủ công trên Supabase Dashboard

echo "============================================================================="
echo "HƯỚNG DẪN TẠO BẢNG VENDOR_SURCHARGES"
echo "============================================================================="
echo ""
echo "⚠️  Supabase không cung cấp public API để thực thi SQL trực tiếp."
echo "Bạn cần thực hiện các bước sau:"
echo ""
echo "1️⃣  Truy cập: https://app.supabase.com/project/vpmsytbbsxmtdicnkytv"
echo "2️⃣  Vào **SQL Editor**"
echo "3️⃣  Copy và chạy SQL sau:"
echo ""
echo "============================================================================="
cat << 'EOF'
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
EOF
echo "============================================================================="
echo ""
echo "4️⃣  Sau khi chạy SQL thành công, chạy lệnh sau để import dữ liệu:"
echo ""
echo "   python3 backend/scripts/run_import_vendor_surcharges.py \"vendor_rates/Tam bảo_092025.xlsx\" \"Tam Bảo\""
echo ""
