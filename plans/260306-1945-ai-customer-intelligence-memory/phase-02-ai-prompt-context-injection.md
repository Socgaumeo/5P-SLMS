# Phase 2: AI Prompt Context Injection

## Context Links
- Parent: [plan.md](plan.md)
- Depends on: [Phase 1](phase-01-customer-profile-table-data-mining.md)

## Overview
- **Date**: 2026-03-06
- **Priority**: HIGH
- **Status**: pending
- **Description**: When AI detects a customer in chat, fetch their profile and inject a summary into the unified prompt. This enables the LLM to auto-suggest routes, cargo, vehicles based on historical patterns.

## Key Insights
- `build_unified_prompt()` in `unified_logistics_prompt.py` already accepts `db_context` dict -- we add profile there
- `ContextLoader._load_booking_context()` already fetches customers list -- extend to fetch profile when customer is identified
- Profile summary should be concise (~200 tokens) to avoid exceeding context budget
- The AI already matches customer names from `db_context["customers"]` list -- profile injection happens AFTER customer is identified
- **CRITICAL (P0 Timing Bug)**: Customer must be pre-scanned from message BEFORE building the prompt, not after. Use `_quick_customer_scan()` regex to extract customer name/code from user message, then fetch profile BEFORE calling LLM
- **Token Budget (P1)**: Hard limit profile to 1600 chars (~400 tokens). `format_customer_profile_for_prompt()` must enforce this with truncation
<!-- Updated: Improvement Merge - Added P0 timing bug fix + P1 token budget enforcement -->

## Requirements

### Functional
- F1: When user mentions a customer name/code, fetch their profile from `customer_profiles`
- F2: Inject profile summary into prompt under a new `## HO SO KHACH HANG` section
- F3: AI uses profile to suggest defaults (e.g., "MEIKO thuong gui PCB tu Quang Minh, toi goi y...")
- F4: If no profile exists, skip injection (no error, graceful degradation)

### Non-Functional
- NF1: Profile fetch adds <100ms to AI call latency
- NF2: Profile summary stays under 400 tokens
- NF3: No change to AI output format (same JSON structure)

## Architecture

### Modified Prompt Structure
```
UNIFIED_SYSTEM_PROMPT (existing)
  |
  v
## DU LIEU HE THONG (existing - customers, vendors, jobs)
  |
  v
## HO SO KHACH HANG (NEW - injected when customer identified)
  **Khach hang:** MEIKO (MK001)
  **Tuyen thuong dung:** Quang Minh -> Hai Phong (15 lan), Quang Minh -> Noi Bai (8 lan)
  **Hang hoa thuong gap:** PCB (avg 500kg), Linh kien dien tu (avg 200kg)
  **Loai xe uu tien:** 5T (8 lan), 2.5T (5 lan)
  **Ghi chu dac biet:** Luon can POD, giao truoc 8h sang
  |
  v
## LICH SU HOI THOAI (existing)
  |
  v
## TIN NHAN MOI TU USER (existing)
```

### Data Flow
```
User message mentions "MEIKO"
        |
        v
  ConversationManager.process() calls AI
        |
        v
  _build_db_context() fetches customers, vendors, jobs (existing)
        |
        v
  NEW: If customer_code found in entities/message -> fetch profile
        |
        v
  build_unified_prompt() includes profile in db_context
        |
        v
  AI generates response with customer-aware suggestions
```

## Related Code Files

### Files to Modify
- `backend/app/ai/prompts/unified_logistics_prompt.py` - Add profile section to `build_unified_prompt()`
- `backend/app/ai/context_loader.py` - Add `_load_customer_profile()` method
- `backend/app/ai/memory/conversation_manager.py` - Pass profile to prompt builder

### Files to Read (Reference)
- `backend/app/services/customer-profile-service.py` (from Phase 1)

## Implementation Steps

1. **Add `_quick_customer_scan()` pre-scan** (`unified_processor.py` or `conversation_manager.py`)
   - **P0 FIX**: Before building AI prompt, scan user message with regex to find customer name/code
   - Pattern: match against known customer codes (MK001, etc.) and customer names from db_context
   - If matched, fetch customer_id BEFORE building prompt
   - This ensures profile is available when `build_unified_prompt()` runs
   - Fallback: if no match, proceed without profile (same as current behavior)
   ```python
   async def _quick_customer_scan(self, message: str, customers: list) -> Optional[int]:
       """Pre-scan message for customer name/code before building AI prompt"""
       message_upper = message.upper()
       for c in customers:
           if c["customer_code"].upper() in message_upper or c["customer_name"].upper() in message_upper:
               return c["customer_id"]
       return None
   ```
<!-- Updated: Improvement Merge - P0 timing bug fix: pre-scan customer before prompt build -->

2. **Add profile fetch to ContextLoader** (`context_loader.py`)
   - New method: `async def _load_customer_profile(self, customer_id: int) -> dict`
   - Query `customer_profiles` table via Supabase client
   - Return profile dict or empty dict if not found
   - Add to `_load_booking_context()`: when customer context available, also load profile

3. **Add profile formatter** (`context_loader.py`)
   - New function: `format_customer_profile_for_prompt(profile: dict) -> str`
   - Format top 3 routes with frequency counts
   - Format top 3 cargo types with avg weight
   - Format top 3 vehicle types with counts
   - Include special_requirements if present
   - Include booking patterns (avg per month, peak days)
   - **Hard limit: 1600 characters max** (~400 tokens). Truncate least-important sections if over
   - Include `pickup_time` and `preferred_days` from booking_patterns if available
   ```python
   def format_customer_profile_for_prompt(profile: dict) -> str:
       MAX_CHARS = 1600
       parts = []
       # ... format sections ...
       result = "\n".join(parts)
       if len(result) > MAX_CHARS:
           result = result[:MAX_CHARS] + "\n... (da cat bot)"
       return result
   ```
<!-- Updated: Improvement Merge - P1 token budget 1600 chars hard limit + pickup_time/preferred_days -->

3. **Modify `build_unified_prompt()`** (`unified_logistics_prompt.py`)
   - Add new optional param: `customer_profile: dict = None`
   - If profile provided, insert `## HO SO KHACH HANG` section after `## DU LIEU HE THONG`
   - Use `format_customer_profile_for_prompt()` to format

4. **Wire profile into ConversationManager** (`conversation_manager.py`)
   - In the process flow, after customer is identified from entities:
     - Extract `customer_code` from accumulated entities
     - Look up `customer_id` from customers table
     - Call `context_loader._load_customer_profile(customer_id)`
     - Pass profile to `build_unified_prompt()` via `db_context["customer_profile"]`

5. **Update db_adapter.py** if needed
   - Add `_query_customer_profiles()` method for the adapter pattern
   - Or use direct Supabase client call (simpler)

## Todo List
- [ ] Add `_load_customer_profile()` to ContextLoader
- [ ] Create `format_customer_profile_for_prompt()` formatter
- [ ] Modify `build_unified_prompt()` to accept and render profile
- [ ] Wire profile fetch in ConversationManager process flow
- [ ] Test: send message mentioning known customer, verify profile in prompt
- [ ] Test: send message with unknown customer, verify graceful skip
- [ ] Test: verify AI response includes profile-based suggestions

## Success Criteria
- When user says "tao booking cho MEIKO", AI response mentions common routes/cargo
- Profile injection adds <100ms latency
- AI still returns valid JSON output format
- No errors when customer has no profile

## Risk Assessment
- **Risk**: Customer not yet identified when prompt is built -> **Mitigation**: Profile injection happens on second turn (after customer confirmed), or during re-prompt
- **Risk**: Profile data stale -> **Mitigation**: `last_aggregated_at` shown; Phase 4 handles auto-refresh
- **Risk**: Token budget exceeded -> **Mitigation**: Hard limit profile summary to 400 tokens, truncate if needed

## Security Considerations
- Profile data flows through existing authenticated chat pipeline
- No PII exposed (routes, cargo types, vehicle preferences)
- Special requirements field sanitized before injection into prompt

## Next Steps
- Phase 3 uses profile data in frontend auto-fill
