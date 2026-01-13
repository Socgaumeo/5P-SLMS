
-- =============================================================================
-- MASTER TABLES FOR ROUTES AND PRICING (EBOOK DATA)
-- =============================================================================

-- 1. MASTER ROUTES
CREATE TABLE IF NOT EXISTS master_routes (
    route_id SERIAL PRIMARY KEY,
    route_code VARCHAR(50) UNIQUE, -- Auto-generate or Manual e.g. HN-HP
    origin VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    distance_km DECIMAL(10,2),
    travel_time_hours DECIMAL(5,2),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_routes_origin_dest ON master_routes(origin, destination);

-- 2. MASTER PRICES (BUYING & SELLING)
-- Handles both Standard Rates (Ebook) and specific Customer/Vendor agreements
CREATE TABLE IF NOT EXISTS master_prices (
    price_id SERIAL PRIMARY KEY,
    
    -- Scope
    price_type VARCHAR(20) NOT NULL CHECK (price_type IN ('STANDARD_SELLING', 'STANDARD_BUYING', 'CONTRACT_SELLING', 'CONTRACT_BUYING')),
    
    -- Relation
    route_id INTEGER REFERENCES master_routes(route_id),
    service_type_code VARCHAR(50) REFERENCES master_service_types(service_code), -- TRUCKING_SHORT, TRUCKING_LONG
    vehicle_type_code VARCHAR(50) REFERENCES master_vehicle_types(type_code),    -- 1.25T, 5T...
    
    -- Specific Contracts (Nullable)
    customer_id INTEGER REFERENCES customers(customer_id), -- Only for SELLING
    vendor_id INTEGER REFERENCES vendors(vendor_id),       -- Only for BUYING
    
    -- Value
    unit_price DECIMAL(18,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'VND',
    
    -- Validity
    valid_from DATE DEFAULT CURRENT_DATE,
    valid_to DATE,
    
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prices_lookup ON master_prices(route_id, service_type_code, vehicle_type_code, price_type);

-- 3. HELPER VIEWS (Optional)
-- View for easy Ebook lookup (Standard Selling)
CREATE OR REPLACE VIEW view_ebook_selling_prices AS
SELECT 
    r.origin, r.destination, r.distance_km,
    p.vehicle_type_code, p.unit_price, p.notes
FROM master_prices p
JOIN master_routes r ON p.route_id = r.route_id
WHERE p.price_type = 'STANDARD_SELLING' AND p.is_active = TRUE;
