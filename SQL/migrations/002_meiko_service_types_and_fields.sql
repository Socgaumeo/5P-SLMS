-- =============================================================================
-- Migration 002: MEIKO Service Types and Extended Fields
-- =============================================================================
-- Changes:
-- 1. Add new service types: TRUCKING_DOM, BORDER_IMP, AIR_IMP, AIR_EXP, SEA_IMP, SEA_EXP
-- 2. Migrate ALL trucking jobs (SHORT, LONG, CONT) to TRUCKING_DOM
-- 3. Deactivate legacy codes: TRUCKING_SHORT, TRUCKING_LONG, TRUCKING_CONT
-- 4. Add missing statuses: IN_TRANSIT, DISPATCHED, DELIVERED
-- 5. Document service_details JSONB expected fields
-- =============================================================================

-- Step 1: Add new service types
INSERT INTO master_service_types (service_code, name_vi, sort_order, is_active)
VALUES
    ('TRUCKING_DOM', 'Vận tải nội địa', 1, TRUE),
    ('BORDER_IMP', 'Nhập khẩu đường bộ', 5, TRUE),
    ('AIR_IMP', 'Vận tải hàng không - Nhập', 6, TRUE),
    ('AIR_EXP', 'Vận tải hàng không - Xuất', 7, TRUE),
    ('SEA_IMP', 'Vận tải đường biển - Nhập', 8, TRUE),
    ('SEA_EXP', 'Vận tải đường biển - Xuất', 9, TRUE)
ON CONFLICT (service_code) DO NOTHING;

-- Step 2: Migrate ALL existing trucking jobs to TRUCKING_DOM
UPDATE job_services
SET service_type_code = 'TRUCKING_DOM'
WHERE service_type_code IN ('TRUCKING_SHORT', 'TRUCKING_LONG', 'TRUCKING_CONT');

-- Step 3: Update master_service_types - deactivate old codes
UPDATE master_service_types SET is_active = FALSE WHERE service_code = 'TRUCKING_SHORT';
UPDATE master_service_types SET is_active = FALSE WHERE service_code = 'TRUCKING_LONG';
UPDATE master_service_types SET is_active = FALSE WHERE service_code = 'TRUCKING_CONT';

-- Step 5: Add missing statuses if not exist
INSERT INTO master_statuses (status_code, name_vi, color_code, is_active)
VALUES
    ('IN_TRANSIT', 'Đang vận chuyển', '#3B82F6', TRUE),
    ('DISPATCHED', 'Đã điều xe', '#8B5CF6', TRUE),
    ('DELIVERED', 'Đã giao hàng', '#10B981', TRUE)
ON CONFLICT (status_code) DO NOTHING;

-- =============================================================================
-- SERVICE_DETAILS JSONB Schema Documentation
-- =============================================================================
-- The service_details JSONB field in job_services stores extended info:
--
-- Common fields:
--   - invoice_number: Số hóa đơn (INV)
--   - cargo_type: Loại hàng
--   - quantity: Số lượng
--   - unit: Đơn vị (kg, pallet, kiện, cont, etc.)
--   - weight_kg: Trọng lượng (kg)
--   - selling_price: Giá bán
--   - buying_price: Giá mua
--   - route: Tuyến đường
--   - notes: Ghi chú
--
-- BORDER_IMP specific fields (Bảng kê IM):
--   - declaration_number: Số tờ khai
--   - china_license_plate: Biển số xe Trung Quốc
--   - vietnam_license_plate: Biển số xe Việt Nam
--   - pallet_qty: Số lượng pallet
--   - fee_transload: Phí sang tải
--   - fee_csht: Phí CSHT
--   - fee_yard: Phí ra vào bãi
--   - fee_declaration: Phí mở tờ khai
--   - fee_domestic_transport: Phí vận tải nội địa
--   - fee_handling: Thủ tục giao nhận
--   - fee_waiting: Phí chờ giờ
--   - fee_extra: Phát sinh
--
-- TRUCKING_DOM specific fields (Truck):
--   - province: Tỉnh
--   - package_qty: Số lượng kiện
--   - fee_transport: Phí vận chuyển
--   - fee_loading: Phí bốc xếp
--   - fee_waiting: Phí chờ giờ
--   - fee_surcharge: Phụ phí
--   - fee_other: Phí khác
--
-- VAT fields:
--   - subtotal: Tổng trước thuế
--   - vat_rate: Tỷ lệ VAT (default 0.10 = 10%)
--   - vat_amount: Số tiền VAT
--   - total_with_vat: Tổng thanh toán
-- =============================================================================

-- Add comment to table for documentation
COMMENT ON COLUMN job_services.service_details IS
'JSONB storing extended service info. See migration 002 for field schema.';
