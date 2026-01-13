-- =============================================================================
-- SLMS - Smart Logistics Management System
-- Database Schema: PRODUCTION VERSION 2.0 (Dynamic Masters + AI Ready)
-- =============================================================================

-- 1. DATABASE PHỤ TRỢ
CREATE DATABASE n8n;
CREATE DATABASE metabase;

-- 2. MASTER TABLES (DANH MỤC ĐỘNG)
CREATE TABLE master_service_types (
    service_code VARCHAR(50) PRIMARY KEY,
    name_vi VARCHAR(100) NOT NULL,
    sort_order INTEGER DEFAULT 99,
    is_active BOOLEAN DEFAULT TRUE
);
INSERT INTO master_service_types VALUES 
('TRUCKING_SHORT', 'Vận tải tuyến ngắn', 1, TRUE),
('TRUCKING_LONG', 'Vận tải tuyến dài', 2, TRUE),
('CD_IMPORT', 'Thông quan nhập khẩu', 3, TRUE),
('CD_EXPORT', 'Thông quan xuất khẩu', 4, TRUE),
('OTHER', 'Dịch vụ khác', 99, TRUE);

CREATE TABLE master_statuses (
    status_code VARCHAR(50) PRIMARY KEY,
    name_vi VARCHAR(100) NOT NULL,
    color_code VARCHAR(20) DEFAULT '#808080',
    is_active BOOLEAN DEFAULT TRUE
);
INSERT INTO master_statuses VALUES 
('DRAFT', 'Nháp', '#E0E0E0', TRUE),
('PENDING', 'Chờ xử lý', '#F2C94C', TRUE),
('CONFIRMED', 'Đã xác nhận', '#2F6BCE', TRUE),
('COMPLETED', 'Hoàn thành', '#27AE60', TRUE),
('CANCELLED', 'Đã hủy', '#EB5757', TRUE);

CREATE TABLE master_vehicle_types (
    type_code VARCHAR(50) PRIMARY KEY,
    name_vi VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);
INSERT INTO master_vehicle_types VALUES 
('1.25T', 'Xe 1.25 Tấn', TRUE), ('2.5T', 'Xe 2.5 Tấn', TRUE), ('5T', 'Xe 5 Tấn', TRUE),
('CONT20', 'Container 20ft', TRUE), ('CONT40', 'Container 40ft', TRUE);

-- 3. CORE TABLES
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    user_code VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) DEFAULT 'STAFF',
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE customers (
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

CREATE TABLE vendors (
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

CREATE TABLE drivers (
    driver_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    id_card VARCHAR(20),
    vendor_id INTEGER REFERENCES vendors(vendor_id),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE vehicles (
    vehicle_id SERIAL PRIMARY KEY,
    plate_number VARCHAR(20) UNIQUE NOT NULL,
    vehicle_type_code VARCHAR(50) REFERENCES master_vehicle_types(type_code),
    vendor_id INTEGER REFERENCES vendors(vendor_id),
    driver_id INTEGER REFERENCES drivers(driver_id),
    is_active BOOLEAN DEFAULT TRUE
);

-- 4. OPERATION TABLES
CREATE TABLE jobs (
    job_id SERIAL PRIMARY KEY,
    job_no VARCHAR(30) UNIQUE NOT NULL,
    customer_id INTEGER REFERENCES customers(customer_id),
    description TEXT,
    etd DATE, eta DATE,
    status_code VARCHAR(50) REFERENCES master_statuses(status_code) DEFAULT 'DRAFT',
    total_revenue DECIMAL(18,2) DEFAULT 0,
    total_cost DECIMAL(18,2) DEFAULT 0,
    profit DECIMAL(18,2) GENERATED ALWAYS AS (total_revenue - total_cost) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE job_services (
    svc_id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(job_id) ON DELETE CASCADE,
    service_type_code VARCHAR(50) REFERENCES master_service_types(service_code),
    scheduled_date DATE,
    scheduled_time TIME,
    origin_address TEXT,
    dest_address TEXT,
    vendor_id INTEGER REFERENCES vendors(vendor_id),
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id),
    driver_id INTEGER REFERENCES drivers(driver_id),
    vendor_text_input TEXT,
    status_code VARCHAR(50) REFERENCES master_statuses(status_code) DEFAULT 'PENDING',
    service_details JSONB DEFAULT '{}',
    msg_vendor TEXT,
    msg_customer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE job_costs (
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

-- 5. AUTOMATION TABLES
CREATE TABLE message_templates (
    template_code VARCHAR(50) PRIMARY KEY,
    content_template TEXT NOT NULL,
    platform VARCHAR(20) DEFAULT 'ZALO'
);
INSERT INTO message_templates VALUES 
('NOTIFY_CUSTOMER_VEHICLE', '5P Logistics: Xe {plate_number} / TX {driver_name} ({driver_phone}) đón hàng lúc {time}.', 'ZALO');

CREATE TABLE automation_logs (
    log_id SERIAL PRIMARY KEY,
    job_id INTEGER,
    trigger_source VARCHAR(50),
    input_content TEXT,
    ai_output JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. TRIGGERS & FUNCTIONS
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

CREATE TRIGGER tr_job_costs_update_totals AFTER INSERT OR UPDATE OR DELETE ON job_costs
    FOR EACH ROW EXECUTE FUNCTION update_job_totals();

-- SEED DATA
INSERT INTO customers (customer_code, company_name) VALUES ('SAMSUNG', 'Samsung Electronics VN');
INSERT INTO vendors (vendor_code, company_name) VALUES ('TAMBAO', 'Vận tải Tam Bảo');