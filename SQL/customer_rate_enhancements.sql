-- =============================================================================
-- CUSTOMER RATE ENHANCEMENTS
-- Add: Surcharges table, File reference tracking
-- =============================================================================

-- 1. Customer Surcharges Table (Phụ phí khách hàng)
CREATE TABLE IF NOT EXISTS customer_surcharges (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER REFERENCES customers(customer_id) NOT NULL,
    
    -- Surcharge type
    surcharge_code  VARCHAR(30) NOT NULL,
    surcharge_name  VARCHAR(100) NOT NULL,
    description     TEXT,
    
    -- Pricing by vehicle type
    pricing         JSONB NOT NULL,
    
    -- Free allowance
    free_allowance  VARCHAR(50),
    
    -- Calculation
    unit            VARCHAR(20),  -- PER_HOUR, PER_TRIP, PER_KM, FLAT, PERCENT
    
    -- Validity
    effective_date  DATE NOT NULL DEFAULT CURRENT_DATE,
    expiry_date     DATE,
    
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes           TEXT
);

-- 2. Normalized customer surcharge prices (for easier AI/n8n access)
CREATE TABLE IF NOT EXISTS customer_surcharge_prices (
    id              SERIAL PRIMARY KEY,
    surcharge_id    INTEGER REFERENCES customer_surcharges(id) ON DELETE CASCADE,
    vehicle_type    VARCHAR(20) NOT NULL,
    price           DECIMAL(12,2) NOT NULL,
    
    UNIQUE(surcharge_id, vehicle_type)
);

-- 3. Rate File References (Lưu trữ file gốc)
CREATE TABLE IF NOT EXISTS rate_file_references (
    id              SERIAL PRIMARY KEY,
    
    -- Reference type
    entity_type     VARCHAR(20) NOT NULL,  -- CUSTOMER, VENDOR
    entity_id       INTEGER NOT NULL,
    
    -- File info
    original_filename VARCHAR(255) NOT NULL,
    stored_path     TEXT,                   -- Local path or cloud URL
    file_type       VARCHAR(10),            -- PDF, XLSX, XLS
    file_size_bytes INTEGER,
    
    -- Parsing info
    parsed_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parsed_by_ai    VARCHAR(50),            -- DEEPSEEK, GEMINI
    ai_confidence   DECIMAL(3,2),
    
    -- Results
    rates_imported  INTEGER DEFAULT 0,
    surcharges_imported INTEGER DEFAULT 0,
    
    -- Validity period from document
    effective_from  DATE,
    effective_to    DATE,
    
    -- Meta
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by      INTEGER
);

CREATE INDEX IF NOT EXISTS idx_rate_file_entity ON rate_file_references(entity_type, entity_id);

-- 4. Add file_reference_id to rate tables
ALTER TABLE customer_rates ADD COLUMN IF NOT EXISTS file_reference_id INTEGER REFERENCES rate_file_references(id);
ALTER TABLE vendor_rates ADD COLUMN IF NOT EXISTS file_reference_id INTEGER REFERENCES rate_file_references(id);

-- 5. Create view for customer surcharges
CREATE OR REPLACE VIEW view_customer_surcharges AS
SELECT 
    cs.id,
    c.customer_code,
    c.short_name AS customer_name,
    cs.surcharge_code,
    cs.surcharge_name,
    csp.vehicle_type,
    csp.price,
    cs.free_allowance,
    cs.unit,
    cs.effective_date,
    cs.notes
FROM customer_surcharges cs
JOIN customers c ON cs.customer_id = c.customer_id
LEFT JOIN customer_surcharge_prices csp ON cs.id = csp.surcharge_id
WHERE cs.is_active = TRUE
ORDER BY c.customer_code, cs.surcharge_code, csp.vehicle_type;

SELECT 'Customer rate enhancements created' AS result;
