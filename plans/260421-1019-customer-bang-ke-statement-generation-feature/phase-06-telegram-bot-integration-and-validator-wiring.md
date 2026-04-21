# Phase 6 — Telegram Bot Integration + loai_hinh Validator Wiring

## Context links
- [plan.md](plan.md)
- Existing: `backend/app/api/telegram-webhook-handler.py`
- Existing validator: `backend/app/services/data_service.py` (loai_hinh check at service-layer)

## Overview
- Priority: High (data quality)
- Status: Pending
- Brief: Verify Telegram bot path uses `data_service.create_job` chokepoint validator + add reject UX in chat flow when loai_hinh missing.

## Key insights
- Validator at service-layer covers REST + Telegram + import scripts (verified in commit 863ec14).
- BUT Telegram chat flow may NOT call `data_service.create_job` directly — might call AI-extract → POST `/api/jobs/create`.
- Need to confirm flow + ensure validator error returns cleanly to Telegram user.

## Requirements

### Functional
- When user sends customs job creation message via Telegram missing loai_hinh:
  - Backend rejects with 400/success=false
  - Telegram bot shows clear Vietnamese error message
  - User prompted to provide loai_hinh
- AI extract should ATTEMPT to extract loai_hinh from message (e.g. "tờ khai loại hình A41")
- Suggest VN customs codes in error message

### Non-functional
- Single validation source (don't duplicate in Telegram handler)
- Error message clear + actionable

## Architecture

```
User Telegram message
  → telegram-webhook-handler.py
  → AI agent extracts entities (incl loai_hinh)
  → POST /api/jobs/create
  → endpoint validator (defense-in-depth)
  → data_service.create_job
  → service-layer validator (chokepoint)  ← single source of truth
  → Returns success=false if loai_hinh missing
  → Telegram handler sees response → sends error to user
```

## Files to inspect / modify

**Inspect**:
- `backend/app/api/telegram-webhook-handler.py` — find job creation flow
- `backend/app/ai/prompts/*.py` — find AI extraction prompts; ensure loai_hinh is requested

**Modify** (if needed):
- AI prompt: add "extract loai_hinh field if mentioned"
- Telegram handler: format validation error nicely with code suggestions

## Implementation steps

1. Trace Telegram → API → service path. Confirm validator hits.
2. Test: send Telegram message creating customs job WITHOUT loai_hinh → verify rejection.
3. Update AI prompt to request loai_hinh field.
4. Improve error message UX (codes, examples).
5. Add unit test for validator chokepoint.

## Todo list

- [ ] Trace Telegram → /api/jobs/create flow
- [ ] Verify validator triggers from Telegram path
- [ ] Update AI extraction prompt to include loai_hinh
- [ ] Polish error message returned to Telegram user
- [ ] Test E2E: Telegram message → reject → user re-submits with loai_hinh → success
- [ ] Commit + push

## Success criteria
- 100% of customs jobs created via Telegram have loai_hinh.
- Error UX is clear (Vietnamese, code suggestions).
- No duplicate validation logic.

## Risk assessment
- **Risk**: AI may hallucinate loai_hinh code. Mitigation: validate against known VN codes whitelist after AI extract.
- **Risk**: User confusion about which code to use. Mitigation: error message lists 10 most-common codes with VN labels.

## Next steps
After Phase 6 → Phase 7 (vendor cost import).
