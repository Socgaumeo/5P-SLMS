# Phase 4: Learning & Profile Auto-Update

## Context Links
- Parent: [plan.md](plan.md)
- Depends on: [Phase 1](phase-01-customer-profile-table-data-mining.md)

## Overview
- **Date**: 2026-03-06
- **Priority**: MEDIUM
- **Status**: pending
- **Description**: Automatically update customer profiles after each job creation/completion. Implement simple anomaly detection to flag unusual orders. Periodic full refresh for data consistency.

## Key Insights
- Jobs created via AI chat go through `_execute_create_booking()` in `conversation_manager.py` and `create_from_chat()` in `jobs.py` -- hook into post-creation
- Jobs completed via `update_status` when status changes to COMPLETED -- hook into status update
- Anomaly detection: compare new booking fields vs profile averages (simple threshold)
- No need for cron/scheduler: trigger profile update inline after job events

## Requirements

### Functional
- F1: After job created, update customer profile with new data point
- F2: After job completed, update stats (revenue, total_jobs)
- F3: Anomaly flag when booking deviates significantly from profile (new route, unusual weight)
- F4: Anomaly info returned in AI chat response for operator awareness

### Non-Functional
- NF1: Profile update adds <200ms to job creation (async fire-and-forget OK)
- NF2: Anomaly detection is simple threshold-based, not ML
- NF3: No data loss if profile update fails (non-blocking)

## Architecture

### Post-Job-Creation Hook
```
User confirms booking in chat
        |
        v
  _execute_create_booking() creates job in DB (existing)
        |
        v
  NEW: call update_profile_on_job_created(customer_id, job_data)
        |
        v
  Increment route/cargo/vehicle counts in JSONB
  Update stats.total_jobs, stats.last_job
  Check anomalies vs profile
        |
        v
  Return anomaly_flags (if any) to include in AI response
```

### Anomaly Detection Logic
Adjusted threshold comparisons (avoid false positives):
- **New route**: pickup/delivery not in `frequent_routes` AND customer has ≥10 jobs -> flag "Tuyen moi, chua co lich su"
- **Unusual weight**: weight > **3x** `avg_weight_kg` for this cargo type AND diff > 500kg -> flag "Trong luong bat thuong (X kg vs trung binh Y kg)"
- **Unusual vehicle**: vehicle_type not in `preferred_vehicles` AND customer has ≥10 jobs -> flag "Loai xe khac thuong le"
- **Off-hours booking**: booking time outside `booking_patterns.peak_days` -> info only, no flag
- **Minimum data requirement**: Skip anomaly detection if customer has <**10** jobs (was 5, too aggressive)
<!-- Updated: Improvement Merge - Adjusted anomaly thresholds: 3x weight + min 10 jobs + diff > 500kg -->

### Incremental Update Strategy
Instead of re-aggregating entire history, do incremental JSONB updates:
```python
# Increment route count
profile.frequent_routes -> find matching route -> count += 1
# Or append new route if not found
# Re-sort by count DESC, keep top 10
```

## Related Code Files

### Files to Modify
- `backend/app/services/customer-profile-service.py` - Add incremental update + anomaly detection methods
- `backend/app/ai/memory/conversation_manager.py` - Hook after `_execute_create_booking()`
- `backend/app/api/jobs.py` - Hook after status update to COMPLETED

### Files to Read (Reference)
- `backend/app/ai/unified_processor.py` - Alternative execution path

## Implementation Steps

1. **Add incremental update methods** to `customer-profile-service.py`
   - `update_on_job_created(customer_id, job_data)`:
     - Extract route (origin, destination), cargo_type, vehicle_type from job_data
     - Fetch current profile
     - Update `frequent_routes`: find or append, increment count, sort by count DESC, keep top 10
     - Update `common_cargo_types`: same pattern
     - Update `preferred_vehicles`: same pattern
     - Update `stats.total_jobs += 1`, `stats.last_job = today`
     - Update `updated_at`, `last_aggregated_at`
     - Upsert to Supabase
   - `update_on_job_completed(customer_id, job_data)`:
     - Update `stats.total_revenue += job.total_revenue`
     - Recalculate `stats.avg_order_value`

2. **Add anomaly detection** to `customer-profile-service.py`
   - `detect_anomalies(customer_id, booking_data) -> list[str]`:
     - Fetch profile
     - If no profile or <**10** jobs: return empty (not enough data)
     - Check route: if not in top 10 frequent_routes AND total_jobs ≥ 10 -> "Tuyen moi"
     - Check weight: if > **3x** avg for cargo type AND diff > **500kg** -> "Trong luong bat thuong (X kg vs trung binh Y kg)"
     - Check vehicle: if not in preferred_vehicles AND total_jobs ≥ 10 -> "Loai xe khac thuong le"
     - Return list of flag strings
<!-- Updated: Improvement Merge - Adjusted thresholds: 3x, min 10 jobs, diff > 500kg -->

3. **Hook into conversation_manager.py**
   - In `_execute_create_booking()`, after successful job creation:
     ```python
     # Fire-and-forget profile update
     try:
         from app.services.customer_profile_service import CustomerProfileService
         profile_svc = CustomerProfileService()
         await profile_svc.update_on_job_created(customer_id, job_data)
         anomalies = await profile_svc.detect_anomalies(customer_id, job_data)
         if anomalies:
             response += f"\n\n⚠ Luu y: {', '.join(anomalies)}"
     except Exception as e:
         logger.warning(f"Profile update failed (non-blocking): {e}")
     ```

4. **Hook into jobs.py status update**
   - In the status update endpoint, when new status is COMPLETED:
     ```python
     if new_status == "COMPLETED":
         try:
             profile_svc = CustomerProfileService()
             await profile_svc.update_on_job_completed(customer_id, job_data)
         except Exception:
             pass  # Non-blocking
     ```

5. **Add periodic full refresh** (optional, low priority)
   - Admin endpoint `POST /api/customer-profiles/refresh-all` (from Phase 1)
   - Can be called manually or via external cron if needed
   - Re-aggregates from scratch to fix any drift from incremental updates

## Todo List
- [ ] Implement `update_on_job_created()` in profile service
- [ ] Implement `update_on_job_completed()` in profile service
- [ ] Implement `detect_anomalies()` in profile service
- [ ] Hook profile update into `_execute_create_booking()` in conversation_manager.py
- [ ] Hook profile update into job status update endpoint in jobs.py
- [ ] Test: create job via chat, verify profile updated
- [ ] Test: create job with new route, verify anomaly flag in response
- [ ] Test: complete job, verify revenue stats updated
- [ ] Test: profile update failure doesn't break job creation

## Success Criteria
- Profile auto-updates after each job creation (route/cargo/vehicle counts increment)
- Profile stats update after job completion (revenue, total_jobs)
- Anomaly flags appear in AI response when booking deviates from history
- Job creation/completion never fails due to profile update errors

## Risk Assessment
- **Risk**: Incremental updates cause data drift vs full aggregation -> **Mitigation**: periodic full refresh endpoint, compare counts
- **Risk**: Concurrent job creation causes race condition on profile JSONB -> **Mitigation**: Use Supabase RPC function with `SELECT ... FOR UPDATE` row lock for atomic JSONB updates:
  ```sql
  CREATE OR REPLACE FUNCTION update_customer_profile_atomic(
    p_customer_id BIGINT,
    p_route JSONB,
    p_cargo JSONB,
    p_vehicle JSONB
  ) RETURNS VOID AS $$
  BEGIN
    -- Lock row first
    PERFORM 1 FROM customer_profiles WHERE customer_id = p_customer_id FOR UPDATE;
    -- Then do incremental JSONB update
    UPDATE customer_profiles SET
      frequent_routes = update_jsonb_array(frequent_routes, p_route),
      common_cargo_types = update_jsonb_array(common_cargo_types, p_cargo),
      preferred_vehicles = update_jsonb_array(preferred_vehicles, p_vehicle),
      updated_at = NOW()
    WHERE customer_id = p_customer_id;
  END;
  $$ LANGUAGE plpgsql;
  ```
<!-- Updated: Improvement Merge - Race condition fix with Supabase RPC + FOR UPDATE row lock -->
- **Risk**: Anomaly flags annoying for intentionally different bookings -> **Mitigation**: flags are informational only, don't block execution

## Security Considerations
- Profile updates happen server-side only, no client input to profile data
- Anomaly flags are advisory, not access-control
- Non-blocking pattern ensures core booking flow always succeeds

## Next Steps
- Monitor profile accuracy over time
- Consider more sophisticated pattern detection if customer base grows >100
- Potential: expose anomaly history in admin dashboard
