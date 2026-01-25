#!/usr/bin/env python3
"""
Script để chạy SQL trên Supabase
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


def main():
    """Hàm chính"""
    try:
        # Tạo Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ SUPABASE_URL hoặc SUPABASE_SERVICE_ROLE_KEY phải được cấu hình trong .env")
            return
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Đọc file SQL
        sql_file = os.path.join('..', 'create_vendor_surcharges_table.sql')
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print("📄 Đọc file SQL...")
        print(f"Nội dung:\n{sql_content}")
        
        # Chạy SQL trên Supabase
        # Supabase không hỗ trợ chạy SQL trực tiếp qua API
        # Cần sử dụng Supabase dashboard hoặc psql client
        
        print("\n⚠️  Supabase không hỗ trợ chạy SQL trực tiếp qua API")
        print("   Bạn cần:")
        print("   1. Mở Supabase dashboard: https://app.supabase.com/project/vpmsytbbsxmtdicnkytv")
        print("   2. Hoặc sử dụng psql client kết nối trực tiếp đến database")
        print("\n   Sau đó chạy file SQL trên dashboard hoặc qua psql")
        
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
