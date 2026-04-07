# Phase 1: Fix Bot Quotation Auth - Direct DB Insert

## Context Links
- Bot processor: `backend/app/ai/unified_processor.py` (line 797-861)
- Admin API auth: `backend/app/api/admin.py` (line 36-38)
- Supabase client: `backend/app/db/supabase_client.py`
- Admin buying-rates insert: `backend/app/api/admin.py` (line 658-697)
- Admin selling-rates insert: `backend/app/api/admin.py` (line 536-571)

## Overview
- **Priority**: P1 (bot quotation creation completely broken)
- **Status**: pending
- **Description**: Bot's `_execute_create_quotation` calls `/api/admin/buying-rates` and `/api/admin/selling-rates` via httpx without auth headers. Admin router requires `require_manager_or_admin` dependency. Result: 401/403 every time.

## Key Insights
- The admin API endpoints just do `get_supabase().table('vendor_rates').insert(...)` and `get_supabase().table('customer_rates').insert(...)`
- Bot already has access to `get_supabase()` (same Python process)
- Direct DB insert is simpler, faster, and avoids auth entirely
- Vendor/customer lookup calls (`/api/jobs/lookup/...`) do NOT require admin auth, so those can stay as HTTP calls OR also be converted to direct DB

## Requirements
### Functional
- Bot can create buying rates (vendor_rates table) without auth
- Bot can create selling rates (customer_rates table) without auth
- Vendor/customer name lookup still works
- Success/error messages unchanged

### Non-functional
- No HTTP round-trip for DB insert (faster)
- No auth dependency for internal bot operations

## Architecture
```
Before: Bot -> httpx POST /api/admin/buying-rates -> auth check (FAIL) -> supabase insert
After:  Bot -> supabase.table('vendor_rates').insert(...) directly
```

## Related Code Files
- **Modify**: `backend/app/ai/unified_processor.py` (method `_execute_create_quotation`, lines 797-861)
- No new files needed

## Implementation Steps

### 1. Add supabase import at top of unified_processor.py
Check if `get_supabase` is already imported. If not, add:
```python
from app.db.supabase_client import get_supabase
```

### 2. Rewrite `_execute_create_quotation` method (line 797-861)

Replace the entire method. Key changes:
- Remove `client` and `api_base` params (httpx client no longer needed for this)
- Keep vendor/customer name lookup (convert to direct DB query too)
- Insert directly into `vendor_rates` or `customer_rates` table
- Keep same return format

```python
async def _execute_create_quotation(self, state, client, api_base):
    """Create a quotation (buying or selling rate) via direct DB insert."""
    from datetime import date as date_type
    entities = state.entities
    quote_type = entities.get("quote_type", "buying").lower()

    # Lookup vendor/customer by name
    vendor_id = None
    customer_id = None
    db = get_supabase()

    if quote_type == "buying" and entities.get("vendor_name"):
        result = db.table('vendors').select('vendor_id, short_name, company_name').eq('is_active', True).execute()
        for v in result.data or []:
            name_lower = entities["vendor_name"].lower()
            if name_lower in (v.get("short_name") or "").lower() or \
               name_lower in (v.get("company_name") or "").lower():
                vendor_id = v.get("vendor_id")
                break

    elif quote_type == "selling" and entities.get("customer_name"):
        result = db.table('customers').select('customer_id, short_name, company_name, customer_code').eq('is_active', True).execute()
        for c in result.data or []:
            name_lower = entities["customer_name"].lower()
            if name_lower in (c.get("short_name") or "").lower() or \
               name_lower in (c.get("company_name") or "").lower() or \
               name_lower in (c.get("customer_code") or "").lower():
                customer_id = c.get("customer_id")
                break

    # Build insert data
    insert_data = {
        'price': entities.get("price"),
        'currency': entities.get("currency", "VND"),
        'unit': entities.get("unit", "TRIP"),
        'vehicle_type': entities.get("vehicle_type"),
        'origin_province': entities.get("origin_province"),
        'destination_province': entities.get("destination_province"),
        'notes': entities.get("sub_route") or entities.get("notes"),
        'rate_type': entities.get("rate_type", "STANDARD"),
        'is_active': True,
        'effective_date': date_type.today().isoformat(),
        'service_type_code': entities.get("service_type_code"),
    }

    # Remove None values
    insert_data = {k: v for k, v in insert_data.items() if v is not None}

    if quote_type == "buying":
        if not vendor_id:
            return {"success": False, "response": f"Khong tim thay NCC '{entities.get('vendor_name')}'. Vui long tao NCC truoc."}
        insert_data["vendor_id"] = vendor_id
        table = 'vendor_rates'
    else:
        if not customer_id:
            return {"success": False, "response": f"Khong tim thay KH '{entities.get('customer_name')}'. Vui long tao KH truoc."}
        insert_data["customer_id"] = customer_id
        table = 'customer_rates'

    try:
        result = db.table(table).insert(insert_data).execute()
        if result.data:
            label = "mua" if quote_type == "buying" else "ban"
            route = ""
            if entities.get("origin_province") and entities.get("destination_province"):
                route = f" {entities['origin_province']}->{entities['destination_province']}"
            price = entities.get("price", 0)
            return {
                "success": True,
                "response": f"Da tao bao gia {label}{route} | {price:,.0f} VND thanh cong!"
            }
        return {"success": False, "response": "Loi tao bao gia: khong co du lieu tra ve"}
    except Exception as e:
        logger.error(f"[UNIFIED] Direct DB insert failed: {e}")
        return {"success": False, "response": f"Loi tao bao gia: {str(e)}"}
```

**Note**: Keep the method signature `(self, state, client, api_base)` unchanged to avoid breaking the caller at line 721. The `client` and `api_base` params are simply unused now.

### 3. Keep unicode response messages
The code above uses ASCII for clarity. In actual implementation, use original Vietnamese with diacritics matching existing messages:
- `"Khong tim thay NCC"` -> `"Khong tim thay NCC"` (keep original `f"Không tìm thấy NCC..."`)
- Same for success messages

## Todo List
- [ ] Check if `get_supabase` already imported in unified_processor.py
- [ ] Rewrite `_execute_create_quotation` to use direct Supabase insert
- [ ] Keep method signature compatible with caller at line 721
- [ ] Test: bot creates buying rate successfully
- [ ] Test: bot creates selling rate successfully
- [ ] Test: error when vendor not found

## Success Criteria
- Bot can create buying/selling quotations without 401 error
- Rates appear in `vendor_rates`/`customer_rates` tables
- Error messages for missing vendor/customer unchanged

## Risk Assessment
- **Low**: Direct DB insert is what the admin API does anyway
- **RLS**: Supabase client uses `service_role` key, bypasses RLS. Same as admin API.

## Security Considerations
- Bot operations are server-side only, no user-facing auth bypass
- Service role key already used throughout the codebase
