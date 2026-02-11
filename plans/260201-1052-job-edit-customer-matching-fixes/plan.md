---
title: "Job Edit and Customer Matching Fixes"
description: "Fix customer matching bug, add job editing via UI and chat, implement per-service vendor/quotation selection"
status: pending
priority: P1
effort: 12h
branch: main
tags: [bugfix, feature, ai, frontend, backend]
created: 2026-02-01
---

# Job Edit and Customer Matching Fixes

## Overview

This plan addresses four key issues in the SLMS system:
1. **Customer matching bug** - Wrong customer matched due to fuzzy matching without confidence scoring
2. **Job detail editing** - Allow editing customer info and adding services in JobDetailModal
3. **Chat update_job** - Implement job editing via chat commands
4. **Per-service features** - Different handlers/vendors and quotations per service

## Phases

| Phase | Description | Status | Effort |
|-------|-------------|--------|--------|
| [Phase 1](./phase-01-customer-matching-confidence-scoring-and-confirmation-flow.md) | Fix customer matching with confidence scoring | pending | 3h |
| [Phase 2](./phase-02-job-detail-modal-customer-and-service-editing.md) | Add customer/service editing to JobDetailModal | pending | 3h |
| [Phase 3](./phase-03-chat-update-job-intent-implementation.md) | Implement update_job intent in chat | pending | 3h |
| [Phase 4](./phase-04-per-service-vendor-and-quotation-selection.md) | Per-service vendor and quotation selection | pending | 3h |

## Key Dependencies

- Supabase database schema (customers, vendors, job_services, quotations)
- AI entity_extractor.py for customer matching
- Frontend App.jsx for JobDetailModal
- Backend conversation_manager.py for chat intents

## Success Criteria

- [ ] Customer matching returns confidence score and prompts confirmation when <0.85
- [ ] JobDetailModal allows editing customer and adding services
- [ ] Chat accepts "sua thong tin khach hang cua Job X" and performs update
- [ ] Each service can have different vendor and quotation

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking existing customer matching | Keep fallback to current behavior if confidence >0.85 |
| UI complexity in JobDetailModal | Incremental approach - edit mode toggle |
| Chat intent conflicts | Clear intent classification rules |
