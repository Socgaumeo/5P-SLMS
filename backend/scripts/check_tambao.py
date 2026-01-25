#!/usr/bin/env python3
"""
Script để kiểm tra vendor TAMBAO trong file SQL
"""

import re

# Đọc file SQL vendors
with open('../import_kh_ncc.sql', 'r', encoding='utf-8') as f:
    sql_content = f.read()

# Tìm tất cả vendor codes
vendor_pattern = r"INSERT\s+INTO\s+vendors\s*\([^)]+\)\s*VALUES\s*\([^)]*'([^']+)'"
vendor_codes = re.findall(vendor_pattern, sql_content, re.IGNORECASE)

print(f'Tổng số vendors trong file SQL: {len(vendor_codes)}')
print('\nDanh sách vendor codes:')
for code in vendor_codes[:20]:
    print(f'  - {code}')

# Kiểm tra có TAMBAO không
if 'TAMBAO' in vendor_codes:
    print('\n✅ Vendor TAMBAO có trong file SQL')
else:
    print('\n❌ Vendor TAMBAO KHÔNG có trong file SQL')
    
# Tìm vendor codes có chứa 'TAM' hoặc 'BAO'
tambao_like = [code for code in vendor_codes if 'TAM' in code.upper() or 'BAO' in code.upper()]
if tambao_like:
    print('\nVendors có chứa TAM hoặc BAO:')
    for code in tambao_like:
        print(f'  - {code}')

# Đọc file drivers để xem vendor_code được sử dụng
print('\n\n=== KIỂM TRA FILE DRIVERS ===')
with open('../import_drivers_tambao.sql', 'r', encoding='utf-8') as f:
    drivers_sql = f.read()

# Tìm vendor_code trong drivers SQL
vendor_pattern_drivers = r"vendor_code\s*=\s*'([^']+)'"
vendor_codes_drivers = re.findall(vendor_pattern_drivers, drivers_sql, re.IGNORECASE)
print(f'\nVendor codes trong file drivers: {set(vendor_codes_drivers)}')
