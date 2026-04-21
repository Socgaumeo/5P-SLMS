# Phase 3 — Family C: Customs Declaration Multi-Sheet Renderer

## Context links
- [plan.md](plan.md) — overview
- [scan report](../../reports/dainese-templates/scan-all-customer-bang-ke-templates-clustering-report.md) — Cluster C4
- Existing reference: `dainese_template_renderer_tc_cpn.py`

## Overview
- Priority: Medium
- Status: Pending
- Brief: Build generic customs-declaration renderer with **multi-sheet output** (NHAP KHAU + XNK TAI CHO), covering 3 customers (GLOREX, THÁI HOÀ, GANG THÉP TN extended) + future similar.

## Key insights
- All 3 customers use 16-col layout: STT/Ngày/Loại xe/Booking-Bill-BKS/Vận chuyển/Tờ khai/Nội dung/ĐVT/SL/Đơn giá/Số tiền/VAT/Tổng tiền/Số GNT/Note.
- Multi-sheet split: services with cd_no prefix `108xxx` → sheet "NHAP KHAU"; `308xxx` → sheet "XNK TAI CHO".
- Title: `BẢNG KÊ THU CHI HỘ LỆ PHÍ HẢI QUAN THÁNG M/YYYY`.
- Reuse most logic from existing `dainese_template_renderer_tc_cpn.py` — extract into generic.

## Requirements

### Functional
- Pull all customs services for customer in date range.
- Split into 2 sheets by cd_no prefix.
- Each row = 1 cost line (itemized).
- Reim costs go to "Số GNT" column with biên lai number extracted from cost_name.
- Per-sheet totals: Tổng + VAT + Tổng cộng.

### Non-functional
- 1 module covers all 3 customers.
- Per-customer config: sheet names, title variant.
- Reuse `common_bang_ke_styling_and_formatting.py` helpers.

## Architecture

```
generic_template_renderer_family_c_customs.py
├── render_customs_workbook(customer, services, jobs_map, costs_by_svc, month, logo, config)
├── _split_services_by_prefix(services) → {nhap_khau: [...], xnk_tc: [...]}
├── _build_sheet(ws, title, services, costs)
└── _extract_bien_lai_from_cost_name() — reuse DAINESE pattern
```

## Files to create / modify

**Create**:
- `backend/app/api/exports/generic_template_renderer_family_c_customs.py`

**Modify**:
- `backend/app/api/exports/generic_customer_export_endpoint_dispatcher.py` — add 'customs' to FAMILY_RENDERERS map.
- `backend/app/api/exports/customer_export_template_registry.py` — add `_customs_template()` helper, add GLOREX/THAIHOA entries.

## Implementation steps

1. Read existing `dainese_template_renderer_tc_cpn.py` — extract reusable parts.
2. Create new module reusing `common_bang_ke_styling_and_formatting.py` helpers.
3. Implement multi-sheet builder loop (1 sheet per data subset).
4. Wire into dispatcher endpoint.
5. Register customers GLOREX, THAIHOA, extend GANGTHEPTN entry.
6. Run verification script — should add 3 more matches.
7. Compare generated vs original Excel files in OneDrive.

## Todo list

- [ ] Extract reusable customs logic from DAINESE tc_cpn renderer
- [ ] Build `render_customs_workbook` with multi-sheet support
- [ ] Add 'customs' family to dispatcher
- [ ] Register GLOREX, THAIHOA in registry
- [ ] Verify against original GLOREX_T3_2026_full.xlsx
- [ ] Verify against THAI_HOA_T3_2026.xlsx
- [ ] Commit + push

## Success criteria
- 3 customers exportable via 1 button each.
- Output Excel matches original layout (2 sheets, 16 cols, totals per sheet).
- Verification script: ≥2/3 ✅ Match status.

## Risk assessment
- **Risk**: cd_no prefix split might miss edge cases (None, non-108/308). Mitigation: default to NHAP KHAU sheet.
- **Risk**: GLOREX has BOTH international + tại chỗ in same workbook → may conflict with Family D. Mitigation: route to Family D for GLOREX QUỐC TẾ file separately.

## Next steps
After Phase 3 → Phase 4 (Family D international).
