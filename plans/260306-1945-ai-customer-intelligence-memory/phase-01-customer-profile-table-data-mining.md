# Phase 1: Customer Profile Table + Data Mining

## Context Links
- Parent: [plan.md](plan.md)
- Dependencies: None (foundation phase)

## Overview
- **Date**: 2026-03-06
- **Priority**: HIGH
- **Status**: pending
- **Description**: Create `customer_profiles` table with JSONB columns, write aggregation script to mine existing jobs/rates data, expose API endpoints for profile CRUD.

## Key Insights
- Supabase supports JSONB natively with GIN indexes for fast lookups
- Existing `jobs` + `job_services` tables contain route, cargo, vehicle, date patterns
- `customer_rates` / `vendor_rates` contain pricing preferences per route
- ~10-50 active customers -- simple SQL aggregation is sufficient, no need for background workers

## Requirements

### Functional
- F1: `customer_profiles` table stores structured intelligence per customer
- F2: Aggregation script mines jobs/rates for top routes, cargo types, vehicles, patterns
- F3: API endpoints: GET profile, PUT update profile, POST trigger refresh
- F4: Manual notes field for operator-added context (e.g., "always needs POD")

### Non-Functional
- NF1: Profile refresh completes in <5s for any customer
- NF2: JSONB profile size stays under 10KB per customer
- NF3: No impact on existing API response times

## Architecture

### New Table: `customer_profiles`
```sql
CREATE TABLE customer_profiles (
  id BIGSERIAL PRIMARY KEY,
  customer_id BIGINT NOT NULL REFERENCES customers(customer_id) UNIQUE,
  -- Aggregated intelligence (JSONB)
  frequent_routes JSONB DEFAULT '[]',
  -- [{"origin": "Ha Noi", "destination": "Hai Phong", "count": 15, "last_used": "2026-03-01"}]
  common_cargo_types JSONB DEFAULT '[]',
  -- [{"cargo_type": "PCB", "avg_weight_kg": 500, "count": 10}]
  preferred_vehicles JSONB DEFAULT '[]',
  -- [{"vehicle_type": "5T", "count": 8}]
  booking_patterns JSONB DEFAULT '{}',
  -- {"avg_bookings_per_month": 12, "peak_days": ["Monday","Tuesday"], "avg_lead_time_hours": 24}
  preferred_vendors JSONB DEFAULT '[]',
  -- [{"vendor_code": "VD001", "vendor_name": "ABC Trans", "route": "HN-HP", "count": 5}]
  special_requirements TEXT DEFAULT '',
  -- Free-text notes from operators
  delivery_requirements JSONB DEFAULT '{}',
  -- {"needs_pod": true, "delivery_before": "08:00", "temperature_control": false, "packing_required": false}
  payment_terms JSONB DEFAULT '{}',
  -- {"method": "transfer", "days": 30, "cod": false, "notes": "Thanh toán cuối tháng"}
  custom_notes JSONB DEFAULT '{}',
  -- {"key": "value"} for any other customer-specific info
  <!-- Updated: Validation Session 1 - Added delivery_requirements, payment_terms, custom_notes JSONB fields -->
  stats JSONB DEFAULT '{}',
  -- {"total_jobs": 50, "total_revenue": 150000000, "avg_order_value": 3000000, "first_job": "2025-06-01", "last_job": "2026-03-05"}
  -- Metadata
  last_aggregated_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_customer_profiles_customer_id ON customer_profiles(customer_id);

-- GIN indexes for JSONB fast lookups
CREATE INDEX idx_cp_frequent_routes ON customer_profiles USING GIN (frequent_routes);
CREATE INDEX idx_cp_common_cargo ON customer_profiles USING GIN (common_cargo_types);
CREATE INDEX idx_cp_preferred_vehicles ON customer_profiles USING GIN (preferred_vehicles);
CREATE INDEX idx_cp_preferred_vendors ON customer_profiles USING GIN (preferred_vendors);
CREATE INDEX idx_cp_last_aggregated ON customer_profiles(last_aggregated_at);
```
<!-- Updated: Improvement Merge - Added 4 GIN indexes + 1 timestamp index for JSONB query performance -->

### Data Flow
```
Existing tables (jobs, job_services, customer_rates)
        |
        v
  Aggregation Script (SQL queries)
        |
        v
  customer_profiles table (JSONB)
        |
        v
  API endpoints (read/update)
```

## Related Code Files

### Files to Create
- `backend/app/services/customer-profile-service.py` - Profile CRUD + aggregation logic
- `backend/app/api/customer-profiles.py` - REST API endpoints
- `backend/scripts/aggregate-customer-profiles.py` - One-time migration + manual refresh script
- `backend/scripts/create-customer-profiles-table.sql` - DDL for Supabase

### Files to Modify
- `backend/main.py` - Register new router

## Implementation Steps

1. **Create DDL script** (`create-customer-profiles-table.sql`)
   - Define table with JSONB columns as shown in Architecture
   - Add UNIQUE constraint on customer_id
   - Run via Supabase SQL Editor or migration script

2. **Create profile service** (`customer-profile-service.py`)
   - `get_profile(customer_id)` - Fetch profile from Supabase
   - `update_special_requirements(customer_id, notes)` - Update operator notes
   - `aggregate_profile(customer_id)` - Run aggregation queries:
     - Top 5 routes: `SELECT origin_address, dest_address, COUNT(*) FROM job_services WHERE job_id IN (SELECT job_id FROM jobs WHERE customer_id=X) GROUP BY 1,2 ORDER BY 3 DESC LIMIT 5`
     - Common cargo: `SELECT cargo_type, AVG(weight_kg), COUNT(*) FROM job_services WHERE ... GROUP BY 1 ORDER BY 3 DESC LIMIT 5`
     - Preferred vehicles: `SELECT vehicle_type, COUNT(*) FROM job_services WHERE ... GROUP BY 1 ORDER BY 2 DESC LIMIT 5`
     - Booking patterns: day-of-week distribution, avg lead time
     - Stats: total jobs, revenue, avg order value
   - `aggregate_all_profiles()` - Loop all active customers

3. **Create API endpoints** (`customer-profiles.py`)
   - `GET /api/customer-profiles/{customer_id}` - Return profile
   - `PUT /api/customer-profiles/{customer_id}/notes` - Update special_requirements
   - `POST /api/customer-profiles/{customer_id}/refresh` - Trigger re-aggregation
   - `POST /api/customer-profiles/refresh-all` - Admin: refresh all profiles

4. **Create migration script** (`aggregate-customer-profiles.py`)
   - One-time script to populate profiles for all existing customers
   - Uses the service's `aggregate_all_profiles()`

5. **Create Excel import script** (`import-customer-profiles-from-excel.py`)
   - Accept Excel file path as argument
   - Column mapping (8 columns):
     - `customer_code` → match to existing customers table
     - `cargo_types` → `common_cargo_types` JSONB array
     - `frequent_routes` → `frequent_routes` JSONB (parse "origin -> destination" format)
     - `preferred_vehicles` → `preferred_vehicles` JSONB array
     - `delivery_requirements` → `delivery_requirements` JSONB (POD, delivery_before, temperature_control)
     - `payment_terms` → `payment_terms` JSONB (method, days, cod, notes)
     - `special_requirements` → `special_requirements` TEXT
     - `custom_notes` → `custom_notes` JSONB
   - **Idempotent**: UPSERT on customer_id — safe to re-run
   - Skip rows with unmatched customer_code, log warnings
   - Use `openpyxl` library for .xlsx reading
<!-- Updated: Improvement Merge - Added detailed Excel import spec with 8-column mapping, idempotent -->

6. **Register router** in `backend/main.py`
   - `app.include_router(customer_profiles_router, prefix="/api/customer-profiles")`

## Todo List
- [ ] Create `customer_profiles` table DDL and run in Supabase
- [ ] Implement `customer-profile-service.py` with aggregation queries
- [ ] Implement `customer-profiles.py` API endpoints
- [ ] Write `aggregate-customer-profiles.py` migration script
- [ ] Write Excel import script for historical customer data
- [ ] Register router in `main.py`
- [ ] Test: create profile, aggregate, verify JSONB content
- [ ] Test: API endpoints return correct data
- [ ] Test: Excel import populates profiles correctly
<!-- Updated: Validation Session 1 - Added Excel import script + expanded JSONB schema -->

## Success Criteria
- Table exists in Supabase with proper indexes
- Aggregation script populates profiles for all active customers
- GET endpoint returns populated profile with routes, cargo, vehicles
- PUT notes endpoint persists operator notes
- Profile refresh completes in <5s per customer

## Risk Assessment
- **Risk**: Complex JOIN queries may fail on Supabase's query builder -> **Mitigation**: Use RPC functions or raw SQL via `supabase.rpc()`
- **Risk**: Empty profiles for new customers -> **Mitigation**: Return sensible defaults, don't error on empty

## Security Considerations
- All endpoints require JWT auth (existing middleware)
- Profile data is not PII-sensitive (routes, cargo types)
- Special requirements notes should be sanitized for XSS

## Next Steps
- Phase 2 consumes profiles in AI prompt context
