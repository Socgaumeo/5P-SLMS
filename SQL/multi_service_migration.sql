-- ============================================
-- SLMS Multi-Service Schema Migration
-- Date: 2026-01-17
-- ============================================

-- 1. ADD STRUCTURED CARGO COLUMNS TO job_services
-- ============================================

-- Cargo/Package Details
ALTER TABLE job_services ADD COLUMN IF NOT EXISTS cargo_type VARCHAR(100);
COMMENT ON COLUMN job_services.cargo_type IS 'Type of cargo: PCB, FPC, ELECTRONICS, GARMENT, etc.';

ALTER TABLE job_services ADD COLUMN IF NOT EXISTS package_quantity INTEGER;
COMMENT ON COLUMN job_services.package_quantity IS 'Number of packages: 45';

ALTER TABLE job_services ADD COLUMN IF NOT EXISTS package_unit VARCHAR(20);
COMMENT ON COLUMN job_services.package_unit IS 'Unit type: kiện, thùng, pallet, container, box';

ALTER TABLE job_services ADD COLUMN IF NOT EXISTS weight_kg DECIMAL(12,2);
COMMENT ON COLUMN job_services.weight_kg IS 'Total weight in kilograms';

ALTER TABLE job_services ADD COLUMN IF NOT EXISTS volume_cbm DECIMAL(10,3);
COMMENT ON COLUMN job_services.volume_cbm IS 'Total volume in cubic meters';

ALTER TABLE job_services ADD COLUMN IF NOT EXISTS dimension_length_cm DECIMAL(10,2);
ALTER TABLE job_services ADD COLUMN IF NOT EXISTS dimension_width_cm DECIMAL(10,2);
ALTER TABLE job_services ADD COLUMN IF NOT EXISTS dimension_height_cm DECIMAL(10,2);
COMMENT ON COLUMN job_services.dimension_length_cm IS 'Package length in cm (per package)';
COMMENT ON COLUMN job_services.dimension_width_cm IS 'Package width in cm (per package)';
COMMENT ON COLUMN job_services.dimension_height_cm IS 'Package height in cm (per package)';

-- Invoice & Documents
ALTER TABLE job_services ADD COLUMN IF NOT EXISTS invoice_numbers TEXT;
COMMENT ON COLUMN job_services.invoice_numbers IS 'Comma-separated list of invoice numbers';

ALTER TABLE job_services ADD COLUMN IF NOT EXISTS documents TEXT[];
COMMENT ON COLUMN job_services.documents IS 'Array of document types: Invoice, Packing List, B/L...';

-- Special Requirements
ALTER TABLE job_services ADD COLUMN IF NOT EXISTS special_requirements TEXT;
COMMENT ON COLUMN job_services.special_requirements IS 'Special handling: nâng hạ, giữ lạnh, fragile...';

-- Warehouse-specific
ALTER TABLE job_services ADD COLUMN IF NOT EXISTS storage_start_date DATE;
ALTER TABLE job_services ADD COLUMN IF NOT EXISTS storage_end_date DATE;
COMMENT ON COLUMN job_services.storage_start_date IS 'Start date for warehouse storage';
COMMENT ON COLUMN job_services.storage_end_date IS 'End date for warehouse storage';

-- Rate Calculation
ALTER TABLE job_services ADD COLUMN IF NOT EXISTS rate_unit VARCHAR(20) DEFAULT 'TRIP';
COMMENT ON COLUMN job_services.rate_unit IS 'TRIP, KG, CBM, DAY, CONTAINER, DECLARATION';


-- 2. INSERT SERVICE TYPES (if not exists)
-- ============================================

-- Trucking Services
INSERT INTO master_service_types (service_code, service_name, category)
VALUES 
    ('TRK-SHORT', 'Trucking ngắn (nội vùng < 50km)', 'TRUCKING'),
    ('TRK-LONG', 'Trucking dài (liên tỉnh > 50km)', 'TRUCKING'),
    ('TRK-CONT', 'Trucking container', 'TRUCKING')
ON CONFLICT (service_code) DO NOTHING;

-- Customs Services
INSERT INTO master_service_types (service_code, service_name, category)
VALUES 
    ('CUS-IMPORT', 'Khai báo nhập khẩu', 'CUSTOMS'),
    ('CUS-EXPORT', 'Khai báo xuất khẩu', 'CUSTOMS'),
    ('CUS-TRANSIT', 'Khai báo quá cảnh', 'CUSTOMS')
ON CONFLICT (service_code) DO NOTHING;

-- Warehouse Services
INSERT INTO master_service_types (service_code, service_name, category)
VALUES 
    ('WHS-STORAGE', 'Lưu kho', 'WAREHOUSE'),
    ('WHS-HANDLE', 'Bốc xếp / Nâng hạ', 'WAREHOUSE')
ON CONFLICT (service_code) DO NOTHING;

-- Other Services
INSERT INTO master_service_types (service_code, service_name, category)
VALUES 
    ('SVC-PACK', 'Đóng gói', 'OTHER'),
    ('SVC-INSURE', 'Bảo hiểm hàng hóa', 'OTHER'),
    ('SVC-WAIT', 'Phí chờ (waiting time)', 'OTHER'),
    ('SVC-EXTRA', 'Phí phát sinh khác', 'OTHER')
ON CONFLICT (service_code) DO NOTHING;


-- 3. ADD CATEGORY COLUMN TO master_service_types (if not exists)
-- ============================================
ALTER TABLE master_service_types ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'OTHER';
COMMENT ON COLUMN master_service_types.category IS 'Service category: TRUCKING, CUSTOMS, WAREHOUSE, OTHER';


-- 4. UPDATE EXISTING SERVICE TYPES WITH CATEGORIES
-- ============================================
UPDATE master_service_types SET category = 'TRUCKING' WHERE service_code LIKE 'TRK%';
UPDATE master_service_types SET category = 'CUSTOMS' WHERE service_code LIKE 'CUS%';
UPDATE master_service_types SET category = 'WAREHOUSE' WHERE service_code LIKE 'WHS%';
UPDATE master_service_types SET category = 'OTHER' WHERE service_code LIKE 'SVC%';


-- 5. CREATE MESSAGE TEMPLATES
-- ============================================
INSERT INTO message_templates (template_code, content_template, platform)
VALUES 
    ('TRK_VENDOR_REQUEST', '🚛 YÊU CẦU XE - {customer}

📅 Ngày: {date}
⏰ Giờ lấy hàng: {time}
📦 Invoice: {invoices}
📋 Hàng: {cargo_type} - {quantity} {unit}
⚖️ Trọng lượng: {weight_kg} kg
📐 Kích thước: {dimensions}
🚗 Loại xe: {vehicle_type}
📍 Giao tại: {delivery_address}

Vui lòng điều xe và phản hồi thông tin lái xe.', 'ZALO'),

    ('TRK_CUSTOMER_CONFIRM', '✅ XÁC NHẬN XE - {customer}

📅 Ngày: {date}
⏰ Giờ: {time}
📦 Invoice: {invoices}
🚗 Loại xe: {vehicle_type}
🚘 BKS: {license_plate}
👤 Tài xế: {driver_name}
📱 SĐT: {driver_phone}
🪪 CCCD: {driver_id_card}', 'ZALO'),

    ('WHS_VENDOR_REQUEST', '📦 YÊU CẦU LƯU KHO - {customer}

📅 Ngày nhập kho: {storage_start_date}
📦 Số lượng: {quantity} {unit}
📐 Kích thước: {dimension_length}x{dimension_width}x{dimension_height} cm
⚖️ Khối lượng: {weight_kg} kg
📊 Thể tích: {volume_cbm} CBM
📋 Yêu cầu đặc biệt: {special_requirements}

Vui lòng xác nhận tiếp nhận.', 'ZALO'),

    ('WHS_CUSTOMER_CONFIRM', '✅ XÁC NHẬN NHẬP KHO - {customer}

📅 Ngày nhập: {storage_start_date}
📦 Số lượng: {quantity} {unit}
📐 Kích thước: {dimensions}
📍 Kho: {warehouse_name}
📋 Yêu cầu: {special_requirements}', 'ZALO'),

    ('CUS_VENDOR_REQUEST', '📋 YÊU CẦU KHAI QUAN - {customer}

📅 Ngày: {date}
🚢 Loại: {customs_type}
📦 Invoice: {invoices}
📦 Hàng hóa: {cargo_type}
📁 Chứng từ cần: {required_docs}

Vui lòng xác nhận tiếp nhận hồ sơ.', 'ZALO'),

    ('CUS_CUSTOMER_CONFIRM', '✅ XÁC NHẬN KHAI QUAN - {customer}

📅 Ngày: {date}
🚢 Loại: {customs_type}
📦 Invoice: {invoices}
📋 Trạng thái: Đã tiếp nhận hồ sơ
⏱️ Dự kiến hoàn thành: {estimated_completion}', 'ZALO')
ON CONFLICT (template_code) DO UPDATE SET
    content_template = EXCLUDED.content_template;


-- 6. VERIFY CHANGES
-- ============================================
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'job_services' 
ORDER BY ordinal_position;

SELECT * FROM master_service_types ORDER BY category, service_code;
