-- =============================================================================
-- ENHANCED VENDOR RATES SCHEMA
-- To capture: Surcharges (Phụ phí), Refrigerated rates (Xe lạnh), Rate codes
-- =============================================================================

-- 1. Add missing columns to vendor_rates
ALTER TABLE vendor_rates ADD COLUMN IF NOT EXISTS rate_code VARCHAR(20);         -- TB18, TB20, etc.
ALTER TABLE vendor_rates ADD COLUMN IF NOT EXISTS rate_type VARCHAR(30) DEFAULT 'STANDARD';  -- STANDARD, REFRIGERATED
ALTER TABLE vendor_rates ADD COLUMN IF NOT EXISTS temperature_range VARCHAR(50); -- "Từ 0 đến 10 độ", etc.
ALTER TABLE vendor_rates ADD COLUMN IF NOT EXISTS origin_province VARCHAR(50);
ALTER TABLE vendor_rates ADD COLUMN IF NOT EXISTS destination_province VARCHAR(50);

-- 2. Surcharges table (Phụ phí)
CREATE TABLE IF NOT EXISTS vendor_surcharges (
    id              SERIAL PRIMARY KEY,
    vendor_id       INTEGER REFERENCES vendors(vendor_id) NOT NULL,
    
    -- Surcharge type
    surcharge_code  VARCHAR(30) NOT NULL,
    -- WAITING_HOUR (chờ giờ), OVERNIGHT (lưu ca), EXTRA_STOP_SAME (thêm điểm cùng tuyến),
    -- EXTRA_STOP_OTHER (thêm điểm khác tuyến), HOLIDAY (ngày lễ), FAILED_PICKUP (đón trượt),
    -- BORDER_CROSSING (cửa khẩu), ENGINE_RUNNING (nổ máy), NIGHT_DELIVERY (giao đêm)
    
    surcharge_name  VARCHAR(100) NOT NULL,
    description     TEXT,
    
    -- Rate type (for refrigerated vs normal)
    rate_type       VARCHAR(30) DEFAULT 'STANDARD',  -- STANDARD, REFRIGERATED
    
    -- Pricing by vehicle type (JSONB for flexibility)
    pricing         JSONB NOT NULL,
    -- Example: {"1.25T": 50000, "1.5T": 60000, "2.5T": 80000, "3.5T": 90000}
    
    -- Free allowance (miễn phí)
    free_allowance  VARCHAR(50),  -- "1 giờ", "30 phút", etc.
    
    -- Calculation unit
    unit            VARCHAR(20),  -- PER_HOUR, PER_TRIP, PER_KM, FLAT
    
    -- Validity
    effective_date  DATE NOT NULL DEFAULT CURRENT_DATE,
    expiry_date     DATE,
    
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes           TEXT
);

-- 3. Create view for easy rate lookup
CREATE OR REPLACE VIEW view_vendor_rates_full AS
SELECT 
    vr.id,
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
ORDER BY mr.origin, mr.destination, vr.vehicle_type;

-- 4. Insert sample surcharges for Tam Bảo (vendor_id = 1)
INSERT INTO vendor_surcharges (vendor_id, surcharge_code, surcharge_name, rate_type, pricing, free_allowance, unit) VALUES
-- Xe thường
(1, 'WAITING_HOUR', 'Phí chờ giờ', 'STANDARD', 
 '{"1.25T": 50000, "1.5T": 50000, "2.5T": 50000, "3.5T": 60000, "5T": 60000, "8T": 70000}', 
 '1 giờ', 'PER_HOUR'),

(1, 'OVERNIGHT', 'Phí lưu ca (Việt Nam)', 'STANDARD', 
 '{"1.25T": 450000, "1.5T": 450000, "2.5T": 500000, "3.5T": 500000, "5T": 600000, "8T": 600000}', 
 NULL, 'PER_NIGHT'),

(1, 'EXTRA_STOP_SAME', 'Thêm điểm cùng tuyến (dưới 20km)', 'STANDARD', 
 '{"1.25T": 50000, "1.5T": 60000, "2.5T": 80000, "3.5T": 90000, "5T": 100000, "8T": 120000}', 
 NULL, 'PER_STOP'),

(1, 'EXTRA_STOP_SAME_FAR', 'Thêm điểm cùng tuyến (trên 20km)', 'STANDARD', 
 '{"1.25T": 100000, "1.5T": 120000, "2.5T": 150000, "3.5T": 150000, "5T": 200000, "8T": 250000}', 
 NULL, 'PER_STOP'),

(1, 'EXTRA_KM', 'Thêm km không cùng tuyến', 'STANDARD', 
 '{"1.25T": 11000, "1.5T": 12000, "2.5T": 14000, "3.5T": 17000, "5T": 20000, "8T": 24000}', 
 NULL, 'PER_KM'),

(1, 'BORDER_CROSSING', 'Xe xuất sang Bằng Tường TQ', 'STANDARD', 
 '{"1.25T": 500000, "1.5T": 500000, "2.5T": 500000, "3.5T": 600000, "5T": 600000, "8T": 700000}', 
 NULL, 'FLAT'),

(1, 'HOLIDAY', 'Phụ phí ngày Lễ, Tết, CN', 'STANDARD', 
 '{"1.25T": 300000, "1.5T": 300000, "2.5T": 300000, "3.5T": 300000, "5T": 300000, "8T": 300000}', 
 NULL, 'FLAT'),

(1, 'FAILED_PICKUP', 'Đón trượt (70% cước)', 'STANDARD', 
 '{}', NULL, 'PERCENT'),

-- Xe lạnh - chờ giờ
(1, 'WAITING_HOUR_ENGINE', 'Phí chờ giờ nổ máy (xe lạnh)', 'REFRIGERATED', 
 '{"1.25T": 100000, "1.5T": 100000, "2.5T": 100000, "3.5T": 120000, "5T": 120000, "7T": 150000}', 
 '30 phút', 'PER_HOUR'),

(1, 'WAITING_HOUR_NO_ENGINE', 'Phí chờ giờ không nổ máy (xe lạnh)', 'REFRIGERATED', 
 '{"1.25T": 50000, "1.5T": 50000, "2.5T": 50000, "3.5T": 60000, "5T": 60000, "7T": 70000}', 
 '1 giờ', 'PER_HOUR'),

(1, 'NIGHT_DELIVERY', 'Phụ phí giao nhận hàng đêm (xe lạnh)', 'REFRIGERATED', 
 '{"1.25T": 50000, "1.5T": 50000, "2.5T": 50000, "3.5T": 50000, "5T": 80000, "7T": 80000}', 
 NULL, 'FLAT')

ON CONFLICT DO NOTHING;

-- 5. Summary
SELECT 'Schema enhanced and surcharges added' AS result;
SELECT surcharge_code, surcharge_name, rate_type FROM vendor_surcharges WHERE vendor_id = 1;
