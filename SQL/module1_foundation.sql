-- =============================================================================
-- MODULE 1 FOUNDATION: MISSING TABLES
-- Based on SLMS_MODULES/01_FOUNDATION documentation
-- =============================================================================

-- 1. ROLES TABLE (for RBAC)
CREATE TABLE IF NOT EXISTS roles (
    id              SERIAL PRIMARY KEY,
    role_code       VARCHAR(20) UNIQUE NOT NULL,    -- ADMIN, CS, OPS, FIN, DRV
    role_name       VARCHAR(50) NOT NULL,
    description     TEXT,
    permissions     JSONB NOT NULL DEFAULT '[]',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default roles
INSERT INTO roles (role_code, role_name, permissions) VALUES
('ADMIN', 'Administrator', '["*"]'),
('CS', 'Customer Service', '["customer.*", "job.create", "job.view"]'),
('OPS', 'Operations', '["job.*", "vehicle.*", "driver.*"]'),
('FIN', 'Finance', '["statement.*", "report.*", "job.view"]'),
('DRV', 'Driver', '["job.view_assigned", "job.update_status"]')
ON CONFLICT (role_code) DO NOTHING;

-- 2. SERVICES TABLE (service catalog)
CREATE TABLE IF NOT EXISTS services (
    id              SERIAL PRIMARY KEY,
    service_code    VARCHAR(20) UNIQUE NOT NULL,
    service_name    VARCHAR(100) NOT NULL,
    category        VARCHAR(20) NOT NULL,            -- TRUCKING, CUSTOMS, WAREHOUSE, OTHER
    sub_category    VARCHAR(50),
    pricing_type    VARCHAR(20) DEFAULT 'FIXED',     -- FIXED, PER_UNIT, PER_KG, PER_CBM
    default_price   DECIMAL(12,2),
    unit            VARCHAR(20),                     -- TRIP, CONT, KG, CBM, DECLARATION
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description     TEXT
);

-- Sample services
INSERT INTO services (service_code, service_name, category, pricing_type, default_price, unit) VALUES
('TRK-SHORT', 'Trucking ngắn (nội vùng)', 'TRUCKING', 'PER_TRIP', NULL, 'TRIP'),
('TRK-LONG', 'Trucking dài (liên tỉnh)', 'TRUCKING', 'PER_TRIP', NULL, 'TRIP'),
('TRK-CONT', 'Trucking container', 'TRUCKING', 'PER_CONT', NULL, 'CONT'),
('CD-IMPORT', 'Khai báo nhập khẩu', 'CUSTOMS', 'PER_DECL', 500000, 'DECLARATION'),
('CD-EXPORT', 'Khai báo xuất khẩu', 'CUSTOMS', 'PER_DECL', 400000, 'DECLARATION'),
('WH-STORAGE', 'Lưu kho', 'WAREHOUSE', 'PER_CBM_DAY', 5000, 'CBM/DAY'),
('WH-HANDLING', 'Bốc xếp', 'WAREHOUSE', 'PER_KG', 500, 'KG')
ON CONFLICT (service_code) DO NOTHING;

-- 3. VENDOR RATES (Giá mua - from vendors)
CREATE TABLE IF NOT EXISTS vendor_rates (
    id              SERIAL PRIMARY KEY,
    vendor_id       INTEGER REFERENCES vendors(vendor_id) NOT NULL,
    
    -- Rate Key
    service_id      INTEGER REFERENCES services(id),
    route_id        INTEGER REFERENCES master_routes(route_id),
    vehicle_type    VARCHAR(20),
    
    -- Pricing
    price           DECIMAL(12,2) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'VND',
    unit            VARCHAR(20) DEFAULT 'TRIP',
    
    -- Validity
    effective_date  DATE NOT NULL DEFAULT CURRENT_DATE,
    expiry_date     DATE,
    
    -- Conditions
    min_weight      DECIMAL(10,2),
    max_weight      DECIMAL(10,2),
    conditions      TEXT,
    
    -- Status
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes           TEXT,
    
    -- Unique constraint
    UNIQUE (vendor_id, service_id, route_id, vehicle_type, effective_date)
);

CREATE INDEX IF NOT EXISTS idx_vendor_rate_vendor ON vendor_rates(vendor_id);
CREATE INDEX IF NOT EXISTS idx_vendor_rate_route ON vendor_rates(route_id);

-- 4. CUSTOMER RATES (Giá bán - to customers)
CREATE TABLE IF NOT EXISTS customer_rates (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER REFERENCES customers(customer_id) NOT NULL,
    
    -- Rate Key
    service_id      INTEGER REFERENCES services(id),
    route_id        INTEGER REFERENCES master_routes(route_id),
    vehicle_type    VARCHAR(20),
    
    -- Pricing
    price           DECIMAL(12,2) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'VND',
    unit            VARCHAR(20) DEFAULT 'TRIP',
    
    -- Reference to vendor rate for margin calculation
    vendor_rate_id  INTEGER REFERENCES vendor_rates(id),
    margin_percent  DECIMAL(5,2),
    
    -- Validity
    effective_date  DATE NOT NULL DEFAULT CURRENT_DATE,
    expiry_date     DATE,
    
    -- Contract reference
    contract_number VARCHAR(50),
    
    -- Status
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes           TEXT,
    
    UNIQUE (customer_id, service_id, route_id, vehicle_type, effective_date)
);

CREATE INDEX IF NOT EXISTS idx_customer_rate_customer ON customer_rates(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_rate_route ON customer_rates(route_id);

-- 5. AUDIT LOGS (for tracking changes)
CREATE TABLE IF NOT EXISTS audit_logs (
    id              BIGSERIAL PRIMARY KEY,
    
    -- Who
    user_id         INTEGER,
    user_code       VARCHAR(20),
    ip_address      VARCHAR(45),
    
    -- What
    action          VARCHAR(50) NOT NULL,            -- CREATE, UPDATE, DELETE, VIEW, LOGIN
    entity_type     VARCHAR(50) NOT NULL,            -- job, customer, statement, etc.
    entity_id       INTEGER,
    entity_code     VARCHAR(50),
    
    -- Details
    old_values      JSONB,
    new_values      JSONB,
    changes         JSONB,
    
    -- Timestamp
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at);

-- 6. Add role_id to users table if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'role_id') THEN
        ALTER TABLE users ADD COLUMN role_id INTEGER REFERENCES roles(id);
    END IF;
END $$;

-- Summary
SELECT 'Module 1 Foundation tables created successfully' AS result;
