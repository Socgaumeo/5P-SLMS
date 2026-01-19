-- ============================================
-- SLMS Service-Specific Views
-- Created: 2026-01-17
-- ============================================

-- 1. TRUCKING VIEW (24 columns)
-- Shows: dates, addresses, cargo, dimensions, vehicle info
CREATE OR REPLACE VIEW v_trucking_services AS
SELECT 
    js.svc_id,
    js.job_id,
    j.job_no,
    js.service_type_code,
    mst.name_vi as service_name,
    c.short_name as customer,
    v.short_name as vendor,
    js.scheduled_date,
    js.scheduled_time,
    js.origin_address,
    js.dest_address,
    js.cargo_type,
    js.package_quantity,
    js.package_unit,
    js.weight_kg,
    js.dimension_length_cm,
    js.dimension_width_cm,
    js.dimension_height_cm,
    js.invoice_numbers,
    js.special_requirements,
    js.vendor_text_input,
    js.status_code,
    js.created_at,
    js.updated_at
FROM job_services js
JOIN jobs j ON js.job_id = j.job_id
JOIN customers c ON j.customer_id = c.customer_id
LEFT JOIN vendors v ON js.vendor_id = v.vendor_id
LEFT JOIN master_service_types mst ON js.service_type_code = mst.service_code
WHERE js.service_type_code IN ('TRUCKING_SHORT', 'TRUCKING_LONG');


-- 2. WAREHOUSE VIEW (19 columns)
-- Shows: storage dates, dimensions, special requirements
CREATE OR REPLACE VIEW v_warehouse_services AS
SELECT 
    js.svc_id,
    js.job_id,
    j.job_no,
    js.service_type_code,
    mst.name_vi as service_name,
    c.short_name as customer,
    v.short_name as vendor,
    js.scheduled_date,
    js.cargo_type,
    js.package_quantity,
    js.package_unit,
    js.weight_kg,
    js.dimension_length_cm,
    js.dimension_width_cm,
    js.dimension_height_cm,
    js.storage_start_date,
    js.storage_end_date,
    js.special_requirements,
    js.status_code,
    js.created_at
FROM job_services js
JOIN jobs j ON js.job_id = j.job_id
JOIN customers c ON j.customer_id = c.customer_id
LEFT JOIN vendors v ON js.vendor_id = v.vendor_id
LEFT JOIN master_service_types mst ON js.service_type_code = mst.service_code
WHERE js.service_type_code IN ('WHS_STORAGE', 'WHS_HANDLE');


-- 3. CUSTOMS VIEW (21 columns)
-- Shows: declaration info, parties, documents
CREATE OR REPLACE VIEW v_customs_services AS
SELECT 
    js.svc_id,
    js.job_id,
    j.job_no,
    js.service_type_code,
    mst.name_vi as service_name,
    c.short_name as customer,
    v.short_name as vendor,
    js.scheduled_date,
    js.declaration_no,
    js.declaration_datetime,
    js.loai_hinh,
    js.customs_type,
    js.customs_port,
    js.buyer_name,
    js.seller_name,
    js.hs_code,
    js.bl_awb_no,
    js.co_no,
    js.customs_status,
    js.status_code,
    js.created_at
FROM job_services js
JOIN jobs j ON js.job_id = j.job_id
JOIN customers c ON j.customer_id = c.customer_id
LEFT JOIN vendors v ON js.vendor_id = v.vendor_id
LEFT JOIN master_service_types mst ON js.service_type_code = mst.service_code
WHERE js.service_type_code IN ('CUS_IMPORT', 'CUS_EXPORT', 'CUS_TRANSIT');


-- 4. PACKING VIEW (25 columns)
-- Shows: before/after dimensions, addon services
CREATE OR REPLACE VIEW v_packing_services AS
SELECT 
    js.svc_id,
    js.job_id,
    j.job_no,
    js.service_type_code,
    mst.name_vi as service_name,
    c.short_name as customer,
    v.short_name as vendor,
    js.scheduled_date,
    js.packing_type,
    js.items_count,
    js.packages_output,
    js.before_length_cm,
    js.before_width_cm,
    js.before_height_cm,
    js.before_volume_cbm,
    js.after_length_cm,
    js.after_width_cm,
    js.after_height_cm,
    js.after_volume_cbm,
    js.shrink_wrap,
    js.vacuum_pack,
    js.lashing,
    js.fumigation,
    js.status_code,
    js.created_at
FROM job_services js
JOIN jobs j ON js.job_id = j.job_id
JOIN customers c ON j.customer_id = c.customer_id
LEFT JOIN vendors v ON js.vendor_id = v.vendor_id
LEFT JOIN master_service_types mst ON js.service_type_code = mst.service_code
WHERE js.service_type_code IN ('SVC_PACK', 'SVC_SHRINK_WRAP', 'SVC_VACUUM', 'SVC_LASHING', 'SVC_FUMIGATION');


-- 5. JOBS OVERVIEW VIEW (11 columns)
-- Summary view for all jobs with service counts
CREATE OR REPLACE VIEW v_jobs_overview AS
SELECT 
    j.job_id,
    j.job_no,
    c.short_name as customer,
    j.description,
    j.status_code,
    j.etd,
    j.total_revenue,
    j.total_cost,
    (SELECT COUNT(*) FROM job_services js WHERE js.job_id = j.job_id) as services_count,
    (SELECT array_agg(DISTINCT js.service_type_code) FROM job_services js WHERE js.job_id = j.job_id) as service_types,
    j.created_at
FROM jobs j
JOIN customers c ON j.customer_id = c.customer_id
ORDER BY j.created_at DESC;


-- ============================================
-- USAGE EXAMPLES
-- ============================================

-- View trucking jobs
-- SELECT * FROM v_trucking_services WHERE scheduled_date = CURRENT_DATE;

-- View warehouse jobs with storage dates
-- SELECT * FROM v_warehouse_services WHERE storage_end_date IS NULL;

-- View customs jobs pending
-- SELECT * FROM v_customs_services WHERE customs_status = 'PENDING';

-- View packing jobs with shrink wrap
-- SELECT * FROM v_packing_services WHERE shrink_wrap = true;

-- View all jobs summary
-- SELECT * FROM v_jobs_overview WHERE status_code = 'PENDING';
