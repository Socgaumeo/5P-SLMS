#!/usr/bin/env python3
"""
Run database migration to add missing statuses
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.services.data_service import DataService

def run_migration():
    """Add missing DISPATCHED and IN_TRANSIT statuses"""
    
    data_service = DataService()
    conn = data_service._get_connection()
    cursor = conn.cursor()
    
    try:
        print("Adding missing statuses to master_statuses...")
        
        cursor.execute("""
            INSERT INTO master_statuses (status_code, name_vi, color_code, is_active) 
            VALUES 
                ('DISPATCHED', 'Đã điều xe', '#8B5CF6', TRUE),
                ('IN_TRANSIT', 'Đang vận chuyển', '#F59E0B', TRUE)
            ON CONFLICT (status_code) DO NOTHING;
        """)
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
        # Verify
        cursor.execute("SELECT status_code, name_vi FROM master_statuses ORDER BY status_code")
        statuses = cursor.fetchall()
        
        print("\nCurrent statuses in database:")
        for status in statuses:
            print(f"  - {status['status_code']}: {status['name_vi']}")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
