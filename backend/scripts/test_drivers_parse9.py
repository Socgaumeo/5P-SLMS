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
            # Sử dụng pattern: '...', '...', '...', '...', (SELECT ...), TRUE/FALSE
            select_pattern = r"'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*\(SELECT\s+vendor_id\s+FROM\s+vendors\s+WHERE\s+vendor_code\s+=\s*'([^']+)'\),\s*(TRUE|FALSE)"
            select_matches = re.findall(select_pattern, full_statement, re.IGNORECASE)
            
            if select_matches:
                for match in select_matches[:1]:
                    print(f'SELECT match: {len(match)} groups')
                    for j, group in enumerate(match, 1):
                        print(f'  Group {j}: {group}')
            else:
                print('No SELECT matches found')
else:
    print('No matches found')
