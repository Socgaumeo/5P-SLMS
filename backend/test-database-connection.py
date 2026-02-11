#!/usr/bin/env python3
"""
Test Database Connection Script
Tests Supabase PostgreSQL connectivity and diagnoses issues.
Usage: python3 test-database-connection.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_connection():
    """Test database connection and provide diagnostics"""
    print("=" * 60)
    print("5P-SLMS Database Connection Test")
    print("=" * 60)
    print()

    # Step 1: Load configuration
    print("Step 1: Loading configuration...")
    try:
        from app.core.config import settings
        db_url = settings.DATABASE_URL

        # Parse URL to hide password
        import re
        safe_url = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', db_url)
        print(f"✓ Configuration loaded")
        print(f"  Database URL: {safe_url}")
        print()
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return False

    # Step 2: Test DNS resolution
    print("Step 2: Testing DNS resolution...")
    try:
        # Extract hostname from URL
        import re
        match = re.search(r'@([^:]+):', db_url)
        if match:
            hostname = match.group(1)
            print(f"  Hostname: {hostname}")

            import socket
            ip = socket.gethostbyname(hostname)
            print(f"✓ DNS resolution successful: {ip}")
            print()
        else:
            print("✗ Could not parse hostname from DATABASE_URL")
            return False
    except socket.gaierror as e:
        print(f"✗ DNS resolution failed: {e}")
        print()
        print("DIAGNOSIS:")
        print("  - Supabase project may be paused or deleted")
        print("  - Database URL may be incorrect")
        print("  - Network connectivity issue")
        print()
        print("SOLUTIONS:")
        print("  1. Check Supabase dashboard: https://supabase.com/dashboard")
        print("  2. Verify project is active and not paused")
        print("  3. Get correct DATABASE_URL from project settings")
        print("  4. Update backend/app/core/config.py or create .env file")
        print()
        return False
    except Exception as e:
        print(f"✗ Unexpected error during DNS test: {e}")
        return False

    # Step 3: Test database connection
    print("Step 3: Testing database connection...")
    try:
        from app.db.session import get_connection
        conn = get_connection()
        print("✓ Database connection successful!")
        conn.close()
        print()
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print()
        print("DIAGNOSIS:")
        print("  - Database credentials may be incorrect")
        print("  - Firewall blocking connection")
        print("  - Database server may be down")
        print()
        return False

    # Step 4: Test search query
    print("Step 4: Testing search query...")
    try:
        from app.db.session import get_db_context

        with get_db_context() as db:
            db.execute("""
                SELECT COUNT(*) as total_jobs
                FROM jobs
            """)
            result = db.fetchone()
            job_count = result['total_jobs'] if result else 0

            print(f"✓ Search query successful")
            print(f"  Total jobs in database: {job_count}")
            print()

            # Test actual search
            search_term = "%0008%"
            db.execute("""
                SELECT j.job_id, j.job_no, j.status_code,
                       c.customer_code, c.company_name
                FROM jobs j
                LEFT JOIN customers c ON j.customer_id = c.customer_id
                WHERE j.job_no ILIKE %s
                LIMIT 5
            """, (search_term,))

            results = db.fetchall()
            if results:
                print(f"  Found {len(results)} jobs matching '0008':")
                for r in results[:3]:
                    print(f"    - {r['job_no']} | {r['customer_code']} | {r['status_code']}")
            else:
                print("  No jobs found matching '0008' (database may be empty)")
            print()

    except Exception as e:
        print(f"✗ Search query failed: {e}")
        print()
        return False

    # All tests passed
    print("=" * 60)
    print("✓ ALL TESTS PASSED - Database connection is working!")
    print("=" * 60)
    print()
    print("If search still not working in frontend:")
    print("  1. Restart backend server: kill existing uvicorn process and restart")
    print("  2. Clear browser cache and hard refresh (Cmd+Shift+R)")
    print("  3. Check browser console for errors")
    print()
    return True


if __name__ == "__main__":
    try:
        success = test_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
