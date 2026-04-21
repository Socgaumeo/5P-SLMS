# Phase 4 — Family D: International Logistics Renderer

## Context links
- [plan.md](plan.md)
- [scan report](../../reports/dainese-templates/scan-all-customer-bang-ke-templates-clustering-report.md) — Cluster C9
- Existing reference: `dainese_template_renderer_nhap_sea_air.py`

## Overview
- Priority: Medium
- Status: Pending
- Brief: Generic international shipping renderer (16-22 cols), covering GLOREX QUỐC TẾ, LKV BD, LKV MB + future SEA/AIR import customers.

## Key insights
- Wide layout (16-22 cols): chi tiết từng loại phí (mở TK, kiểm hóa, vận chuyển, làm hàng, phát sinh, đầu nước ngoài, cước QT, THC, CFS, DO, đại lý) + cột "Phí trả hộ" (local/CSHT/lưu kho).
- Foreign-party detection: `note` chứa "S.P.A", "S.R.L", "Corporation"... → Family D thay vì C.
- Title varies: "DỊCH VỤ LOGISTICS HÀNG NHẬP", "BẢNG KÊ NHẬP HÀNG QUỐC TẾ", etc.
- Reuse cost-name mapper từ DAINESE.

## Requirements

### Functional
- Pull SEA_IMP/SEA_EXP/AIR_IMP/AIR_EXP/BORDER_IMP/BORDER_EXP services.
- Aggregate job_costs into 14 fee buckets (per existing mapper).
- Group "Phí trả hộ" reim costs into 3-4 sub-cols.
- Compute V=SUM(K:U), Z=SUM(W:Y), AA=V+Z formulas.

### Non-functional
- 1 module covers 3+ customers.
- Per-customer config: title, sheet name, columns to hide.

## Architecture

```
generic_template_renderer_family_d_international.py
├── render_international_workbook(...)
├── _build_two_row_header() — group headers row N + col headers row N+1
├── _service_to_row(svc, costs)  — heavy fee-bucket aggregation
├── _build_totals_row()
└── reuse aggregate_costs_into_columns from dainese_cost_name_to_column_mapper
```

## Files to create / modify

**Create**:
- `backend/app/api/exports/generic_template_renderer_family_d_international.py`

**Modify**:
- `dispatcher.py` — add 'international' family
- `registry.py` — add `_international_template()` + GLOREX-QT, LKVIET, LKVMB entries

## Implementation steps

1. Generalize DAINESE nhap_sea_air renderer → accept config dict.
2. Move 5P-specific 5P logo / company info to common helpers (already done in Phase 1).
3. Add 'international' family to dispatcher.
4. Register 3 customers.
5. Verify against original LKV BD, LKV MB, GLOREX QUỐC TẾ files.

## Todo list

- [ ] Refactor DAINESE nhap_sea_air → extract into family D module
- [ ] Add `_international_template()` helper in registry
- [ ] Register LKVIET (LKV BD), LKVMB, GLOREX-QUOCTE
- [ ] Verify generation
- [ ] Commit + push

## Success criteria
- 3 customers exportable.
- Layout matches reference (16+ cols, group headers, totals row).
- DAINESE nhap_sea_air still works (regression-free).

## Risk assessment
- **Risk**: DAINESE nhap_sea_air refactor might break existing DAINESE export. Mitigation: keep DAINESE renderer dedicated, copy logic to family D module independently.
- **Risk**: LKV BD/MB might have different column layouts. Mitigation: per-customer config field for column overrides.

## Next steps
After Phase 4 → Phase 5 (special-case customers).
