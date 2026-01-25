#!/usr/bin/env python3
"""
Script để tạo vendor TAMBAO trong Supabase
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
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
        
        print("="*60)
        print("TẠO VENDOR TAMBAO")
        print("="*60)
        
        # Kiểm tra xem vendor TAMBAO đã tồn tại chưa
        existing = supabase.table('vendors').select('*').eq('vendor_code', 'TAMBAO').execute()
        
        if existing.data:
            print(f"✅ Vendor TAMBAO đã tồn tại: {existing.data[0]}")
            return
        
        # Tạo vendor TAMBAO
        record = {
            'vendor_code': 'TAMBAO',
            'company_name': 'Công ty TNHH Vận tải Tam Bảo',
            'short_name': 'Tam Bảo',
            'vendor_type': 'TRUCKING',
            'is_active': True,
            'payment_terms': 30
        }
        
        result = supabase.table('vendors').insert(record).execute()
        
        print(f"✅ Đã tạo vendor TAMBAO thành công:")
        print(f"   - vendor_id: {result.data[0]['vendor_id']}")
        print(f"   - vendor_code: {result.data[0]['vendor_code']}")
        print(f"   - company_name: {result.data[0]['company_name']}")
        
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
