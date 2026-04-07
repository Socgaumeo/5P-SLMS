#!/usr/bin/env python3
"""
Migrate data from old Supabase project to new Singapore-hosted project.
"""

from supabase import create_client, Client
import json
from datetime import datetime, date
from decimal import Decimal

# Old Supabase (ap-south-1 Mumbai)
OLD_URL = "https://vpmsytbbsxmtdicnkytv.supabase.co"
OLD_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZwbXN5dGJic3htdGRpY25reXR2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTE1MTA0NCwiZXhwIjoyMDg0NzI3MDQ0fQ.q3pEIxoqaH0tM8SgEOYAgaK4T4fTvaTXzk367tixuHA"

# New Supabase (ap-southeast-1 Singapore)
NEW_URL = "https://ooixntyflwmjaryxwakx.supabase.co"
NEW_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9vaXhudHlmbHdtamFyeXh3YWt4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDgxMzYyOSwiZXhwIjoyMDg2Mzg5NjI5fQ.SOEp-m3ZFyYcVUcafUoQZU9u145G1diX8Lr8h0jsbik"

# Tables to migrate (in dependency order)
TABLES_ORDER = [
    # Master tables first (no dependencies)
    "master_service_types",
    "master_statuses",
    "master_vehicle_types",
    "master_routes",
    "services",
    "rate_file_references",
    # Core tables
    "users",
    "customers",
    "vendors",
    "employees",
    "drivers",
    "vehicles",
    # Operation tables
    "jobs",
    "job_services",
    "job_costs",
    # Automation tables
    "message_templates",
    "automation_logs",
    "activity_logs",
    # Rates tables
    "vendor_rates",
    "vendor_surcharges",
    "customer_rates",
    "customer_surcharges",
]


def json_serializer(obj):
    """Handle datetime and Decimal serialization"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def export_table(client: Client, table_name: str) -> list:
    """Export all data from a table"""
    try:
        result = client.table(table_name).select("*").execute()
        print(f"  ✓ Exported {len(result.data)} rows from {table_name}")
        return result.data
    except Exception as e:
        print(f"  ✗ Error exporting {table_name}: {e}")
        return []


def import_table(client: Client, table_name: str, data: list) -> int:
    """Import data into a table"""
    if not data:
        print(f"  - Skipping {table_name} (no data)")
        return 0

    success_count = 0

    # Insert in batches of 100
    batch_size = 100
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        try:
            # Remove generated columns that can't be inserted
            cleaned_batch = []
            for row in batch:
                cleaned_row = {k: v for k, v in row.items()
                             if k not in ['profit', 'buying_amount', 'selling_amount']}  # Generated cols
                cleaned_batch.append(cleaned_row)

            result = client.table(table_name).upsert(cleaned_batch).execute()
            success_count += len(result.data) if result.data else len(cleaned_batch)
        except Exception as e:
            print(f"  ✗ Batch error in {table_name}: {e}")
            # Try inserting one by one
            for row in batch:
                try:
                    cleaned_row = {k: v for k, v in row.items()
                                  if k not in ['profit', 'buying_amount', 'selling_amount']}
                    client.table(table_name).upsert(cleaned_row).execute()
                    success_count += 1
                except Exception as e2:
                    print(f"    ✗ Row error: {e2}")

    print(f"  ✓ Imported {success_count}/{len(data)} rows to {table_name}")
    return success_count


def main():
    print("=" * 60)
    print("SUPABASE MIGRATION: Mumbai → Singapore")
    print("=" * 60)

    # Connect to both databases
    print("\n[1/4] Connecting to databases...")
    old_client = create_client(OLD_URL, OLD_SERVICE_KEY)
    new_client = create_client(NEW_URL, NEW_SERVICE_KEY)
    print("  ✓ Connected to old Supabase (Mumbai)")
    print("  ✓ Connected to new Supabase (Singapore)")

    # Export all data
    print("\n[2/4] Exporting data from old database...")
    all_data = {}
    for table in TABLES_ORDER:
        data = export_table(old_client, table)
        all_data[table] = data

    # Save backup to file
    print("\n[3/4] Saving backup...")
    backup_file = f"/tmp/supabase_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, default=json_serializer, ensure_ascii=False, indent=2)
    print(f"  ✓ Backup saved to: {backup_file}")

    # Import to new database
    print("\n[4/4] Importing data to new database...")
    for table in TABLES_ORDER:
        if table in all_data:
            import_table(new_client, table, all_data[table])

    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE!")
    print("=" * 60)

    # Summary
    print("\nSummary:")
    for table, data in all_data.items():
        print(f"  {table}: {len(data)} rows")


if __name__ == "__main__":
    main()
