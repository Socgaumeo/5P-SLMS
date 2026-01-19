-- =============================================================================
-- FIX: Normalize surcharges for easier AI/n8n access
-- Also add vendor_code to the view for clarity
-- =============================================================================

-- 1. Create normalized surcharge prices table (easier for AI)
CREATE TABLE IF NOT EXISTS vendor_surcharge_prices (
    id              SERIAL PRIMARY KEY,
    surcharge_id    INTEGER REFERENCES vendor_surcharges(id) ON DELETE CASCADE,
    vehicle_type    VARCHAR(20) NOT NULL,
    price           DECIMAL(12,2) NOT NULL,
    
    UNIQUE(surcharge_id, vehicle_type)
);

-- 2. Migrate JSONB pricing to normalized table
INSERT INTO vendor_surcharge_prices (surcharge_id, vehicle_type, price)
SELECT 
    s.id,
    (p.kv).key AS vehicle_type,
    ((p.kv).value)::numeric AS price
FROM vendor_surcharges s
CROSS JOIN LATERAL jsonb_each(s.pricing) AS p(kv)
WHERE jsonb_typeof(s.pricing) = 'object'
ON CONFLICT (surcharge_id, vehicle_type) DO NOTHING;

-- 3. Update view to include vendor_code
DROP VIEW IF EXISTS view_vendor_rates_full;
CREATE VIEW view_vendor_rates_full AS
SELECT 
    vr.id,
    v.vendor_code,        -- Added vendor_code for clarity
    v.company_name AS vendor_name,
    v.short_name AS vendor_short_name,
    mr.origin,
    vr.origin_province,
    mr.destination,
    vr.destination_province,
    vr.rate_code,
    vr.rate_type,
    vr.vehicle_type,
    vr.temperature_range,
    vr.price,
    vr.notes,
    vr.effective_date,
    vr.is_active
FROM vendor_rates vr
JOIN vendors v ON vr.vendor_id = v.vendor_id
LEFT JOIN master_routes mr ON vr.route_id = mr.route_id
WHERE vr.is_active = TRUE
ORDER BY v.vendor_code, mr.origin, mr.destination, vr.vehicle_type;

-- 4. Create easy surcharge lookup view
CREATE OR REPLACE VIEW view_vendor_surcharges AS
SELECT 
    vs.id,
    v.vendor_code,
    v.short_name AS vendor_name,
    vs.surcharge_code,
    vs.surcharge_name,
    vs.rate_type,
    vsp.vehicle_type,
    vsp.price,
    vs.free_allowance,
    vs.unit,
    vs.effective_date,
    vs.notes
FROM vendor_surcharges vs
JOIN vendors v ON vs.vendor_id = v.vendor_id
LEFT JOIN vendor_surcharge_prices vsp ON vs.id = vsp.surcharge_id
WHERE vs.is_active = TRUE
ORDER BY v.vendor_code, vs.surcharge_code, vsp.vehicle_type;

-- 5. Summary
SELECT 'Schema normalized for AI access' AS result;
SELECT COUNT(*) AS surcharge_price_records FROM vendor_surcharge_prices;
