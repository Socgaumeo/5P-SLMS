#!/usr/bin/env python3
"""
Script tạo bảng vendor_surcharges sử dụng Supabase Management API
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def execute_sql_via_api(sql_query: str):
    """
    Thực thi SQL thông qua Supabase Management API
    
    Args:
        sql_query: Câu lệnh SQL cần thực thi
    """
    supabase_url = os.getenv('SUPABASE_URL')
    api_key = os.getenv('SUPABASE_PUBLISHABLE_KEY')
    
    if not supabase_url or not api_key:
        raise ValueError("SUPABASE_URL và SUPABASE_PUBLISHABLE_KEY phải được cấu hình trong .env")
    
    # Lấy project reference từ URL
    project_ref = supabase_url.split('://')[1].split('.')[0]
    
    # Supabase Management API endpoint
    # Lưu ý: Supabase không cung cấp public API để thực thi SQL trực tiếp
    # Cần sử dụng Supabase Dashboard hoặc psql client
    
    print("⚠️  Supabase không cung cấp public API để thực thi SQL trực tiếp.")
    print("Bạn cần thực hiện thủ công trên Supabase Dashboard.")
    print(f"\nProject Reference: {project_ref}")
    print(f"\nSQL cần chạy:")
    print("="*60)
    print(sql_query)
    print("="*60)
    
    return False


def main():
    """Hàm chính"""
    sql_query = """
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
"""
    
    print("="*60)
    print("THỰC THI SQL TẠO BẢNG VENDOR_SURCHARGES")
    print("="*60)
    
    try:
        execute_sql_via_api(sql_query)
        
        print("\n1️⃣  Truy cập: https://app.supabase.com/project/vpmsytbbsxmtdicnkytv")
        print("2️⃣  Vào **SQL Editor**")
        print("3️⃣  Copy SQL ở trên và chạy")
        print("4️⃣  Sau khi chạy thành công, chạy lệnh sau:")
        print("\n   python3 backend/scripts/run_import_vendor_surcharges.py \"vendor_rates/Tam bảo_092025.xlsx\" \"Tam Bảo\"")
        
    except Exception as e:
        print(f"\n❌ Lỗi: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
