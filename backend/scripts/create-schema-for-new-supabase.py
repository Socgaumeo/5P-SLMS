#!/usr/bin/env python3
"""
Create schema on new Supabase (Singapore) using direct SQL execution.
"""

from supabase import create_client
import os

# New Supabase (ap-southeast-1 Singapore)
NEW_URL = "https://ooixntyflwmjaryxwakx.supabase.co"
NEW_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9vaXhudHlmbHdtamFyeXh3YWt4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDgxMzYyOSwiZXhwIjoyMDg2Mzg5NjI5fQ.SOEp-m3ZFyYcVUcafUoQZU9u145G1diX8Lr8h0jsbik"

# Schema SQL - all tables needed for SLMS
SCHEMA_SQL = """
-- =============================================================================
-- SLMS Database Schema for New Supabase (Singapore)
-- =============================================================================

-- 1. MASTER TABLES
CREATE TABLE IF NOT EXISTS master_service_types (
    service_code VARCHAR(50) PRIMARY KEY,
    name_vi VARCHAR(100) NOT NULL,
    sort_order INTEGER DEFAULT 99,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS master_statuses (
    status_code VARCHAR(50) PRIMARY KEY,
    name_vi VARCHAR(100) NOT NULL,
    color_code VARCHAR(20) DEFAULT '#808080',
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS master_vehicle_types (
    type_code VARCHAR(50) PRIMARY KEY,
    name_vi VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- 2. CORE TABLES
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    user_code VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(200) UNIQUE,
    password_hash VARCHAR(255),
    role VARCHAR(50) DEFAULT 'STAFF',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    created_by INTEGER
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    customer_code VARCHAR(20) UNIQUE NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    short_name VARCHAR(50),
    tax_code VARCHAR(20),
    address TEXT,
    province VARCHAR(100),
    contact_name VARCHAR(100),
    contact_phone VARCHAR(20),
    contact_zalo VARCHAR(20),
    contact_email VARCHAR(200),
    payment_terms INTEGER DEFAULT 30,
    credit_limit DECIMAL(18,2) DEFAULT 0,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vendors (
    vendor_id SERIAL PRIMARY KEY,
    vendor_code VARCHAR(20) UNIQUE NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    short_name VARCHAR(50),
    vendor_type VARCHAR(50) DEFAULT 'TRUCKING',
    tax_code VARCHAR(20),
    address TEXT,
    province VARCHAR(100),
    contact_name VARCHAR(100),
    contact_phone VARCHAR(20),
    telegram_chat_id VARCHAR(50),
    bank_name VARCHAR(100),
    bank_account VARCHAR(50),
    payment_terms INTEGER DEFAULT 30,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS drivers (
    driver_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    id_card VARCHAR(20),
    vendor_id INTEGER REFERENCES vendors(vendor_id),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id SERIAL PRIMARY KEY,
    plate_number VARCHAR(20) UNIQUE NOT NULL,
    vehicle_type_code VARCHAR(50) REFERENCES master_vehicle_types(type_code),
    vendor_id INTEGER REFERENCES vendors(vendor_id),
    driver_id INTEGER REFERENCES drivers(driver_id),
    is_active BOOLEAN DEFAULT TRUE
);

-- 3. OPERATION TABLES
CREATE TABLE IF NOT EXISTS jobs (
    job_id SERIAL PRIMARY KEY,
    job_no VARCHAR(30) UNIQUE NOT NULL,
    customer_id INTEGER REFERENCES customers(customer_id),
    description TEXT,
    etd DATE,
    eta DATE,
    status_code VARCHAR(50) DEFAULT 'DRAFT',
    total_revenue DECIMAL(18,2) DEFAULT 0,
    total_cost DECIMAL(18,2) DEFAULT 0,
    profit DECIMAL(18,2) GENERATED ALWAYS AS (total_revenue - total_cost) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER
);

CREATE TABLE IF NOT EXISTS job_services (
    svc_id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(job_id) ON DELETE CASCADE,
    service_type_code VARCHAR(50),
    scheduled_date DATE,
    scheduled_time TIME,
    origin_address TEXT,
    dest_address TEXT,
    vendor_id INTEGER REFERENCES vendors(vendor_id),
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id),
    driver_id INTEGER REFERENCES drivers(driver_id),
    vendor_text_input TEXT,
    status_code VARCHAR(50) DEFAULT 'PENDING',
    service_details JSONB DEFAULT '{}',
    msg_vendor TEXT,
    msg_customer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job_costs (
    cost_id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(job_id) ON DELETE CASCADE,
    svc_id INTEGER REFERENCES job_services(svc_id) ON DELETE CASCADE,
    cost_name VARCHAR(200) NOT NULL,
    vendor_id INTEGER REFERENCES vendors(vendor_id),
    quantity DECIMAL(18,3) DEFAULT 1,
    unit VARCHAR(20) DEFAULT 'TRIP',
    buying_rate DECIMAL(18,2) DEFAULT 0,
    buying_amount DECIMAL(18,2) GENERATED ALWAYS AS (quantity * buying_rate) STORED,
    selling_rate DECIMAL(18,2) DEFAULT 0,
    selling_amount DECIMAL(18,2) GENERATED ALWAYS AS (quantity * selling_rate) STORED,
    profit DECIMAL(18,2) GENERATED ALWAYS AS ((quantity * selling_rate) - (quantity * buying_rate)) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. AUTOMATION TABLES
CREATE TABLE IF NOT EXISTS message_templates (
    template_code VARCHAR(50) PRIMARY KEY,
    content_template TEXT NOT NULL,
    platform VARCHAR(20) DEFAULT 'ZALO'
);

CREATE TABLE IF NOT EXISTS automation_logs (
    log_id SERIAL PRIMARY KEY,
    job_id INTEGER,
    trigger_source VARCHAR(50),
    input_content TEXT,
    ai_output JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_logs (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    old_value JSONB,
    new_value JSONB,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. RATE TABLES
CREATE TABLE IF NOT EXISTS vendor_rates (
    rate_id SERIAL PRIMARY KEY,
    vendor_id INTEGER REFERENCES vendors(vendor_id),
    origin_province VARCHAR(100),
    dest_province VARCHAR(100),
    vehicle_type VARCHAR(50),
    base_price DECIMAL(18,2),
    price_per_km DECIMAL(18,2),
    min_price DECIMAL(18,2),
    effective_date DATE DEFAULT CURRENT_DATE,
    expiry_date DATE,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vendor_surcharges (
    surcharge_id SERIAL PRIMARY KEY,
    vendor_id INTEGER REFERENCES vendors(vendor_id),
    surcharge_name VARCHAR(200) NOT NULL,
    surcharge_type VARCHAR(50),
    amount DECIMAL(18,2),
    percentage DECIMAL(5,2),
    conditions TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customer_rates (
    rate_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    origin_province VARCHAR(100),
    dest_province VARCHAR(100),
    vehicle_type VARCHAR(50),
    base_price DECIMAL(18,2),
    price_per_km DECIMAL(18,2),
    min_price DECIMAL(18,2),
    effective_date DATE DEFAULT CURRENT_DATE,
    expiry_date DATE,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customer_surcharges (
    surcharge_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    surcharge_name VARCHAR(200) NOT NULL,
    surcharge_type VARCHAR(50),
    amount DECIMAL(18,2),
    percentage DECIMAL(5,2),
    conditions TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. INDEXES
CREATE INDEX IF NOT EXISTS idx_jobs_customer ON jobs(customer_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status_code);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_services_job ON job_services(job_id);
CREATE INDEX IF NOT EXISTS idx_job_costs_job ON job_costs(job_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created ON activity_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_vendor_rates_vendor ON vendor_rates(vendor_id);
CREATE INDEX IF NOT EXISTS idx_customer_rates_customer ON customer_rates(customer_id);

-- 7. TRIGGERS
CREATE OR REPLACE FUNCTION generate_job_no() RETURNS TRIGGER AS $$
DECLARE v_prefix VARCHAR(10); v_seq INTEGER;
BEGIN
    v_prefix := 'LG' || TO_CHAR(CURRENT_DATE, 'YYMM') || '/';
    SELECT COALESCE(MAX(CAST(SUBSTRING(job_no FROM LENGTH(v_prefix)+1) AS INTEGER)), 0) + 1
    INTO v_seq FROM jobs WHERE job_no LIKE v_prefix || '%';
    NEW.job_no := v_prefix || LPAD(v_seq::TEXT, 3, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_jobs_generate_no ON jobs;
CREATE TRIGGER tr_jobs_generate_no BEFORE INSERT ON jobs
    FOR EACH ROW WHEN (NEW.job_no IS NULL OR NEW.job_no = '')
    EXECUTE FUNCTION generate_job_no();

CREATE OR REPLACE FUNCTION update_job_totals() RETURNS TRIGGER AS $$
BEGIN
    UPDATE jobs SET
        total_revenue = COALESCE((SELECT SUM(selling_amount) FROM job_costs WHERE job_id = COALESCE(NEW.job_id, OLD.job_id)), 0),
        total_cost = COALESCE((SELECT SUM(buying_amount) FROM job_costs WHERE job_id = COALESCE(NEW.job_id, OLD.job_id)), 0)
    WHERE job_id = COALESCE(NEW.job_id, OLD.job_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_job_costs_update_totals ON job_costs;
CREATE TRIGGER tr_job_costs_update_totals AFTER INSERT OR UPDATE OR DELETE ON job_costs
    FOR EACH ROW EXECUTE FUNCTION update_job_totals();
"""


def main():
    print("=" * 60)
    print("CREATE SCHEMA ON NEW SUPABASE (Singapore)")
    print("=" * 60)

    # Connect
    print("\n[1/2] Connecting to new Supabase...")
    client = create_client(NEW_URL, NEW_SERVICE_KEY)
    print("  ✓ Connected")

    # Execute SQL via RPC (Supabase doesn't allow direct SQL, need to use Supabase Dashboard)
    print("\n[2/2] Schema SQL generated.")
    print("\n⚠️  Supabase API does not support direct SQL execution.")
    print("   Please run the schema manually in Supabase SQL Editor:")
    print(f"   1. Go to: {NEW_URL.replace('.supabase.co', '')}.supabase.co/project/ooixntyflwmjaryxwakx/sql")
    print("   2. Copy and paste the SQL below")
    print("   3. Click 'Run'")

    # Save SQL to file
    sql_file = "/tmp/new_supabase_schema.sql"
    with open(sql_file, 'w') as f:
        f.write(SCHEMA_SQL)
    print(f"\n   SQL saved to: {sql_file}")

    print("\n" + "=" * 60)
    print("SQL SCHEMA (copy this to Supabase SQL Editor):")
    print("=" * 60)
    print(SCHEMA_SQL)


if __name__ == "__main__":
    main()
