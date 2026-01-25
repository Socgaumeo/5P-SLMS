#!/usr/bin/env python3
"""Test script để debug parsing drivers SQL - phiên bản 4"""

import os
import re

# Đọc file SQL
sql_file = os.path.join(os.path.dirname(__file__), '../../import_drivers_tambao.sql')
with open(sql_file, 'r', encoding='utf-8') as f:
    sql_content = f.read()

# Test pattern mới - xử lý whitespace
insert_pattern = r"INSERT\s+INTO\s+drivers\s*\((.*?)\)\s*SELECT"

matches = re.findall(insert_pattern, sql_content, re.DOTALL | re.IGNORECASE)
print(f'Pattern: Found {len(matches)} INSERT statements')

if matches:
    for i, columns_str in enumerate(matches[:3], 1):
        print(f'\nMatch {i}:')
        print(f'  Columns: {columns_str}')
        
        # Tìm phần SELECT tương ứng
        insert_pos = sql_content.find(f"INSERT INTO drivers ({columns_str}) SELECT")
        if insert_pos != -1:
            select_part = sql_content[insert_pos + len(f"INSERT INTO drivers ({columns_str}) SELECT"):]
            where_pos = select_part.find("WHERE NOT EXISTS")
            if where_pos != -1:
                select_values = select_part[:where_pos].strip()
                print(f'  SELECT values: {select_values[:200]}...')
                
                # Parse SELECT values
                select_pattern = r"'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*\(SELECT\s+vendor_id\s+FROM\s+vendors\s+WHERE\s+vendor_code\s*=\s*'([^']*)'\),\s*(TRUE|FALSE)"
                select_matches = re.findall(select_pattern, select_values, re.IGNORECASE)
                
                if select_matches:
                    for match in select_matches[:1]:
                        driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_code, is_active_str = match
                        print(f'    Driver Code: {driver_code}')
                        print(f'    Full Name: {full_name}')
                        print(f'    Vendor Code: {vendor_code}')
                        print(f'    Is Active: {is_active_str}')
                else:
                    print('    Không parse được SELECT values')
else:
    print('Không tìm thấy INSERT statements')
