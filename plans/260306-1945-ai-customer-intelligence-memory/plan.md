---
title: "AI Customer Intelligence & Memory"
description: "AI learns customer habits to auto-suggest bookings, routes, and flag anomalies"
status: pending
priority: P2
effort: 12h
branch: main
tags: [ai, customer-intelligence, memory, suggestions]
created: 2026-03-06
---

# AI Customer Intelligence & Memory

## Goal
Enable AI chatbot to remember customer preferences and patterns, auto-suggest common fields when creating bookings, and flag anomalies vs historical behavior.

## Approach
- PostgreSQL JSONB profiles on existing Supabase (no new infra)
- Mine existing `jobs`, `job_services`, `customer_rates` tables
- Inject profile into AI prompt so LLM contextually suggests
- Incremental rollout: foundation -> AI context -> UI suggestions -> auto-learning

## Phases

| # | Phase | Priority | Effort | Status |
|---|-------|----------|--------|--------|
| 1 | [Customer Profile Table + Data Mining](phase-01-customer-profile-table-data-mining.md) | HIGH | 3-4h | pending |
| 2 | [AI Prompt Context Injection](phase-02-ai-prompt-context-injection.md) | HIGH | 2-3h | pending |
| 3 | [Smart Suggestion API + Frontend](phase-03-smart-suggestion-api-frontend.md) | MEDIUM | 3-4h | pending |
| 4 | [Learning & Profile Auto-Update](phase-04-learning-profile-auto-update.md) | MEDIUM | 2-3h | pending |

## Key Files (Existing)
- `backend/app/ai/prompts/unified_logistics_prompt.py` - System prompt builder
- `backend/app/ai/unified_processor.py` - Conversation processor
- `backend/app/ai/context_loader.py` - DB context loader for AI
- `backend/app/ai/memory/conversation_manager.py` - Chat memory + action execution
- `backend/app/api/chat.py` - Chat API endpoints
- `backend/app/api/jobs.py` - Job CRUD + booking creation
- `backend/app/db/supabase_client.py` - Supabase client singleton

## Key Files (New)
- `backend/app/services/customer_profile_service.py` - Profile CRUD + aggregation
- `backend/app/api/customer_profiles.py` - Profile API endpoints
- `backend/scripts/aggregate-customer-profiles.py` - One-time migration script

## Dependencies
- Supabase PostgreSQL (existing)
- Existing `jobs`, `job_services`, `customers`, `customer_rates`, `vendor_rates` tables
- AI client (Anthropic/Gemini/DeepSeek) - already integrated

## Risks
- JSONB queries may be slow if profiles grow large -> mitigate with indexed top-level keys
- AI prompt token budget: profile injection adds ~200-400 tokens -> acceptable
- Cold start: new customers have empty profiles until enough jobs accumulate

## Success Criteria
- AI auto-suggests route/cargo/vehicle when user mentions known customer
- Booking creation pre-fills 3+ fields from profile
- Profile updates automatically after each completed job
- No regression in existing chat/booking flows

## Validation Log

### Session 1 — 2026-03-06
**Trigger:** Initial plan creation validation
**Questions asked:** 6

#### Questions & Answers

1. **[Data Source]** Profile data nên được aggregate từ nguồn nào? Plan hiện tại dùng jobs + job_services + customer_rates, nhưng hiện tại có bao nhiêu dữ liệu jobs trong hệ thống?
   - Options: Dùng data hiện có | Bắt đầu từ scratch | Import từ Excel/file ngoài
   - **Answer:** Dùng data hiện có + import thêm từ bên ngoài
   - **Custom input:** "dùng data hiện tại và import thêm từ bên ngoài"
   - **Rationale:** Cần cả hai: mine existing data AND import historical Excel. Requires Excel import script in Phase 1.

2. **[UX Override]** Khi AI gợi ý sai, operator nên xử lý thế nào?
   - Options: Chỉ hiển thị gợi ý, user tự chọn | Auto-fill nhưng dễ override | Auto-fill + confirm dialog
   - **Answer:** Chỉ hiển thị gợi ý, user tự chọn (Recommended)
   - **Rationale:** Non-intrusive suggestions. AI shows options but never auto-fills — operator stays in control.

3. **[Scope]** Anomaly detection có cần thiết ngay từ đầu không?
   - Options: Có, implement Phase 4 đầy đủ | Chỉ auto-update, bỏ anomaly | Defer Phase 4
   - **Answer:** Có, implement Phase 4 đầy đủ (Recommended)
   - **Rationale:** Anomaly flags help catch input errors early. Full Phase 4 confirmed.

4. **[Admin UI]** Có muốn operator (MANAGER) chỉnh sửa profile trên giao diện Admin?
   - Options: Có, thêm tab Customer Profiles | Không cần UI | Chỉ xem, không sửa
   - **Answer:** Có, thêm tab Customer Profiles trong Admin (Recommended)
   - **Rationale:** Operators need to view profiles + edit special requirements + trigger refresh. Adds frontend work to Phase 3.

5. **[Data Import]** Bạn muốn import dữ liệu khách hàng từ đâu?
   - Options: File Excel từ hệ thống cũ | Nhập tay qua Admin UI | Cả hai
   - **Answer:** File Excel từ hệ thống cũ (Recommended)
   - **Rationale:** Excel import script needed in Phase 1 to bootstrap profiles from historical data.

6. **[Profile Data]** Ngoài thông tin tuyến/xe/hàng, còn thông tin gì đặc biệt cần lưu?
   - Options: Yêu cầu giao hàng đặc biệt | Điều khoản thanh toán | Cả hai + khác | Chỉ tuyến/xe/hàng
   - **Answer:** Cả hai + thông tin khác
   - **Rationale:** Profile needs: delivery requirements (POD, time), payment terms, and other custom fields. Expand JSONB schema.

#### Confirmed Decisions
- **Data source**: Mine existing DB data + import from Excel files
- **Suggestion UX**: Display-only suggestions, never auto-fill — user clicks to accept
- **Phase 4 scope**: Full implementation including anomaly detection
- **Admin UI**: Add Customer Profiles tab in Admin panel (view + edit + refresh)
- **Profile schema**: Expand to include delivery_requirements, payment_terms, custom_notes JSONB fields

#### Action Items
- [ ] Phase 1: Add Excel import script for historical customer data
- [ ] Phase 1: Add `delivery_requirements`, `payment_terms`, `custom_notes` JSONB fields to schema
- [ ] Phase 3: Add Customer Profiles tab in Admin panel (view/edit/refresh)
- [ ] Phase 3: Change suggestion UX from auto-fill to display-only with click-to-accept

#### Impact on Phases
- Phase 1: Add Excel import script + expand JSONB schema with delivery_requirements, payment_terms, custom_notes
- Phase 3: Add Admin UI tab for Customer Profiles management; change suggestion from auto-fill to display-only click-to-accept

### Session 2 — 2026-03-06
**Trigger:** Merge improvements from AI_CustomerIntelligence_Improvement.docx + AI_Optimization_5P_SLMS.md
**Changes applied:** 8 improvements merged into phases

#### Merged Improvements

1. **[P0] Timing Bug Fix** → Phase 2
   - Added `_quick_customer_scan()` pre-scan: regex match customer name/code BEFORE building AI prompt
   - Ensures profile is available when `build_unified_prompt()` runs

2. **[P1] Token Budget Enforcement** → Phase 2
   - `format_customer_profile_for_prompt()` hard limit: 1600 chars (~400 tokens)
   - Truncation with "... (da cat bot)" suffix if over limit

3. **[P1] GIN Indexes** → Phase 1
   - Added 4 GIN indexes on JSONB columns (frequent_routes, common_cargo_types, preferred_vehicles, preferred_vendors)
   - Added 1 timestamp index on last_aggregated_at

4. **[P1] Excel Import Spec** → Phase 1
   - 8-column mapping spec: customer_code, cargo_types, frequent_routes, preferred_vehicles, delivery_requirements, payment_terms, special_requirements, custom_notes
   - Idempotent UPSERT, skip unmatched customer_code with warnings

5. **[P2] Anomaly Threshold Adjustment** → Phase 4
   - Changed from 2x to 3x weight threshold + minimum 10 jobs + diff > 500kg
   - Reduces false positives for small customers

6. **[P3] Race Condition RPC** → Phase 4
   - Supabase RPC function with `SELECT ... FOR UPDATE` row lock for atomic JSONB updates
   - Prevents concurrent job creation from corrupting profile JSONB

7. **[P2] Time/Day Suggestion** → Phase 3
   - Added `pickup_time` + `preferred_days` fields to suggestion API response
   - Extracted from booking_patterns in customer profile

8. **[P2] Admin UI Spec** → Phase 3
   - 4-component spec: ProfileList (table), ProfileDetail (read-only), ProfileEdit (notes/delivery/payment), ProfileRefresh (trigger re-aggregation)

#### Referenced (Not Merged)
- **AI_Optimization_5P_SLMS.md**: 5-layer AI optimization strategy (Model Routing, Prompt Caching, Structured Output, Semantic Cache, Multi-Agent). Scope is broader than Customer Intelligence — should be a separate plan.

#### Impact on Phases
- Phase 1: +GIN indexes in DDL, +Excel import spec with 8-column mapping
- Phase 2: +Pre-scan timing fix (P0), +Token budget 1600 chars hard limit
- Phase 3: +pickup_time/preferred_days in API, +4-component Admin UI spec
- Phase 4: +Adjusted anomaly thresholds (3x/10jobs/500kg), +RPC with FOR UPDATE lock
