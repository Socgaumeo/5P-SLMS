# Customer Bảng Kê (Statement) Generation Feature — Master Plan

## Goal
Cho phép user xuất bảng kê Excel cho **mọi customer** với:
- Format chuẩn 5P (logo, header công ty, tên + địa chỉ + MST KH)
- Đủ data phí + ghi chú (PRIORITY > pixel-perfect layout)
- Tổng / VAT / Tổng cộng / bằng chữ
- Hỗ trợ filter theo tháng / khoảng ngày / loại dịch vụ

## Current state (đã làm — commit `728c05f` trên main)

| Phase | Status | Outcome |
|---|---|---|
| 0. Foundation (DAINESE 5 sub-templates) | ✅ Done | `dainese_*.py` — 5 dedicated renderers (nhap_sea_air, phi_co, tc_cpn, tt, xuat) |
| 0.5 MEIKO 3-sheet template | ✅ Pre-existing | `meiko_customer_export_template.py` |
| 1. Generic engine + shared helpers | ✅ Done | `common_bang_ke_styling_and_formatting.py` |
| 2. Family A trucking + Family B handling renderers | ✅ Done | 2 generic renderers cover 14 customers |
| 2.5 Generic dispatcher endpoint + registry expansion | ✅ Done | 1 entry/customer in `customer_export_template_registry.py` |
| 2.6 Cost data fixes (svc_id backfill + buy=sell bug) | ✅ Done | 207 orphaned rows + 211 buy=sell rows backfilled |
| 2.7 Frontend: per-template buttons + service-type filter on list | ✅ Done | `SearchBox.jsx` |

**16 customers** active hôm nay. Trừ MEIKO/DAINESE special, **14 customer chỉ qua 1-line registry config**.

## Remaining phases

| Phase | Description | Effort | Doc |
|---|---|---|---|
| 3 | Family C: Customs declaration BKS+TK (multi-sheet) | 2 days | [phase-03-family-c-customs-multi-sheet.md](phase-03-family-c-customs-multi-sheet.md) |
| 4 | Family D: International logistics (16+ fee cols) | 2 days | [phase-04-family-d-international-logistics.md](phase-04-family-d-international-logistics.md) |
| 5 | Special-case customers (TDI/KWE/MESSER/etc.) | 2-3 days | [phase-05-special-case-customers.md](phase-05-special-case-customers.md) |
| 6 | Telegram bot integration + loai_hinh validator wiring | 1 day | [phase-06-telegram-bot-integration.md](phase-06-telegram-bot-integration.md) |
| 7 | Vendor cost import (real margin computation) | 2 days | [phase-07-vendor-cost-import-real-margin.md](phase-07-vendor-cost-import-real-margin.md) |
| 8 | Frontend UX polish + admin config UI | 1-2 days | [phase-08-frontend-ux-and-admin-config.md](phase-08-frontend-ux-and-admin-config.md) |
| 9 | E2E testing + customer rollout playbook | 1 day | [phase-09-e2e-testing-and-rollout.md](phase-09-e2e-testing-and-rollout.md) |

**Tổng remaining**: ~11-13 ngày.

## Architecture principles

1. **DRY** — 1 module = 1 template family, không duplicate code per customer.
2. **Config over code** — thêm customer = 1 line trong registry, không tạo file Python mới.
3. **Data correctness > pixel perfection** (per user T3.2026 review).
4. **Defensive fallback** — `job_costs` → `service_details.unit_price` → `selling_price` → `grand_total`.
5. **Single chokepoint validation** — `data_service.create_job` (covers REST + Telegram + import scripts).
6. **Format chuẩn 5P bất biến** — logo, header, bank info giống nhau mọi customer; chỉ vary title/columns/customer block.

## Module map (after all phases)

```
backend/app/api/exports/
├── common_bang_ke_styling_and_formatting.py     # Shared (5P brand)
├── customer_export_template_registry.py          # Single source of truth
├── generic_customer_export_endpoint_dispatcher.py # 1 endpoint /api/jobs/exports/generic
├── generic_template_renderer_family_a_trucking.py
├── generic_template_renderer_family_b_handling.py
├── generic_template_renderer_family_c_customs.py    # Phase 3
├── generic_template_renderer_family_d_international.py # Phase 4
├── meiko_customer_export_template.py             # Special — kept
├── dainese_customer_export_template.py           # Special — kept
├── dainese_template_renderer_*.py (×5)           # Special — kept
├── tdi_special_multi_sheet_template.py           # Phase 5
├── kwe_data_dump_template.py                     # Phase 5
└── messer_special_template.py                    # Phase 5 (if needed)
```

## Verified status (T3.2026 — 18 customer/template combos tested)

| Status | Count | Notes |
|---|---|---|
| ✅ Match / partial | 12 | Working customers |
| ❌ Real DB data gap | 4 | DONGSUNG, TVC (no jobs); MESSERHP (404); BINHMINH/UPGAIN fixed |
| 🟡 False-negative | 4 | DAINESE multi-sheet — verify script can't read 2-row headers |
| ❌ DB empty | 1 | MESSERHP |

## Key technical decisions

### Filter precedence
1. Customer code (registry lookup)
2. Family/template key (registry config)
3. Date filter: `month=YYYY-MM` OR `from_date+to_date`
4. Service type narrow filter (optional)

### Cost source resolution
Per service, in order:
1. `job_costs` rows where `svc_id = service.svc_id` (itemized — best)
2. `job_costs` rows where `job_id = service.job_id` AND `svc_id IS NULL` (orphan recovery)
3. `service_details.unit_price × quantity`
4. `service_details.selling_price`
5. `service_details.total_revenue` minus VAT
6. `service_details.grand_total` minus VAT

### Cost-name → bucket mapping (fuzzy regex)
Maintained in `dainese_cost_name_to_column_mapper.py`. Works for any customer because Vietnamese cost names are standardized:
- "Phí mở tờ khai" → customs declaration bucket
- "Phí vận chuyển" / "Cước" → transport bucket
- "Phụ phí xăng dầu" → fuel surcharge bucket
- "Phí xếp dỡ (THC)" → THC
- ... (27 unit tests pass)

## Open questions

1. **Vendor cost import workflow** — chưa rõ ai/khi nào nhập vendor invoices vào DB. Cần workflow/UI riêng.
2. **Multi-sheet output preference** — KH muốn 1 file nhiều sheets hay nhiều file riêng?
3. **TDI BẢNG THEO DÕI** — internal tracking sheet hay bảng kê thật?
4. **Bank info variant** — có customer nào dùng STK khác Techcombank ĐĐ 346886?
5. **VAT rate per service** — 8% phổ biến, CO=0%, có gì khác không?
6. **Customer code disambiguation** — KK vs KKFASHION (cùng K+K Fashion), MESSERHP/HD/DQ/TN — gộp hay tách?
7. **Frontend admin UI** — cần page CRUD registry config hay chỉ edit Python file?
