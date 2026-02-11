#!/usr/bin/env python3
"""
Run database migration to add missing statuses using Supabase client
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(__file__))

from supabase import create_client


def run_migration():
    """Add missing statuses to master_statuses"""

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")
        return

    client = create_client(supabase_url, supabase_key)

    # Statuses organized by category
    statuses = [
        # Common
        {'status_code': 'PENDING', 'name_vi': 'Chờ xử lý', 'color_code': '#FEF3C7', 'is_active': True},
        {'status_code': 'CONFIRMED', 'name_vi': 'Đã xác nhận', 'color_code': '#DBEAFE', 'is_active': True},
        {'status_code': 'CANCELLED', 'name_vi': 'Đã hủy', 'color_code': '#DC2626', 'is_active': True},
        # Transport
        {'status_code': 'DISPATCHED', 'name_vi': 'Đã điều xe', 'color_code': '#8B5CF6', 'is_active': True},
        {'status_code': 'IN_TRANSIT', 'name_vi': 'Đang vận chuyển', 'color_code': '#F59E0B', 'is_active': True},
        # General
        {'status_code': 'ASSIGNED', 'name_vi': 'Đã phân công', 'color_code': '#4F46E5', 'is_active': True},
        {'status_code': 'IN_PROGRESS', 'name_vi': 'Đang thực hiện', 'color_code': '#F59E0B', 'is_active': True},
        {'status_code': 'COMPLETED', 'name_vi': 'Hoàn thành', 'color_code': '#059669', 'is_active': True},
        # Warehouse-specific
        {'status_code': 'WHS_RECEIVED', 'name_vi': 'Đã nhập kho', 'color_code': '#2563EB', 'is_active': True},
        {'status_code': 'WHS_PROCESSING', 'name_vi': 'Đang xử lý kho', 'color_code': '#D97706', 'is_active': True},
        {'status_code': 'WHS_RELEASED', 'name_vi': 'Đã xuất kho', 'color_code': '#059669', 'is_active': True},
        # Customs-specific
        {'status_code': 'CUS_SUBMITTED', 'name_vi': 'Đã nộp hồ sơ', 'color_code': '#4F46E5', 'is_active': True},
        {'status_code': 'CUS_PROCESSING', 'name_vi': 'Đang xử lý HQ', 'color_code': '#D97706', 'is_active': True},
        {'status_code': 'CUS_APPROVED', 'name_vi': 'Đã thông quan', 'color_code': '#059669', 'is_active': True},
    ]

    try:
        print("Adding/updating statuses in master_statuses...")

        for status in statuses:
            result = client.table('master_statuses').upsert(
                status, on_conflict='status_code'
            ).execute()
            print(f"  + {status['status_code']}: {status['name_vi']}")

        print("\n✅ Migration completed!")

        # Verify
        result = client.table('master_statuses').select('status_code, name_vi').order('status_code').execute()
        print("\nCurrent statuses:")
        for row in result.data:
            print(f"  - {row['status_code']}: {row['name_vi']}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    run_migration()
