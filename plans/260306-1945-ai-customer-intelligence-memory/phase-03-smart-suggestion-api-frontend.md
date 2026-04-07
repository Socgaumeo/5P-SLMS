# Phase 3: Smart Suggestion API + Frontend

## Context Links
- Parent: [plan.md](plan.md)
- Depends on: [Phase 1](phase-01-customer-profile-table-data-mining.md), [Phase 2](phase-02-ai-prompt-context-injection.md)

## Overview
- **Date**: 2026-03-06
- **Priority**: MEDIUM
- **Status**: pending
- **Description**: Create suggestion API that returns pre-filled booking fields when customer is selected. Integrate into frontend booking forms and chat confirmation cards.

## Key Insights
- Frontend `ChatWindow.jsx` renders `ConfirmationCard.jsx` for booking confirmation -- can pre-populate
- `EntityCard.jsx` shows accumulated entities -- can show suggested defaults with visual indicator
- Jobs API `create_from_chat` in `jobs.py` already receives enriched entities -- suggestions merge naturally
- Keep it simple: suggestion = "most frequent value" from profile, not ML prediction

## Requirements

### Functional
- F1: `GET /api/suggestions/booking?customer_id=X` returns suggested field values
- F2: Frontend displays suggestions as clickable chips — user clicks to accept (NOT auto-fill)
- F3: Suggested fields shown with "gợi ý" badge and click-to-accept interaction
- F4: User explicitly accepts or ignores each suggestion
- F5: Chat confirmation shows available suggestions with "(gợi ý)" label, not auto-filled
- F6: Customer Profiles tab in Admin: view profile, edit notes/delivery/payment, trigger refresh
<!-- Updated: Validation Session 1 - Changed to display-only click-to-accept; added Admin UI tab -->

### Non-Functional
- NF1: Suggestion API responds in <200ms
- NF2: No regression in booking creation flow
- NF3: Suggestions don't block user interaction (async loading)

## Architecture

### Suggestion API Response
```json
{
  "customer_id": 123,
  "customer_code": "MK001",
  "suggestions": {
    "pickup_address": {"value": "KCN Quang Minh, Hanoi", "confidence": 0.85, "source": "15/18 jobs"},
    "delivery_address": {"value": "Cang Hai Phong", "confidence": 0.65, "source": "12/18 jobs"},
    "vehicle_type": {"value": "5T", "confidence": 0.72, "source": "13/18 jobs"},
    "cargo_type": {"value": "PCB", "confidence": 0.80, "source": "14/18 jobs"},
    "service_type": {"value": "TRUCKING_DOM", "confidence": 0.90, "source": "16/18 jobs"},
    "pickup_time": {"value": "08:00", "confidence": 0.70, "source": "10/18 jobs"},
    "preferred_days": {"value": ["Monday", "Tuesday"], "confidence": 0.75, "source": "peak from booking_patterns"}
  },
  "profile_summary": "18 jobs tong cong, trung binh 6 jobs/thang, thuong book vao Thu 2-3"
}
```
<!-- Updated: Improvement Merge - Added pickup_time + preferred_days suggestions -->
```

### Data Flow
```
Frontend: User selects customer in chat/form
        |
        v
  GET /api/suggestions/booking?customer_id=X
        |
        v
  Backend: Read customer_profiles JSONB
        |
        v
  Transform top-1 values into suggestion format
        |
        v
  Frontend: Auto-fill form fields with suggestions
        |
        v
  User confirms or overrides -> normal booking flow
```

## Related Code Files

### Files to Create
- `backend/app/api/customer-suggestions.py` - Suggestion API endpoint

### Files to Modify
- `backend/main.py` - Register suggestions router
- `frontend/src/components/chat/ConfirmationCard.jsx` - Show clickable suggestion chips
- `frontend/src/components/chat/EntityCard.jsx` - Visual indicator for suggested fields
- `frontend/src/components/chat/ChatWindow.jsx` - Fetch suggestions when customer identified
- `frontend/src/components/admin/AdminPanel.jsx` - Add Customer Profiles tab
<!-- Updated: Validation Session 1 - Added AdminPanel.jsx for profiles tab -->

## Implementation Steps

1. **Create suggestion endpoint** (`customer-suggestions.py`)
   - `GET /api/suggestions/booking` with query param `customer_id`
   - Fetch profile from `customer_profiles` table
   - Transform JSONB data into suggestion format:
     - `frequent_routes[0]` -> pickup_address, delivery_address suggestions
     - `preferred_vehicles[0]` -> vehicle_type suggestion
     - `common_cargo_types[0]` -> cargo_type suggestion
   - Calculate confidence as `count / total_jobs`
   - Return structured response

2. **Register router** in `main.py`
   - `app.include_router(suggestions_router, prefix="/api/suggestions")`

3. **Modify ConfirmationCard.jsx**
   - Accept `suggestions` prop
   - When rendering booking confirmation, show suggested values with "(goi y)" label
   - Use lighter/italic styling for suggested vs user-provided values
   - Example: `Tuyen: Quang Minh -> Hai Phong (goi y tu lich su)`

4. **Modify ChatWindow.jsx**
   - After AI identifies customer (from `accumulated_entities.customer_code`):
     - Call `GET /api/suggestions/booking?customer_id=X`
     - Store suggestions in component state
     - Pass to ConfirmationCard when rendering

5. **Modify EntityCard.jsx**
   - Show suggestion badges next to auto-filled fields
   - Small info icon: "Goi y dua tren 15 chuyen truoc"

6. **Admin Customer Profiles Tab** (`AdminPanel.jsx`)
   - **4 components**: ProfileList, ProfileDetail, ProfileEdit, ProfileRefresh
   - **ProfileList**: Table with columns: Customer Code, Name, Total Jobs, Last Job, Last Aggregated. Search/filter. Click to open detail.
   - **ProfileDetail**: Read-only view of full profile JSONB (routes, cargo, vehicles, stats, delivery_requirements, payment_terms). Visual summary cards.
   - **ProfileEdit**: Edit `special_requirements`, `delivery_requirements`, `payment_terms`, `custom_notes`. Save via `PUT /api/customer-profiles/{id}/notes`
   - **ProfileRefresh**: Button to trigger `POST /api/customer-profiles/{id}/refresh`. Show last_aggregated_at timestamp. "Refresh All" button for admin.
<!-- Updated: Improvement Merge - Added 4-component Admin UI spec (List/Detail/Edit/Refresh) -->

## Todo List
- [ ] Create `customer-suggestions.py` with booking suggestion endpoint
- [ ] Register suggestions router in `main.py`
- [ ] Modify `ConfirmationCard.jsx` to render clickable suggestion chips
- [ ] Modify `ChatWindow.jsx` to fetch suggestions on customer identification
- [ ] Modify `EntityCard.jsx` for suggestion badges
- [ ] Add Customer Profiles tab in `AdminPanel.jsx` (view/edit/refresh)
- [ ] Test: select known customer, verify suggestion chips appear
- [ ] Test: click suggestion chip, verify it populates the field
- [ ] Test: ignore suggestions, verify booking works without them
- [ ] Test: Admin profiles tab shows/edits profiles correctly
<!-- Updated: Validation Session 1 - Added Admin profiles tab + changed to click-to-accept UX -->

## Success Criteria
- Selecting a customer with history auto-fills 3+ booking fields
- Suggested fields visually distinguished from user-entered fields
- User can override any suggestion without friction
- Booking creation works identically with or without suggestions

## Risk Assessment
- **Risk**: Suggestions wrong for one-off bookings -> **Mitigation**: Show confidence + source, user always overrides
- **Risk**: Frontend fetch adds delay -> **Mitigation**: Async fetch, don't block UI, show skeleton/spinner
- **Risk**: Profile empty for new customers -> **Mitigation**: Return empty suggestions, no auto-fill

## Security Considerations
- Suggestion endpoint requires JWT auth
- Customer profile data scoped to authenticated user's organization
- No sensitive data in suggestions (routes, vehicle types only)

## Next Steps
- Phase 4 keeps profiles fresh via auto-updates
