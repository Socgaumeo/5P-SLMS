# Phase 4: Cross-check Validation

## Overview
- **Priority**: HIGH (final verification before sign-off)
- **Status**: Pending
- **Depends on**: Phase 3 complete (all jobs imported)

## Validation Strategy

### Step 1: Count Validation
For each customer, compare:
- Number of jobs imported vs expected from Excel
- Number of job_costs rows vs expected cost line items
- Number of job_services rows

```sql
SELECT c.short_name, COUNT(DISTINCT j.job_id) as jobs,
       COUNT(DISTINCT js.svc_id) as services,
       COUNT(jc.cost_id) as costs
FROM jobs j
JOIN customers c ON j.customer_id = c.customer_id
LEFT JOIN job_services js ON j.job_id = js.job_id
LEFT JOIN job_costs jc ON j.job_id = jc.job_id
WHERE j.job_no LIKE '%-2503-%'
GROUP BY c.short_name
ORDER BY c.short_name;
```

### Step 2: Revenue Validation
For each customer, compare total_revenue in DB vs grand total in Excel debit notes:
- Sum of all job_costs.selling_amount per customer
- Compare against Excel bottom-line totals
- Flag any discrepancy > 1,000 VND (rounding tolerance)

```sql
SELECT c.short_name, j.job_no, j.total_revenue,
       js.service_details->>'grand_total' as excel_grand_total,
       js.service_details->>'selling_price' as service_fees,
       js.service_details->>'reimbursement_total' as thu_chi_ho
FROM jobs j
JOIN customers c ON j.customer_id = c.customer_id
JOIN job_services js ON j.job_id = js.job_id
WHERE j.job_no LIKE '%-2503-%'
ORDER BY c.short_name, j.job_no;
```

### Step 3: Document Number Validation
Verify all jobs have at least one document number:
```sql
SELECT j.job_no, js.cd_no, js.bl_awb_no, js.invoice_numbers,
       js.service_details->>'co_number' as co
FROM jobs j
JOIN job_services js ON j.job_id = js.job_id
WHERE j.job_no LIKE '%-2503-%'
  AND (js.cd_no IS NULL OR js.cd_no = '')
  AND (js.bl_awb_no IS NULL OR js.bl_awb_no = '')
  AND (js.invoice_numbers IS NULL OR js.invoice_numbers = '{}')
ORDER BY j.job_no;
```

### Step 4: Cost Line Items Validation
Verify thu/chi hộ items are separate from service fees:
```sql
SELECT j.job_no, jc.cost_name, jc.selling_rate, jc.selling_amount,
       CASE WHEN jc.cost_name LIKE 'Thu hộ:%' OR jc.cost_name LIKE 'Chi hộ:%'
            THEN 'REIMBURSEMENT' ELSE 'SERVICE_FEE' END as cost_type
FROM jobs j
JOIN job_costs jc ON j.job_id = jc.job_id
WHERE j.job_no LIKE '%-2503-%'
ORDER BY j.job_no, cost_type, jc.cost_name;
```

### Step 5: VAT Info Validation
Verify service_details JSONB has VAT fields where applicable:
```sql
SELECT j.job_no,
       js.service_details->>'vat_rate' as vat_rate,
       js.service_details->>'vat_amount' as vat_amount,
       js.service_details->>'selling_price' as pre_vat,
       js.service_details->>'total_revenue' as post_vat
FROM jobs j
JOIN job_services js ON j.job_id = js.job_id
WHERE j.job_no LIKE '%-2503-%'
  AND js.service_details->>'vat_rate' IS NOT NULL
ORDER BY j.job_no;
```

## Spot-Check List (Known Problem Cases from v1)
These specific values MUST match exactly:

| Customer | Check | Expected Value |
|----------|-------|---------------|
| TDI | Air service revenue per job | Match Excel exactly |
| DAINESE | 5 files → multiple jobs | All 5 files parsed |
| MESSER | Service fee vs chi hộ split | Separate cost rows |
| GLOREX | Thu hộ 200,000 + 40,000 | Present as cost rows |
| GANG THÉP | CPN file 6,480,000 total | Included |
| UTRACORN | Total = 2,602,800 (2,410,000 + 8% VAT) | Exact match |
| NIPPON | rv file (105 rows) | All rows imported |
| VINTECH | 2 files (trucking + air) | Both imported |
| HƯNG PHÁT | 2 files (L1 + L2) | Both imported |
| THÁI HOÀ | TCH thu chi hộ file | Included |
| LOGIMARK | 2 files with CD numbers | Both imported |

## Implementation
Run all queries via psql, output to a validation report file.
Compare totals against Excel manually for top 5 highest-revenue customers.

## Success Criteria
- [ ] Job count per customer matches expected
- [ ] Total revenue per customer within 1,000 VND of Excel totals
- [ ] All jobs have at least one document number
- [ ] Thu/chi hộ items are separate cost rows (not merged)
- [ ] VAT info present in service_details JSONB
- [ ] All 11 spot-check cases pass
