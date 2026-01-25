#!/usr/bin/env python3
"""
Script đơn giản để import drivers từ file SQL lên Supabase
Parse thủ công từng dòng SQL
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
        
        # Tìm tất cả các INSERT statements
        # Pattern để tìm INSERT INTO drivers statements
        insert_pattern = r"INSERT\s+INTO\s+drivers\s*\((.*?)\)\s*SELECT"
        
        insert_statements = re.findall(insert_pattern, sql_content, re.DOTALL | re.IGNORECASE)
        print(f"📑 Tìm thấy {len(insert_statements)} INSERT statements")
        
        # Import từng INSERT statement
        imported = 0
        failed = 0
        
        for i, columns_str in enumerate(insert_statements, 1):
            # Tìm phần SELECT tương ứng
            # Sử dụng regex để tìm INSERT statement đầy đủ
            full_insert_pattern = rf"INSERT\s+INTO\s+drivers\s*\({re.escape(columns_str)}\)\s+SELECT\s+([^;]+);"
            full_match = re.search(full_insert_pattern, sql_content, re.DOTALL | re.IGNORECASE)
            
            if not full_match:
                print(f"⚠️  Không tìm thấy full INSERT statement cho match {i}")
                continue
            
            select_part = full_match.group(1)
            
            # Parse SELECT values thủ công
            # Format: 'TB0013', '13', 'Trần Xuân Cường', '0972029223', '1084007116', '29H 70692', (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
            
            # Tìm driver_code (giá trị đầu tiên trong SELECT)
            driver_code_match = re.search(r"SELECT\s+'([^']+)'", select_part)
            if not driver_code_match:
                print(f"⚠️  Không tìm thấy driver_code trong statement {i}")
                continue
            
            driver_code = driver_code_match.group(1)
            
            # Tìm employee_id
            employee_id_match = re.search(r"SELECT\s+'[^']+',\s*'([^']*)'", select_part)
            employee_id = employee_id_match.group(1) if employee_id_match else ''
            
            # Tìm full_name
            full_name_match = re.search(r"SELECT\s+'[^']+',\s*'[^']*',\s*'([^']*)'", select_part)
            full_name = full_name_match.group(1) if full_name_match else ''
            
            # Tìm phone
            phone_match = re.search(r"SELECT\s+'[^']+',\s*'[^']*',\s*'[^']*',\s*'([^']*)'", select_part)
            phone = phone_match.group(1) if phone_match else ''
            
            # Tìm id_card
            id_card_match = re.search(r"SELECT\s+'[^']+',\s*'[^']*',\s*'[^']*',\s*'[^']*',\s*'([^']*)'", select_part)
            id_card = id_card_match.group(1) if id_card_match else ''
            
            # Tìm license_plate
            license_plate_match = re.search(r"SELECT\s+'[^']+',\s*'[^']*',\s*'[^']*',\s*'[^']*',\s*'[^']*',\s*'([^']*)'", select_part)
            license_plate = license_plate_match.group(1) if license_plate_match else ''
            
            # Tìm is_active (TRUE/FALSE)
            is_active_match = re.search(r"SELECT.*,\s*(TRUE|FALSE)\s*$", select_part, re.IGNORECASE)
            is_active = is_active_match.group(1).upper() == 'TRUE' if is_active_match else True
            
            # Tạo record
            record = {
                'driver_code': driver_code,
                'employee_id': employee_id,
                'full_name': full_name,
                'phone': phone,
                'id_card': id_card,
                'license_plate': license_plate,
                'vendor_id': tambao_vendor_id,
                'is_active': is_active
            }
            
            # Kiểm tra xem driver đã tồn tại chưa
            existing = supabase.table('drivers').select('driver_id').eq('driver_code', driver_code).execute()
            
            if existing.data:
                # Update
                result = supabase.table('drivers').update(record).eq('driver_code', driver_code).execute()
                print(f"[{i}/{len(insert_statements)}] Updated: {driver_code} - {full_name}")
                imported += 1
            else:
                # Insert
                result = supabase.table('drivers').insert(record).execute()
                print(f"[{i}/{len(insert_statements)}] Inserted: {driver_code} - {full_name}")
                imported += 1
        
        print(f"\n✓ Import hoàn tất: {imported} thành công, {failed} thất bại")
        
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
