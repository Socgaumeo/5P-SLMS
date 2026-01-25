#!/bin/bash

# Script chạy tất cả các import dữ liệu lên Supabase
# Usage: ./run_all_imports.sh

echo "=========================================="
echo "CHẠY TẤT CẢ IMPORT DỮ LIỆU LÊN SUPABASE"
echo "=========================================="
echo ""

# Đường dẫn đến thư mục scripts
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Kiểm tra file .env
if [ ! -f "../../.env" ]; then
    echo "❌ Lỗi: Không tìm thấy file .env"
    echo "Vui lòng tạo file .env với các thông tin Supabase"
    exit 1
fi

echo "✅ Đã tìm thấy file .env"
echo ""

# Import customers, vendors, drivers từ SQL
echo "=========================================="
echo "BƯỚC 1: Import Customers, Vendors, Drivers"
echo "=========================================="
python3 import_to_supabase.py

if [ $? -ne 0 ]; then
    echo "❌ Import customers/vendors/drivers thất bại"
    exit 1
fi

echo ""
echo "✅ Import customers/vendors/drivers hoàn tất"
echo ""

# Import vendor rates từ Excel (nếu có file)
echo "=========================================="
echo "BƯỚC 2: Import Vendor Rates & Surcharges"
echo "=========================================="

# Kiểm tra xem có file vendor_rates không
VENDOR_RATES_FILE="../../vendor_rates/Tam_bảo_092025.xlsx"

if [ -f "$VENDOR_RATES_FILE" ]; then
    echo "📁 Tìm thấy file: $VENDOR_RATES_FILE"
    echo ""
    
    python3 import_vendor_rates_supabase.py "$VENDOR_RATES_FILE" "Tam Bảo"
    
    if [ $? -ne 0 ]; then
        echo "❌ Import vendor rates/surcharges thất bại"
        exit 1
    fi
    
    echo ""
    echo "✅ Import vendor rates/surcharges hoàn tất"
else
    echo "⚠️  Không tìm thấy file vendor_rates, bỏ qua bước này"
fi

echo ""
echo "=========================================="
echo "✅ TẤT CẢ IMPORT ĐÃ HOÀN TẤT"
echo "=========================================="
echo ""
echo "Kiểm tra dữ liệu trên Supabase Dashboard:"
echo "https://app.supabase.com/project/vpmsytbbsxmtdicnkytv/editor"
