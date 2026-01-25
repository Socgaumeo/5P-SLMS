#!/usr/bin/env python3
"""
Script kiểm tra dữ liệu vendor_rates trên Supabase
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()


def check_vendor_rates():
    """Kiểm tra dữ liệu vendor_rates trên Supabase"""
    try:
        # Tạo Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL và SUPABASE_SERVICE_ROLE_KEY phải được cấu hình trong .env")
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Lấy tất cả vendor_rates
        print("="*60)
        print("KIỂM TRA DỮ LIỆU VENDOR_RATES")
        print("="*60)
        
        result = supabase.table('vendor_rates').select('*').execute()
        
        if not result.data:
            print("❌ Không có dữ liệu vendor_rates nào")
            return
        
        rates = result.data
        print(f"\n✓ Tổng số vendor_rates: {len(rates)}")
        
        # Phân loại theo rate_type
        rate_types = {}
        for rate in rates:
            rate_type = rate.get('rate_type', 'UNKNOWN')
            if rate_type not in rate_types:
                rate_types[rate_type] = []
            rate_types[rate_type].append(rate)
        
        print(f"\n📊 Phân loại theo rate_type:")
        for rate_type, type_rates in rate_types.items():
            print(f"  - {rate_type}: {len(type_rates)} records")
        
        # Hiển thị chi tiết từng loại
        for rate_type in rate_types.keys():
            print(f"\n{'='*60}")
            print(f"CHI TIẾT {rate_type}")
            print(f"{'='*60}")
            
            type_rates = rate_types[rate_type]
            for i, rate in enumerate(type_rates[:10], 1):  # Chỉ hiển thị 10 đầu tiên
                origin = rate.get('origin', 'N/A')
                destination = rate.get('destination', 'N/A')
                vehicle_type = rate.get('vehicle_type', 'N/A')
                price = rate.get('price', 0)
                
                print(f"  [{i}] {origin} → {destination} | {vehicle_type} | {price:,} VND")
            
            if len(type_rates) > 10:
                print(f"  ... và {len(type_rates) - 10} records khác")
        
        print(f"\n{'='*60}")
        print("TỔNG KẾT")
        print(f"{'='*60}")
        print(f"✓ Tổng số vendor_rates: {len(rates)}")
        print(f"✓ Số loại rate_type: {len(rate_types)}")
        
        for rate_type, count in rate_types.items():
            print(f"  - {rate_type}: {count} records")
        
    except Exception as e:
        print(f"\n❌ Lỗi khi kiểm tra vendor_rates: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    check_vendor_rates()
