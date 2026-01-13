-- =============================================================================
-- THÊM CÁC CỘT CÒN THIẾU CHO BẢNG CUSTOMERS VÀ VENDORS
-- Chạy file này trong PostgreSQL, sau đó refresh NocoDB
-- =============================================================================

-- CUSTOMERS
ALTER TABLE customers ADD COLUMN IF NOT EXISTS tax_code VARCHAR(20);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS province VARCHAR(100);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS contact_name VARCHAR(100);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(20);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS contact_email VARCHAR(200);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS payment_terms INTEGER DEFAULT 30;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS credit_limit DECIMAL(18,2) DEFAULT 0;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS notes TEXT;

-- VENDORS
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS tax_code VARCHAR(20);
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS province VARCHAR(100);
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS contact_name VARCHAR(100);
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(20);
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS bank_name VARCHAR(100);
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS bank_account VARCHAR(50);
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS payment_terms INTEGER DEFAULT 30;
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS notes TEXT;

-- Xác nhận
SELECT 'Customers columns:' as info, count(*) as total FROM information_schema.columns WHERE table_name = 'customers';
SELECT 'Vendors columns:' as info, count(*) as total FROM information_schema.columns WHERE table_name = 'vendors';
