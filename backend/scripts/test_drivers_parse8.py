#!/usr/bin/env python3
"""Test script đơn giản để debug parsing drivers SQL - không dùng escape"""

import os
import re

# Đọc file SQL
sql_file = os.path.join(os.path.dirname(__file__), '../../import_drivers_tambao.sql')
with open(sql_file, 'r', encoding='utf-8') as f:
    sql_content = f.read()

# Test pattern đơn giản - không dùng escape
print('Test 1: Tìm INSERT statements')
insert_pattern = r"INSERT\s+INTO\s+drivers\s*\((.*?)\)\s*SELECT"
matches = re.findall(insert_pattern, sql_content, re.DOTALL | re.IGNORECASE)
print(f'Found {len(matches)} matches')

if matches:
    for i, columns_str in enumerate(matches[:1], 1):
        print(f'\nMatch {i}: {columns_str}')
        
        # Tìm full INSERT statement - không dùng escape
        # Sử dụng pattern đơn giản hơn
        full_pattern = r"INSERT\s+INTO\s+drivers\s*\(" + re.escape(columns_str) + r"\)\s+SELECT.*?WHERE\s+NOT\s+EXISTS"
        full_match = re.search(full_pattern, sql_content, re.DOTALL | re.IGNORECASE)
        
        if full_match:
            full_statement = full_match.group(0)
            print(f'Full statement: {full_statement[:300]}...')
            
            # Tìm SELECT values - pattern đơn giản hơn
            # Pattern: 'TB0013', '13', 'Trần Xuân Cường', '0972029223', '1084007116', '29H 70692', (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
            select_pattern = r"SELECT\s+'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s+\(SELECT\s+vendor_id\s+FROM\s+vendors\s+WHERE\s+vendor_code\s+=\s*'([^']+)'\),\s*(TRUE|FALSE)"
            select_match = re.search(select_pattern, full_statement, re.IGNORECASE | re.DOTALL)
            
            if select_match:
                print(f'SELECT match found!')
                print(f'Groups: {len(select_match.groups())}')
                for j, group in enumerate(select_match.groups(), 1):
                    print(f'  Group {j}: {group}')
            else:
                print('SELECT match NOT found')
                # Debug: hiển thị SELECT values
                print(f'Debug SELECT values: {full_statement[full_statement.find("SELECT"):full_statement.find("WHERE")]}')
else:
    print('No matches found')
