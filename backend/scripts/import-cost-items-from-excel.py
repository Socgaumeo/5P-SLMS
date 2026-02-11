#!/usr/bin/env python3
"""
Import cost items from Excel vendor rates file into master_cost_items table.
Usage: python3 scripts/import_cost_items.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import re
from app.db.session import get_connection

EXCEL_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                          'vendor_rates/ASGL_định mức làm hàng_02032022.xlsx')

def generate_cost_code(name, region, index):
    """Generate a unique cost code from the name and region."""
    # Region prefix
    region_map = {
        'Miền Nam': 'MN',
        'Hà Nội': 'HN',
        'Hải Phòng': 'HP',
        'Thái Nguyên': 'TN',
    }
    region_prefix = region_map.get(region, 'XX')

    return f"{region_prefix}-{index:04d}"


def parse_price(value):
    """Parse price value from Excel (may contain text or formatting)."""
    if pd.isna(value):
        return 0
    if isinstance(value, (int, float)):
        return float(value)
    # Handle string values like "1,000,000 / cont"
    text = str(value)
    # Extract first number
    match = re.search(r'[\d,]+', text.replace(' ', ''))
    if match:
        return float(match.group().replace(',', ''))
    return 0


def import_sheet_tn_bn_qn(conn, df):
    """Import 'Chi phí TN - BN - QN' sheet (Thái Nguyên, Bắc Ninh, Quảng Ninh)."""
    region = 'Miền Nam'  # Actually Thái Nguyên area
    # Data starts at row 5 (after header row)
    df_data = pd.read_excel(EXCEL_FILE, sheet_name='Chi phí TN - BN - QN', header=5)

    cursor = conn.cursor()
    count = 0

    for idx, row in df_data.iterrows():
        stt = row.iloc[0] if not pd.isna(row.iloc[0]) else None
        name = row.iloc[1] if not pd.isna(row.iloc[1]) else None

        # Skip header rows or section headers (like "1", "2", "Hàng nguyên container")
        if not name or (stt and '.' not in str(stt)):
            continue

        default_price = parse_price(row.iloc[2])
        selling_price = parse_price(row.iloc[3])
        unit = str(row.iloc[4]).strip() if not pd.isna(row.iloc[4]) else 'UNIT'
        notes = str(row.iloc[5]).strip() if len(row) > 5 and not pd.isna(row.iloc[5]) else ''

        cost_code = generate_cost_code(name, 'Thái Nguyên', count + 1)

        cursor.execute("""
            INSERT INTO master_cost_items
            (cost_code, name_vi, category, region, default_price, selling_price, unit, notes, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true)
            ON CONFLICT (cost_code) DO NOTHING
        """, (cost_code, name, 'Hải quan', 'Thái Nguyên', default_price, selling_price, unit, notes))
        count += 1

    conn.commit()
    return count


def import_sheet_ha_noi(conn):
    """Import 'Hà Nội' sheet."""
    df_data = pd.read_excel(EXCEL_FILE, sheet_name='Hà Nội', header=13)

    cursor = conn.cursor()
    count = 0

    for idx, row in df_data.iterrows():
        stt = row.iloc[0] if not pd.isna(row.iloc[0]) else None
        name = row.iloc[1] if not pd.isna(row.iloc[1]) else None

        if not name or pd.isna(name):
            continue

        name = str(name).strip()
        if not name or name.startswith('STT'):
            continue

        unit = str(row.iloc[2]).strip() if not pd.isna(row.iloc[2]) else 'UNIT'
        default_price = parse_price(row.iloc[3])
        notes = str(row.iloc[4]).strip() if len(row) > 4 and not pd.isna(row.iloc[4]) else ''

        cost_code = generate_cost_code(name, 'Hà Nội', count + 1)

        cursor.execute("""
            INSERT INTO master_cost_items
            (cost_code, name_vi, category, region, default_price, selling_price, unit, notes, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true)
            ON CONFLICT (cost_code) DO NOTHING
        """, (cost_code, name, 'Hải quan', 'Hà Nội', default_price, default_price, unit, notes))
        count += 1

    conn.commit()
    return count


def import_sheet_hai_phong(conn):
    """Import 'Hải Phòng' sheet."""
    df_data = pd.read_excel(EXCEL_FILE, sheet_name='Hải Phòng', header=7)

    cursor = conn.cursor()
    count = 0

    for idx, row in df_data.iterrows():
        stt = row.iloc[0] if not pd.isna(row.iloc[0]) else None
        name = row.iloc[1] if not pd.isna(row.iloc[1]) else None

        if not name or pd.isna(name):
            continue

        name = str(name).strip()
        if not name or name.startswith('STT'):
            continue

        unit = str(row.iloc[2]).strip() if not pd.isna(row.iloc[2]) else 'UNIT'
        default_price = parse_price(row.iloc[3])
        notes = str(row.iloc[4]).strip() if len(row) > 4 and not pd.isna(row.iloc[4]) else ''

        cost_code = generate_cost_code(name, 'Hải Phòng', count + 1)

        cursor.execute("""
            INSERT INTO master_cost_items
            (cost_code, name_vi, category, region, default_price, selling_price, unit, notes, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true)
            ON CONFLICT (cost_code) DO NOTHING
        """, (cost_code, name, 'Hải quan', 'Hải Phòng', default_price, default_price, unit, notes))
        count += 1

    conn.commit()
    return count


def main():
    print(f"Importing cost items from: {EXCEL_FILE}")

    if not os.path.exists(EXCEL_FILE):
        print(f"Error: File not found: {EXCEL_FILE}")
        return

    conn = get_connection()

    try:
        # Import each sheet
        df = pd.ExcelFile(EXCEL_FILE)

        print("\n1. Importing 'Chi phí TN - BN - QN' sheet...")
        count1 = import_sheet_tn_bn_qn(conn, df)
        print(f"   Imported {count1} items for Thái Nguyên region")

        print("\n2. Importing 'Hà Nội' sheet...")
        count2 = import_sheet_ha_noi(conn)
        print(f"   Imported {count2} items for Hà Nội region")

        print("\n3. Importing 'Hải Phòng' sheet...")
        count3 = import_sheet_hai_phong(conn)
        print(f"   Imported {count3} items for Hải Phòng region")

        print(f"\n✅ Total: {count1 + count2 + count3} cost items imported")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
