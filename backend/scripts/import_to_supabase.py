#!/usr/bin/env python3
"""
Script import dữ liệu từ SQL files lên Supabase
Hỗ trợ import: customers, vendors, drivers, vendor_rates, vendor_surcharges
"""

import os
import sys
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Thêm đường dẫn parent để import từ app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from supabase import create_client, Client
from app.core.config import settings

# Load environment variables
load_dotenv()


class SupabaseImporter:
    """Class quản lý import dữ liệu lên Supabase"""
    
    def __init__(self):
        """Khởi tạo Supabase client"""
        self.supabase: Client = self._get_supabase_client()
        self.stats = {
            'customers': {'success': 0, 'failed': 0, 'errors': []},
            'vendors': {'success': 0, 'failed': 0, 'errors': []},
            'drivers': {'success': 0, 'failed': 0, 'errors': []},
            'vendor_rates': {'success': 0, 'failed': 0, 'errors': []},
            'vendor_surcharges': {'success': 0, 'failed': 0, 'errors': []},
        }
    
    def _get_supabase_client(self) -> Client:
        """Tạo Supabase client"""
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL và SUPABASE_SERVICE_ROLE_KEY phải được cấu hình trong .env")
        
        return create_client(supabase_url, supabase_key)
    
    def parse_sql_insert(self, sql_content: str, table_name: str) -> List[Dict[str, Any]]:
        """
        Parse SQL INSERT statements thành list của dictionaries
        
        Args:
            sql_content: Nội dung file SQL
            table_name: Tên bảng cần import
        
        Returns:
            List của dictionaries chứa dữ liệu
        """
        records = []
        
        # Pattern để tìm INSERT INTO statements
        # Cải thiện pattern để xử lý cả định dạng phức tạp
        pattern = rf"INSERT INTO {table_name}\s*\((.*?)\)\s*VALUES\s*\((.*?)\)"
        
        # Xử lý multi-line INSERT
        matches = re.findall(pattern, sql_content, re.DOTALL | re.IGNORECASE)
        
        for columns_str, values_str in matches:
            # Parse columns
            columns = [col.strip().strip('"') for col in columns_str.split(',')]
            
            # Parse values - xử lý string literals
            values = self._parse_sql_values(values_str)
            
            if len(columns) == len(values):
                record = dict(zip(columns, values))
                records.append(record)
            else:
                print(f"Warning: Column count mismatch. Columns: {len(columns)}, Values: {len(values)}")
        
        # Nếu không tìm thấy records với pattern trên, thử parse theo cách khác
        if not records:
            records = self._parse_sql_insert_alternative(sql_content, table_name)
        
        return records
    
    def _parse_sql_insert_alternative(self, sql_content: str, table_name: str) -> List[Dict[str, Any]]:
        """
        Parse SQL INSERT theo cách thay thế cho các định dạng phức tạp
        
        Args:
            sql_content: Nội dung file SQL
            table_name: Tên bảng cần import
        
        Returns:
            List của dictionaries chứa dữ liệu
        """
        records = []
        
        # Tìm tất cả các INSERT statements
        insert_pattern = rf"INSERT INTO {table_name}\s*\((.*?)\)\s*SELECT\s+(.*?)\s+FROM\s+drivers\s+WHERE\s+NOT EXISTS"
        matches = re.findall(insert_pattern, sql_content, re.DOTALL | re.IGNORECASE)
        
        for columns_str, select_str in matches:
            # Parse columns
            columns = [col.strip().strip('"') for col in columns_str.split(',')]
            
            # Parse SELECT statement
            select_pattern = r"'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*\(SELECT\s+vendor_id\s+FROM\s+vendors\s+WHERE\s+vendor_code\s*=\s*'(\w+)'\),\s*(TRUE|FALSE)"
            select_matches = re.findall(select_pattern, select_str, re.IGNORECASE)
            
            for match in select_matches:
                values = list(match[:-1])  # Tất cả trừ giá trị cuối cùng
                vendor_code = match[-2]  # Vendor code
                is_active = match[-1] == 'TRUE'
                
                # Thay thế vendor_id bằng vendor_code
                values.append(vendor_code)
                values.append(is_active)
                
                if len(columns) == len(values):
                    record = dict(zip(columns, values))
                    records.append(record)
        
        return records
    
    def _parse_sql_values(self, values_str: str) -> List[Any]:
        """
        Parse SQL values string thành list của Python values
        
        Args:
            values_str: SQL values string
        
        Returns:
            List của Python values
        """
        values = []
        current = ''
        in_quotes = False
        quote_char = None
        
        i = 0
        while i < len(values_str):
            char = values_str[i]
            
            if char in ("'", '"') and (i == 0 or values_str[i-1] != '\\'):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
                current += char
            elif char == ',' and not in_quotes:
                values.append(self._convert_sql_value(current.strip()))
                current = ''
            else:
                current += char
            
            i += 1
        
        if current.strip():
            values.append(self._convert_sql_value(current.strip()))
        
        return values
    
    def _convert_sql_value(self, value: str) -> Any:
        """
        Convert SQL value string thành Python value
        
        Args:
            value: SQL value string
        
        Returns:
            Python value (str, int, float, bool, None)
        """
        value = value.strip()
        
        # NULL
        if value.upper() == 'NULL':
            return None
        
        # Boolean
        if value.upper() == 'TRUE':
            return True
        if value.upper() == 'FALSE':
            return False
        
        # String with quotes
        if (value.startswith("'") and value.endswith("'")) or \
           (value.startswith('"') and value.endswith('"')):
            return value[1:-1]
        
        # Number
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        return value
    
    def import_customers(self) -> bool:
        """
        Import dữ liệu customers từ file import_kh_ncc.sql
        
        Returns:
            True nếu thành công, False nếu thất bại
        """
        print("\n" + "="*60)
        print("IMPORT CUSTOMERS")
        print("="*60)
        
        try:
            # Đọc file SQL
            sql_file = os.path.join(os.path.dirname(__file__), '../../import_kh_ncc.sql')
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Parse SQL
            records = self.parse_sql_insert(sql_content, 'customers')
            
            if not records:
                print("Không tìm thấy dữ liệu customers trong file SQL")
                return False
            
            print(f"Đã parse được {len(records)} records từ file SQL")
            
            # Import từng record
            for i, record in enumerate(records, 1):
                try:
                    # Kiểm tra xem customer đã tồn tại chưa
                    existing = self.supabase.table('customers').select('customer_id').eq('customer_code', record.get('customer_code')).execute()
                    
                    if existing.data:
                        # Update
                        result = self.supabase.table('customers').update(record).eq('customer_code', record.get('customer_code')).execute()
                        print(f"[{i}/{len(records)}] Updated: {record.get('customer_code')} - {record.get('company_name')}")
                    else:
                        # Insert
                        result = self.supabase.table('customers').insert(record).execute()
                        print(f"[{i}/{len(records)}] Inserted: {record.get('customer_code')} - {record.get('company_name')}")
                    
                    self.stats['customers']['success'] += 1
                    
                except Exception as e:
                    error_msg = f"Error importing customer {record.get('customer_code')}: {str(e)}"
                    print(f"ERROR: {error_msg}")
                    self.stats['customers']['failed'] += 1
                    self.stats['customers']['errors'].append(error_msg)
            
            print(f"\n✓ Import customers hoàn tất: {self.stats['customers']['success']} thành công, {self.stats['customers']['failed']} thất bại")
            return True
            
        except Exception as e:
            error_msg = f"Lỗi khi import customers: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.stats['customers']['errors'].append(error_msg)
            return False
    
    def import_vendors(self) -> bool:
        """
        Import dữ liệu vendors từ file import_kh_ncc.sql
        
        Returns:
            True nếu thành công, False nếu thất bại
        """
        print("\n" + "="*60)
        print("IMPORT VENDORS")
        print("="*60)
        
        try:
            # Đọc file SQL
            sql_file = os.path.join(os.path.dirname(__file__), '../../import_kh_ncc.sql')
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Parse SQL
            records = self.parse_sql_insert(sql_content, 'vendors')
            
            if not records:
                print("Không tìm thấy dữ liệu vendors trong file SQL")
                return False
            
            print(f"Đã parse được {len(records)} records từ file SQL")
            
            # Import từng record
            for i, record in enumerate(records, 1):
                try:
                    # Kiểm tra xem vendor đã tồn tại chưa
                    existing = self.supabase.table('vendors').select('vendor_id').eq('vendor_code', record.get('vendor_code')).execute()
                    
                    if existing.data:
                        # Update
                        result = self.supabase.table('vendors').update(record).eq('vendor_code', record.get('vendor_code')).execute()
                        print(f"[{i}/{len(records)}] Updated: {record.get('vendor_code')} - {record.get('company_name')}")
                    else:
                        # Insert
                        result = self.supabase.table('vendors').insert(record).execute()
                        print(f"[{i}/{len(records)}] Inserted: {record.get('vendor_code')} - {record.get('company_name')}")
                    
                    self.stats['vendors']['success'] += 1
                    
                except Exception as e:
                    error_msg = f"Error importing vendor {record.get('vendor_code')}: {str(e)}"
                    print(f"ERROR: {error_msg}")
                    self.stats['vendors']['failed'] += 1
                    self.stats['vendors']['errors'].append(error_msg)
            
            print(f"\n✓ Import vendors hoàn tất: {self.stats['vendors']['success']} thành công, {self.stats['vendors']['failed']} thất bại")
            return True
            
        except Exception as e:
            error_msg = f"Lỗi khi import vendors: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.stats['vendors']['errors'].append(error_msg)
            return False
    
    def import_drivers(self) -> bool:
        """
        Import dữ liệu drivers từ file import_drivers_tambao.sql
        
        Returns:
            True nếu thành công, False nếu thất bại
        """
        print("\n" + "="*60)
        print("IMPORT DRIVERS")
        print("="*60)
        
        try:
            # Đọc file SQL
            sql_file = os.path.join(os.path.dirname(__file__), '../../import_drivers_tambao.sql')
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Parse SQL theo cách đặc biệt cho drivers
            records = self._parse_drivers_manual(sql_content)
            
            if not records:
                print("Không tìm thấy dữ liệu drivers trong file SQL")
                return False
            
            print(f"Đã parse được {len(records)} records từ file SQL")
            
            # Import từng record
            for i, record in enumerate(records, 1):
                try:
                    # Xử lý vendor_id từ vendor_code
                    vendor_code = record.get('vendor_code')
                    if vendor_code:
                        vendor_result = self.supabase.table('vendors').select('vendor_id').eq('vendor_code', vendor_code).execute()
                        if vendor_result.data:
                            record['vendor_id'] = vendor_result.data[0]['vendor_id']
                        else:
                            print(f"Warning: Vendor {vendor_code} không tìm thấy, bỏ qua driver {record.get('driver_code')}")
                            continue
                    
                    # Xóa vendor_code khỏi record vì không có trong bảng drivers
                    if 'vendor_code' in record:
                        del record['vendor_code']
                    
                    # Kiểm tra xem driver đã tồn tại chưa
                    existing = self.supabase.table('drivers').select('driver_id').eq('driver_code', record.get('driver_code')).execute()
                    
                    if existing.data:
                        # Update
                        result = self.supabase.table('drivers').update(record).eq('driver_code', record.get('driver_code')).execute()
                        print(f"[{i}/{len(records)}] Updated: {record.get('driver_code')} - {record.get('full_name')}")
                    else:
                        # Insert
                        result = self.supabase.table('drivers').insert(record).execute()
                        print(f"[{i}/{len(records)}] Inserted: {record.get('driver_code')} - {record.get('full_name')}")
                    
                    self.stats['drivers']['success'] += 1
                    
                except Exception as e:
                    error_msg = f"Error importing driver {record.get('driver_code')}: {str(e)}"
                    print(f"ERROR: {error_msg}")
                    self.stats['drivers']['failed'] += 1
                    self.stats['drivers']['errors'].append(error_msg)
            
            print(f"\n✓ Import drivers hoàn tất: {self.stats['drivers']['success']} thành công, {self.stats['drivers']['failed']} thất bại")
            return True
            
        except Exception as e:
            error_msg = f"Lỗi khi import drivers: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.stats['drivers']['errors'].append(error_msg)
            return False
    
    def _parse_drivers_sql(self, sql_content: str) -> List[Dict[str, Any]]:
        """
        Parse SQL file đặc biệt cho drivers với định dạng phức tạp
        
        Args:
            sql_content: Nội dung file SQL
        
        Returns:
            List của dictionaries chứa dữ liệu drivers
        """
        records = []
        
        # Tìm tất cả các INSERT statements
        # SQL có định dạng: INSERT INTO drivers (...) SELECT '...', '...', ..., (SELECT ...), TRUE WHERE ...
        # Pattern cần xử lý cả whitespace và newline
        insert_pattern = r"INSERT INTO drivers \((.*?)\) SELECT '(.*?)', '(.*?)', '(.*?)', '(.*?)', '(.*?)',\s*\(SELECT vendor_id FROM vendors WHERE vendor_code = '(.*?)'\),\s*(TRUE|FALSE)"
        
        matches = re.findall(insert_pattern, sql_content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            columns_str, driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_code, is_active_str = match
            
            # Parse columns
            columns = [col.strip().strip('"') for col in columns_str.split(',')]
            
            # Tạo values
            values = [driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_code, is_active_str == 'TRUE']
            
            # Tạo record
            record = dict(zip(columns, values))
            records.append(record)
        
        # Nếu pattern trên không hoạt động, thử parse thủ công từng INSERT
        if not records:
            records = self._parse_drivers_manual(sql_content)
        
        return records
    
    def _parse_drivers_manual(self, sql_content: str) -> List[Dict[str, Any]]:
        """
        Parse SQL drivers theo cách thủ công - xử lý từng INSERT statement
        
        Args:
            sql_content: Nội dung file SQL
        
        Returns:
            List của dictionaries chứa dữ liệu drivers
        """
        records = []
        
        # Tìm tất cả các INSERT INTO drivers statements - xử lý whitespace
        insert_pattern = r"INSERT\s+INTO\s+drivers\s*\((.*?)\)\s*SELECT"
        
        insert_statements = re.findall(insert_pattern, sql_content, re.DOTALL | re.IGNORECASE)
        
        for columns_str in insert_statements:
            # Parse columns
            columns = [col.strip().strip('"') for col in columns_str.split(',')]
            
            # Tìm phần SELECT tương ứng
            # Sử dụng pattern đơn giản hơn để tìm full INSERT statement
            full_pattern = r"INSERT\s+INTO\s+drivers\s*\(" + re.escape(columns_str) + r"\)\s+SELECT.*?WHERE\s+NOT\s+EXISTS"
            full_match = re.search(full_pattern, sql_content, re.DOTALL | re.IGNORECASE)
            
            if not full_match:
                continue
            
            full_statement = full_match.group(0)
            
            # Tìm phần SELECT đến WHERE
            select_part = full_statement[full_statement.find("SELECT"):]
            where_pos = select_part.find("WHERE NOT EXISTS")
            if where_pos == -1:
                continue
            
            select_values = select_part[:where_pos].strip()
            
            # Parse SELECT values - xử lý whitespace
            # Pattern: 'TB0013', '13', 'Trần Xuân Cường', '0972029223', '1084007116', '29H 70692', (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
            select_pattern = r"'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*\(SELECT\s+vendor_id\s+FROM\s+vendors\s+WHERE\s+vendor_code\s+=\s*'([^']*)'\),\s*(TRUE|FALSE)"
            select_matches = re.findall(select_pattern, select_values, re.IGNORECASE)
            
            for match in select_matches:
                driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_code, is_active_str = match
                
                # Tạo values - chỉ 7 values (không có vendor_code ở đây)
                values = [driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_code, is_active_str == 'TRUE']
                
                # Tạo record
                record = dict(zip(columns, values))
                records.append(record)
        
        return records
    
    def import_vendor_rates(self) -> bool:
        """
        Import dữ liệu vendor_rates
        
        Returns:
            True nếu thành công, False nếu thất bại
        """
        print("\n" + "="*60)
        print("IMPORT VENDOR RATES")
        print("="*60)
        
        try:
            # Kiểm tra xem có file SQL cho vendor_rates không
            sql_file = os.path.join(os.path.dirname(__file__), '../../scripts/import_vendor_rates.sql')
            
            if not os.path.exists(sql_file):
                print("Không tìm thấy file import_vendor_rates.sql, bỏ qua")
                return True
            
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Parse SQL
            records = self.parse_sql_insert(sql_content, 'vendor_rates')
            
            if not records:
                print("Không tìm thấy dữ liệu vendor_rates trong file SQL")
                return False
            
            print(f"Đã parse được {len(records)} records từ file SQL")
            
            # Import từng record
            for i, record in enumerate(records, 1):
                try:
                    # Kiểm tra xem vendor_rate đã tồn tại chưa
                    existing = self.supabase.table('vendor_rates').select('rate_id').eq('vendor_code', record.get('vendor_code')).eq('route_code', record.get('route_code')).execute()
                    
                    if existing.data:
                        # Update
                        result = self.supabase.table('vendor_rates').update(record).eq('vendor_code', record.get('vendor_code')).eq('route_code', record.get('route_code')).execute()
                        print(f"[{i}/{len(records)}] Updated: {record.get('vendor_code')} - {record.get('route_code')}")
                    else:
                        # Insert
                        result = self.supabase.table('vendor_rates').insert(record).execute()
                        print(f"[{i}/{len(records)}] Inserted: {record.get('vendor_code')} - {record.get('route_code')}")
                    
                    self.stats['vendor_rates']['success'] += 1
                    
                except Exception as e:
                    error_msg = f"Error importing vendor_rate: {str(e)}"
                    print(f"ERROR: {error_msg}")
                    self.stats['vendor_rates']['failed'] += 1
                    self.stats['vendor_rates']['errors'].append(error_msg)
            
            print(f"\n✓ Import vendor_rates hoàn tất: {self.stats['vendor_rates']['success']} thành công, {self.stats['vendor_rates']['failed']} thất bại")
            return True
            
        except Exception as e:
            error_msg = f"Lỗi khi import vendor_rates: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.stats['vendor_rates']['errors'].append(error_msg)
            return False
    
    def import_vendor_surcharges(self) -> bool:
        """
        Import dữ liệu vendor_surcharges
        
        Returns:
            True nếu thành công, False nếu thất bại
        """
        print("\n" + "="*60)
        print("IMPORT VENDOR SURCHARGES")
        print("="*60)
        
        try:
            # Kiểm tra xem có file SQL cho vendor_surcharges không
            sql_file = os.path.join(os.path.dirname(__file__), '../../scripts/import_vendor_surcharges.sql')
            
            if not os.path.exists(sql_file):
                print("Không tìm thấy file import_vendor_surcharges.sql, bỏ qua")
                return True
            
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Parse SQL
            records = self.parse_sql_insert(sql_content, 'vendor_surcharges')
            
            if not records:
                print("Không tìm thấy dữ liệu vendor_surcharges trong file SQL")
                return False
            
            print(f"Đã parse được {len(records)} records từ file SQL")
            
            # Import từng record
            for i, record in enumerate(records, 1):
                try:
                    # Kiểm tra xem vendor_surcharge đã tồn tại chưa
                    existing = self.supabase.table('vendor_surcharges').select('surcharge_id').eq('vendor_code', record.get('vendor_code')).eq('surcharge_type', record.get('surcharge_type')).execute()
                    
                    if existing.data:
                        # Update
                        result = self.supabase.table('vendor_surcharges').update(record).eq('vendor_code', record.get('vendor_code')).eq('surcharge_type', record.get('surcharge_type')).execute()
                        print(f"[{i}/{len(records)}] Updated: {record.get('vendor_code')} - {record.get('surcharge_type')}")
                    else:
                        # Insert
                        result = self.supabase.table('vendor_surcharges').insert(record).execute()
                        print(f"[{i}/{len(records)}] Inserted: {record.get('vendor_code')} - {record.get('surcharge_type')}")
                    
                    self.stats['vendor_surcharges']['success'] += 1
                    
                except Exception as e:
                    error_msg = f"Error importing vendor_surcharge: {str(e)}"
                    print(f"ERROR: {error_msg}")
                    self.stats['vendor_surcharges']['failed'] += 1
                    self.stats['vendor_surcharges']['errors'].append(error_msg)
            
            print(f"\n✓ Import vendor_surcharges hoàn tất: {self.stats['vendor_surcharges']['success']} thành công, {self.stats['vendor_surcharges']['failed']} thất bại")
            return True
            
        except Exception as e:
            error_msg = f"Lỗi khi import vendor_surcharges: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.stats['vendor_surcharges']['errors'].append(error_msg)
            return False
    
    def print_summary(self):
        """In tổng kết import"""
        print("\n" + "="*60)
        print("TỔNG KẾT IMPORT")
        print("="*60)
        
        for table, stats in self.stats.items():
            print(f"\n{table.upper()}:")
            print(f"  ✓ Thành công: {stats['success']}")
            print(f"  ✗ Thất bại: {stats['failed']}")
            if stats['errors']:
                print(f"  Lỗi:")
                for error in stats['errors'][:5]:  # Chỉ hiển thị 5 lỗi đầu tiên
                    print(f"    - {error}")
                if len(stats['errors']) > 5:
                    print(f"    ... và {len(stats['errors']) - 5} lỗi khác")
        
        print("\n" + "="*60)
    
    def run_all(self):
        """Chạy tất cả các import"""
        print("="*60)
        print("BẮT ĐẦU IMPORT DỮ LIỆU LÊN SUPABASE")
        print(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # Import theo thứ tự phụ thuộc
        self.import_customers()
        self.import_vendors()
        self.import_drivers()
        self.import_vendor_rates()
        self.import_vendor_surcharges()
        
        # In tổng kết
        self.print_summary()


def main():
    """Hàm chính"""
    try:
        importer = SupabaseImporter()
        importer.run_all()
        
        # Exit code dựa trên kết quả
        total_failed = sum(stats['failed'] for stats in importer.stats.values())
        sys.exit(0 if total_failed == 0 else 1)
        
    except Exception as e:
        print(f"\nFATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
