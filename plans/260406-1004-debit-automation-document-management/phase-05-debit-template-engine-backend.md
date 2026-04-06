# Phase 5 — Debit Note Template Engine — Backend

## Context Links
- [MEIKO export template](../../backend/app/api/exports/meiko_customer_export_template.py)
- [Template registry](../../backend/app/api/exports/customer_export_template_registry.py)
- [Supabase client](../../backend/app/db/supabase_client.py)

## Overview
- **Priority:** High
- **Status:** Pending
- **Description:** Engine that loads customer Excel templates, fills data from DB, generates debit notes. Single + batch generation.

## Key Insights
- MEIKO export creates workbook from scratch → NEW approach loads existing template file
- `openpyxl.load_workbook(path)` preserves formatting, merged cells, formulas
- Templates stored via Telegram file_id (admin uploads template to bot) or server disk
- Field mapping: JSON in DB maps cell refs → data fields
- Data: jobs + job_services + customer_rates

## Architecture

### Template Storage
- Admin uploads Excel template via bot command `/template MEIKO` or web UI
- Template file stored as Telegram file_id (like documents)
- Or stored on server disk (`stored_files/templates/`) for faster access
- Field mapping JSON stored in `debit_templates` table

### Debit Templates Table
```sql
CREATE TABLE debit_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id INTEGER REFERENCES customers(customer_id),
  template_name TEXT NOT NULL,
  telegram_file_id TEXT,                -- Template file on Telegram
  local_file_path TEXT,                 -- Cached on server disk
  field_mapping JSONB NOT NULL,
  sheet_config JSONB DEFAULT '{}',
  is_active BOOLEAN DEFAULT true,
  created_by INTEGER REFERENCES users(user_id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Field Mapping
```json
{
  "B2": {"field": "customer_name", "format": "text"},
  "B3": {"field": "job_no", "format": "text"},
  "B4": {"field": "booking_date", "format": "date", "date_format": "DD/MM/YYYY"},
  "D10": {"field": "total_revenue", "format": "currency"},
  "D11": {"field": "vat_amount", "format": "currency", "formula": "total_revenue * 0.08"},
  "A8:E50": {"field": "services", "format": "table", "columns": {
    "A": "stt", "B": "service_description", "C": "quantity", "D": "unit_price", "E": "amount"
  }}
}
```

### Generation Flow
```
generate(template_id, job_ids[])
  → Download template (Telegram or disk cache)
  → load_workbook(template_bytes)
  → Query DB: jobs + job_services + customer info
  → Fill cells per field_mapping
  → Save to temp file → FileResponse
```

## Endpoints
```
GET    /api/debit/templates                    # List (filter by customer_id)
POST   /api/debit/templates                    # Create (upload Excel + mapping)
PUT    /api/debit/templates/{id}               # Update mapping or template
DELETE /api/debit/templates/{id}               # Delete
POST   /api/debit/generate                     # Single: {template_id, job_ids[]}
POST   /api/debit/batch-generate               # Batch: {template_id, customer_id, month} → ZIP
```

## Related Code Files
- **Create:** `backend/app/services/debit-note-generator-service.py` — Core engine
- **Create:** `backend/app/api/debit-template-crud-endpoints.py` — Template CRUD
- **Create:** `backend/app/api/debit-generation-endpoints.py` — Generate endpoints
- **Modify:** `backend/main.py` — Register routers

## Implementation Steps

1. Create SQL for `debit_templates` table (add to migration from Phase 1)
2. Create `debit-note-generator-service.py`:
   - `load_template(template_id)` → download + cache + load_workbook
   - `resolve_job_data(job_ids, customer_id)` → query DB
   - `fill_cells(wb, mapping, data)` → write values with format
   - `generate_single(template_id, job_ids)` → return temp file path
   - `generate_batch(template_id, customer_id, month)` → multiple files → ZIP
3. Create `debit-template-crud-endpoints.py` — CRUD for templates
4. Create `debit-generation-endpoints.py` — Generate + batch
5. Register routers in main.py

## Todo List
- [ ] Add debit_templates to SQL migration
- [ ] Create debit-note-generator-service.py
- [ ] Create debit-template-crud-endpoints.py
- [ ] Create debit-generation-endpoints.py
- [ ] Register routers
- [ ] Test single + batch generation

## Success Criteria
- Template loaded correctly with formatting preserved
- Cells filled with correct data (text, currency, date)
- Service line items fill table rows
- Batch generates ZIP with multiple Excel files
- Generated files open in MS Excel / Google Sheets
