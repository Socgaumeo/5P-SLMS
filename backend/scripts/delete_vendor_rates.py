#!/usr/bin/env python3
"""
Script xóa tất cả vendor_rates trên Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()


def delete_all_vendor_rates():
    """Xóa tất cả vendor_rates trên Supabase"""
    try:
        # Tạo Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL và SUPABASE_SERVICE_ROLE_KEY phải được cấu hình trong .env")
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Lấy tất cả vendor_rates
        print("="*60)
        print("XÓA TẤT CẢ VENDOR_RATES")
        print("="*60)
        
        result = supabase.table('vendor_rates').select('*').execute()
        
        if not result.data:
            print("❌ Không có dữ liệu vendor_rates nào")
            return
        
        rates = result.data
        print(f"\n✓ Số vendor_rates hiện tại: {len(rates)}")
        
        # Xóa từng rate
        for i, rate in enumerate(rates, 1):
            try:
                supabase.table('vendor_rates').delete().eq('id', rate['id']).execute()
                print(f"  [{i}] Deleted rate ID: {rate['id']}")
            except Exception as e:
                print(f"  ❌ Lỗi khi xóa rate ID {rate['id']}: {str(e)}")
        
        print(f"\n✓ Đã xóa {len(rates)} vendor_rates")
        
    except Exception as e:
        print(f"\n❌ Lỗi khi xóa vendor_rates: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    delete_all_vendor_rates()
