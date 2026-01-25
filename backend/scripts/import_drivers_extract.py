#!/usr/bin/env python3
"""
Script đơn giản để import drivers từ file SQL lên Supabase
Extract driver codes và tạo records trực tiếp
"""

import os
import sys
import re
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
        print("IMPORT DRIVERS TỪ FILE SQL")
        print("="*60)
        
        # Đọc file SQL
        sql_file = os.path.join(os.path.dirname(__file__), '../../import_drivers_tambao.sql')
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Tìm vendor_id cho TAMBAO
        vendor_result = supabase.table('vendors').select('vendor_id').eq('vendor_code', 'TAMBAO').execute()
        
        if not vendor_result.data:
            print("❌ Không tìm thấy vendor TAMBAO trong database")
            return
        
        tambao_vendor_id = vendor_result.data[0]['vendor_id']
        print(f"✅ Vendor TAMBAO ID: {tambao_vendor_id}")
        
        # Tìm tất cả các driver codes trong SQL
        # Pattern: 'TB0013', '13', 'Trần Xuân Cường', '0972029223', '1084007116', '29H 70692', (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
        # WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0013');
        
        # Tìm tất cả các driver codes từ WHERE NOT EXISTS
        driver_codes = re.findall(r"WHERE\s+NOT\s+EXISTS.*driver_code\s*=\s*'([^']+)'", sql_content, re.IGNORECASE)
        
        print(f"📑 Tìm thấy {len(driver_codes)} driver codes")
        
        # Import từng driver
        imported = 0
        failed = 0
        
        for i, driver_code in enumerate(driver_codes, 1):
            # Tìm INSERT statement cho driver_code này
            # Tìm pattern: 'TB0013', '13', 'Trần Xuân Cường', ...
            pattern = rf"'{driver_code}'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'"
            match = re.search(pattern, sql_content)
            
            if not match:
                print(f"⚠️  Không tìm thấy dữ liệu cho driver_code: {driver_code}")
                failed += 1
                continue
            
            employee_id, full_name, phone, id_card, license_plate = match.groups()
            
            # Tìm is_active
            is_active_pattern = rf"'{driver_code}'.*?\(SELECT vendor_id.*?\),\s*(TRUE|FALSE)"
            is_active_match = re.search(is_active_pattern, sql_content, re.IGNORECASE | re.DOTALL)
            is_active = is_active_match.group(1).upper() == 'TRUE' if is_active_match else True
            
            # Tạo record - truncate các trường quá dài
            record = {
                'driver_code': driver_code,
                'employee_id': employee_id[:20] if employee_id else None,
                'full_name': full_name[:100] if full_name else None,
                'phone': phone[:20] if phone else None,
                'id_card': id_card[:20] if id_card else None,
                'license_plate': license_plate[:20] if license_plate else None,
                'vendor_id': tambao_vendor_id,
                'is_active': is_active
            }
            
            # Kiểm tra xem driver đã tồn tại chưa
            existing = supabase.table('drivers').select('driver_id').eq('driver_code', driver_code).execute()
            
            if existing.data:
                # Update
                result = supabase.table('drivers').update(record).eq('driver_code', driver_code).execute()
                print(f"[{i}/{len(driver_codes)}] Updated: {driver_code} - {full_name}")
                imported += 1
            else:
                # Insert
                result = supabase.table('drivers').insert(record).execute()
                print(f"[{i}/{len(driver_codes)}] Inserted: {driver_code} - {full_name}")
                imported += 1
        
        print(f"\n✓ Import hoàn tất: {imported} thành công, {failed} thất bại")
        
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
