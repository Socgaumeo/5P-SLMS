#!/usr/bin/env python3
"""Test script để debug parsing drivers SQL - phiên bản 2"""

import os
import re

# Đọc file SQL
sql_file = os.path.join(os.path.dirname(__file__), '../../import_drivers_tambao.sql')
with open(sql_file, 'r', encoding='utf-8') as f:
    sql_content = f.read()

# Test pattern với whitespace
pattern = r"INSERT INTO drivers \((.*?)\) SELECT '(.*?)', '(.*?)', '(.*?)', '(.*?)', '(.*?)',\s*\(SELECT vendor_id FROM vendors WHERE vendor_code = '(.*?)'\),\s*(TRUE|FALSE)"

matches = re.findall(pattern, sql_content, re.DOTALL | re.IGNORECASE)
print(f'Pattern: Found {len(matches)} matches')

if matches:
    for i, match in enumerate(matches[:3], 1):
        columns_str, driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_code, is_active_str = match
        print(f'\nMatch {i}:')
        print(f'  Columns: {columns_str}')
        print(f'  Driver Code: {driver_code}')
        print(f'  Full Name: {full_name}')
        print(f'  Vendor Code: {vendor_code}')
        print(f'  Is Active: {is_active_str}')
else:
    print('\nKhông tìm thấy matches với pattern trên.')
    print('Thử pattern đơn giản hơn...')
    
    # Test pattern đơn giản hơn
    simple_pattern = r"INSERT INTO drivers \((.*?)\)"
    simple_matches = re.findall(simple_pattern, sql_content, re.IGNORECASE)
    print(f'\nSimple pattern: Found {len(simple_matches)} INSERT statements')
    
    if simple_matches:
        for i, columns_str in enumerate(simple_matches[:3], 1):
            print(f'\nMatch {i}:')
            print(f'  Columns: {columns_str}')
