#!/usr/bin/env python3
"""Test script để debug parsing drivers SQL"""

import os
import re

# Đọc file SQL
sql_file = os.path.join(os.path.dirname(__file__), '../../import_drivers_tambao.sql')
with open(sql_file, 'r', encoding='utf-8') as f:
    sql_content = f.read()

# Test pattern 1
pattern1 = r"INSERT INTO drivers \((.*?)\) SELECT '(.*?)', '(.*?)', '(.*?)', '(.*?)', '(.*?)', \(SELECT vendor_id FROM vendors WHERE vendor_code = '(.*?)'\), (TRUE|FALSE)"
matches1 = re.findall(pattern1, sql_content, re.DOTALL | re.IGNORECASE)
print(f'Pattern 1: Found {len(matches1)} matches')

if matches1:
    for i, match in enumerate(matches1[:3], 1):
        columns_str, driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_code, is_active_str = match
        print(f'Match {i}:')
        print(f'  Columns: {columns_str}')
        print(f'  Driver Code: {driver_code}')
        print(f'  Full Name: {full_name}')
        print(f'  Vendor Code: {vendor_code}')
        print()

# Test pattern 2 - đơn giản hơn
pattern2 = r"INSERT INTO drivers \(driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active\) SELECT '(.*?)', '(.*?)', '(.*?)', '(.*?)', '(.*?)', \(SELECT vendor_id FROM vendors WHERE vendor_code = '(.*?)'\), (TRUE|FALSE)"
matches2 = re.findall(pattern2, sql_content, re.DOTALL | re.IGNORECASE)
print(f'Pattern 2: Found {len(matches2)} matches')

if matches2:
    for i, match in enumerate(matches2[:3], 1):
        driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_code, is_active_str = match
        print(f'Match {i}:')
        print(f'  Driver Code: {driver_code}')
        print(f'  Full Name: {full_name}')
        print(f'  Vendor Code: {vendor_code}')
        print()

# Test pattern 3 - tìm tất cả INSERT
pattern3 = r"INSERT INTO drivers"
matches3 = re.findall(pattern3, sql_content, re.IGNORECASE)
print(f'Pattern 3: Found {len(matches3)} INSERT statements')

# Hiển thị 500 ký tự đầu tiên của INSERT đầu tiên
if matches3:
    first_insert = sql_content.find("INSERT INTO drivers")
    if first_insert != -1:
        print(f'\nFirst INSERT (first 500 chars):')
        print(sql_content[first_insert:first_insert+500])
