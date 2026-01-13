-- =============================================================================
-- SLMS - Import Khách hàng và Nhà cung cấp
-- Dữ liệu đã cập nhật theo địa giới hành chính 2025
-- Generated: 2026-01-11 15:34:34
-- =============================================================================

-- =============================================================================
-- 1. CẬP NHẬT SCHEMA - BỔ SUNG CÁC TRƯỜNG CÒN THIẾU
-- =============================================================================

-- Bổ sung trường cho bảng customers
ALTER TABLE customers ADD COLUMN IF NOT EXISTS short_name VARCHAR(50);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS tax_code VARCHAR(20);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS province VARCHAR(100);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS contact_name VARCHAR(100);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(20);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS contact_zalo VARCHAR(20);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS contact_email VARCHAR(200);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS payment_terms INTEGER DEFAULT 30;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS credit_limit DECIMAL(18,2) DEFAULT 0;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Bổ sung trường cho bảng vendors  
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS short_name VARCHAR(50);
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS tax_code VARCHAR(20);
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS province VARCHAR(100);
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS contact_name VARCHAR(100);
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(20);
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS telegram_chat_id VARCHAR(50);
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS bank_name VARCHAR(100);
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS bank_account VARCHAR(50);
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS payment_terms INTEGER DEFAULT 30;
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE vendors ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- =============================================================================
-- 2. IMPORT KHÁCH HÀNG (CUSTOMERS)
-- =============================================================================

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('MCTRANS', 'CÔNG TY TNHH MC TRANS GLOBAL', 'MCTRANS', '0102123106', 'Tầng 2, Tòa nhà HL, Lô A2B Đường Duy Tân, Phường Dịch Vọng Hậu, Quận Cầu Giấy, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('KTXL', 'CÔNG TY TNHH DỊCH VỤ KỸ THUẬT XÂY LẮP VIỆT NAM', 'KTXL', '0104144461', 'Tầng 9, Lô CC5A đường Nam Sơn, Bán đảo Linh Đàm, Phường Hoàng Liệt, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('MTVN', 'CÔNG TY CỔ PHẦN GIẢI PHÁP THIẾT BỊ MÔI TRƯỜNG VIỆT NAM', 'MTVN', '0104491828', 'Số 1, ngõ 126 đường Khuất Duy Tiến, Phường Nhân Chính, Quận Thanh Xuân, Thành phố Hà Nội', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('KD', 'CÔNG TY CỔ PHẦN XÂY DỰNG & KỸ THUẬT KD VIỆT NAM', 'KD', '0104725628', 'Số nhà 24, liền kề 20, Khu Đô thị Văn Khê, Phường Hà Đông, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('UNICO', 'CÔNG TY TNHH UNICO LOGISTICS VIETNAM', 'UNICO', '0106651587', 'Phòng 1201, tầng 12, tòa nhà Hàn Việt, 203 Minh Khai, Phường Bạch Mai, Thành phố Hà Nội', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('LAS', 'CÔNG TY TNHH THƯƠNG MẠI VÀ DỊCH VỤ KỸ THUẬT LAS', 'LAS', '0106708177', 'Tầng 9, Tòa nhà HL, số 6/82 Duy Tân, Phường Cầu Giấy, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('ACS', 'CÔNG TY TNHH ACS LOGISTICS VIỆT NAM', 'ACS', '0106872963', 'Tầng 6, Tòa nhà TTC, Số 19 phố Duy Tân, Phường Dịch Vọng Hậu, Quận Cầu Giấy, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('THIENVUONG', 'CÔNG TY TNHH DỊCH VỤ VÀ THƯƠNG MẠI QUỐC TẾ THIÊN VƯƠNG', 'THIENVUONG', '0106919435', 'Số 6, ngõ 297, ngách 105 đường Trần Cung, phường Nghĩa Đô, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('SILVERMOUNTAIN', 'CÔNG TY TNHH SILVER MOUNTAIN LOGISTICS (VIETNAM)', 'SILVERMOUNTAIN', '0107273271', 'Tầng 8, Tòa nhà IDMC, số 21 phố Duy Tân, Phường Dịch Vọng Hậu, Quận Cầu Giấy, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('VINHPHUC', 'CÔNG TY CỔ PHẦN XÂY DỰNG & KỸ THUẬT VĨNH PHÚC', 'VINHPHUC', '0107370719', 'Số 01, ngách 463/7 Đội Cấn, Phường Ngọc Hà, Thành phố Hà Nội', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('TVT', 'CÔNG TY CỔ PHẦN VẬN TẢI THÁI VIỆT TRUNG', 'TVT', '0107457293', 'Tầng 1, Số Nhà 2, Ngõ 1, Đường Phúc Lợi, Phường Việt Hưng , Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('MESSERTN', 'CÔNG TY TNHH  KHÍ CÔNG NGHIỆP MESSER HẢI PHÒNG - CHI NHÁNH YÊN BÌNH THÁI NGUYÊN', 'MESSERTN', '0200134811-007', 'Lô CN2, KCN Yên Bình giai đoạn 2, diện tích 50,96 ha, Phường Vạn Xuân, Tỉnh Thái Nguyên, Việt Nam', 'Thái Nguyên', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('CTS', 'CÔNG TY TNHH CTS LOGISTICS VIỆT NAM', 'CTS', '0107927340', 'Xóm Lẻ, thôn Triều Khúc, Phường Thanh Liệt, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('WASTE', 'CÔNG TY TNHH KỸ THUẬT CÔNG NGHỆ WASTE VIỆT NAM', 'WASTE', '0108061632', 'Tầng 4, tòa nhà Kinh Đô, số 93 Lò Đúc, Phường Hai Bà Trưng, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('SGINNO', 'CÔNG TY TNHH SG INNO', 'SGINNO', '0108139462', 'Tầng 10 tòa nhà Việt Á, số 9 phố Duy Tân, Phường Dịch Vọng Hậu, Quận Cầu Giấy, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('U&I', 'CÔNG TY CỔ PHẦN LOGISTICS U&I - MIỀN BẮC', 'U&I', '0108156122', 'PHÒNG 1451M, TÒA NHÀ HAPRO, 11B CÁT LINH, PHƯỜNG QUỐC TỬ GIÁM, QUẬN ĐỐNG ĐA, THÀNH PHỐ HÀ NỘI, VIỆT NAM', 'HÀ NỘI', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('KC', 'CÔNG TY TNHH KC INTERNATIONAL LOGISTICS', 'KC', '0108321496', 'Tầng 1, Tòa nhà Ngôi Sao, số 68 đường Dương Đình Nghệ, Phường Cầu Giấy, Thành phố Hà Nội', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('WORLDWIDE', 'CÔNG TY TNHH WORLDWIDE PARTNER LOGISTICS VIỆT NAM', 'WORLDWIDE', '0108968815', 'Tầng 3 Số nhà 23/5/112 đường Hoàng Quốc Việt, Tổ 32, Phường Nghĩa Đô, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('GLOREX', 'CÔNG TY TNHH GLOREX VINA', 'GLOREX', '0110138191', 'Số nhà D30, Liền kề Dreamland, số 107 đường Xuân La, Phường Xuân Đỉnh, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('VECOPIN', 'CÔNG TY TNHH CÔNG NGHỆ VECOPIN VIỆT NAM', 'VECOPIN', '0110633051', 'Số 45 đường Kinh Bắc 42, Khu phố Niềm Xá, Phường Kinh Bắc, Tỉnh Bắc Ninh, Việt Nam', 'Bắc Ninh', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('THANHDAT', 'CÔNG TY TNHH QUẢN LÝ CHUỖI CUNG ỨNG QUỐC TẾ THÀNH ĐẠT', 'THANHDAT', '0110666346', 'Phòng 302, Số 79+81 Trần Xuân Soạn, Phường Hai Bà Trưng, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('TVTL', 'CÔNG TY CỔ PHẦN LOGISTICS THÁI VIỆT TRUNG (VIỆT NAM)', 'TVTL', '0111172597', 'Tầng 1, Số nhà 2, Ngõ 1, Đường Phúc Lợi, Phường Việt Hưng, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('MESSERHP', 'CÔNG TY TNHH  KHÍ CÔNG NGHIỆP MESSER HẢI PHÒNG', 'MESSERHP', '0200134811', 'Tổ dân phố 2, Phường An Dương, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('MESSERHD', 'CÔNG TY TNHH  KHÍ CÔNG NGHIỆP MESSER HẢI PHÒNG - CHI NHÁNH HẢI DƯƠNG', 'MESSERHD', '0200134811-001', 'Khu dân cư Hiệp Thượng, Phường Phạm Sư Mạnh, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('MESSERDQ', 'CÔNG TY TRÁCH NHIỆM HỮU HẠN KHÍ CÔNG NGHIỆP MESSER HẢI PHÒNG - CHI NHÁNH DUNG QUẤT', 'MESSERDQ', '0200134811-002', 'Thôn Tân Hy, Xã Vạn Tường, Tỉnh Quảng Ngãi, Việt Nam', 'Quảng Ngãi', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('VINALINK1', 'CHI NHÁNH CÔNG TY CỔ PHẦN LOGISTICS VINALINK', 'VINALINK1', '0301776205-001', 'Tầng 06, số 14, Láng Hạ, Phường Thành Công, Quận Ba Đình, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('AROMA', 'CÔNG TY TNHH HƯƠNG LIỆU THỰC PHẨM VIỆT NAM', 'AROMA', '0200566628', 'Quốc lộ 10, Phường Trần Hưng Đạo, Phường Thủy Nguyên, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('PHUTAI', 'CÔNG TY TNHH KỸ NGHỆ CÔNG NGHIỆP PHÚ TÀI', 'PHUTAI', '0201205945', 'Số 272 Khu Quảng Luận, Phường Hưng Đạo, Thành Phố Hải Phòng, Việt Nam', 'Hải Phòng', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('UPGAIN', 'CÔNG TY TRÁCH NHIỆM HỮU HẠN SẢN XUẤT UPGAIN (VIỆT NAM)', 'UPGAIN', '0300731233', 'Lô số 64-66-68, đường B, Khu chế xuất Sài Gòn - Linh Trung, Phường Linh Xuân, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('HOACHATCA', 'CÔNG TY TNHH HÓA CHẤT ỨNG DỤNG C.A', 'HOACHATCA', '0301765852', '37 Lê Quang Định, Phường 14, Quận Bình Thạnh, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('KINTETSU', 'CÔNG TY TNHH TIẾP VẬN KINTETSU VIỆT NAM', 'KINTETSU', '2500268961', 'Lô 38G1, Khu công nghiệp Quang Minh, xã Quang Minh, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('NIPPON', 'CHI NHÁNH CÔNG TY LIÊN DOANH TNHH NIPPON EXPRESS (VIỆT NAM) TẠI HÀ NỘI', 'NIPPON', '0302065148-001', 'Tháp Hòa Bình, 106 Hoàng Quốc Việt, Phường Nghĩa Đô, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('EXPOLANKAHN', 'CHI NHÁNH CÔNG TY TNHH GIAO NHẬN EXPOLANKA (VIỆT NAM) TẠI HÀ NỘI', 'EXPOLANKAHN', '0305338347-001', 'L10-02, Tầng 10, tòa nhà Century Towner, 458 Minh Khai, Phường Vĩnh Tuy, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('ANT', 'CÔNG TY TNHH ANT LOGISTICS', 'ANT', '0313226968', '15/28 Đoàn Như Hài, Phường Xóm Chiếu, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('CNL', 'CÔNG TY TNHH CNL TRANSPORT', 'CNL', '0316709667', '341A Lê Trọng Tấn, Phường Sơn Kỳ, Quận Tân Phú, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('LOGIMARKHN', 'CHI NHÁNH HÀ NỘI - CÔNG TY TNHH LOGIMARK INTERNATIONAL', 'LOGIMARKHN', '0316972812-001', 'Tầng 8A, toà nhà 201 Đường Trường Chinh, Phường Phương Liệt, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('MEIKO', 'CÔNG TY TNHH ĐIỆN TỬ MEIKO VIỆT NAM', 'MEIKO', '0500551830', 'Lô CN9, Khu Công nghiệp Thạch Thất – Quốc Oai, Xã Tây Phương, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('KKFASHION', 'CÔNG TY TNHH K+K FASHION', 'KKFASHION', '0500577571', 'Cụm Công nghiệp Ngọc Hòa, thôn Ngọc Giả, Phường Chương Mỹ, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('NEWORDER', 'CÔNG TY TNHH CHỈ SỢI VÀ DÂY DỆT NEW ORDER', 'NEWORDER', '0900997813', 'Khu công nghiệp dệt may Phố Nối B, Phường Đường Hào, Tỉnh Hưng Yên, Việt Nam', 'Hưng Yên', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('SUNGHWAVINA', 'CÔNG TY TNHH SUNG HWA VINA', 'SUNGHWAVINA', '1101803816', 'Lô A-10, đường số 2, Khu Công Nghiệp Hòa Bình, Xã Nhị Thành, Huyện Thủ Thừa, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('PINETREE', 'CÔNG TY TRÁCH NHIỆM HỮU HẠN MỘT THÀNH VIÊN PINETREE', 'PINETREE', '1900583028', 'Ấp Trà Ban 1, Xã Vĩnh Lợi, Tỉnh Cà Mau, Việt Nam', 'Cà Mau', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('MAXTURN', 'CÔNG TY TRÁCH NHIỆM HỮU HẠN MAXTURN APPAREL', 'MAXTURN', '2300316424', 'Lô G1-B, KCN Quế Võ, Phường Phương Liễu, Tỉnh Bắc Ninh, Việt Nam', 'Bắc Ninh', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('RENBAO', 'CÔNG TY TNHH ĐIỆN TỬ RENBAO VIỆT NAM', 'RENBAO', '2301315423', 'Lô CN 6-2B, Khu công nghiệp Quế Võ III, Phường Quế Võ, Tỉnh Bắc Ninh, Việt Nam', 'Bắc Ninh', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('FUKANG', 'CÔNG TY TNHH VẬN TẢI QUỐC TẾ FUKANG', 'FUKANG', '2400883441', 'Tầng 03, Lô số L3-03, Số 08 đường Nguyễn Văn Cừ, Phường Bắc Giang, Tỉnh Bắc Ninh, Việt Nam', 'Bắc Ninh', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('LASHT', 'CÔNG TY TNHH THƯƠNG MẠI VÀ DỊCH VỤ KỸ THUẬT LAS HÀ TĨNH', 'LASHT', '3002257398', 'Nhà bà Mai Thị Bích Phương, Khu tái định cư Đông Yên, Phường Hoành Sơn, Tỉnh Hà Tĩnh, Việt Nam', 'Hà Tĩnh', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('SRITHAI', 'CÔNG TY TNHH SRITHAI ( VIỆT NAM)', 'SRITHAI', '3700255640', 'Số 9, Đường số 2, KCN Sóng Thần 1, Phường Dĩ An, Phường Dĩ An, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('LKVMN', 'CÔNG TY CỔ PHẦN SẢN XUẤT LỌC KHÍ VIỆT', 'LKVMN', '3700869915', 'Lô C3.4, đường N14, KCN Đồng An 2, Phường Bình Dương, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('SEWANGVINA', 'CÔNG TY TNHH SEWANG VINA', 'SEWANGVINA', '3702567275', 'Lô B_3A_CN, Lô B_2B_CN, Lô B_1C_CN, Khu công nghiệp Bàu Bàng, Thị trấn Lai Uyên, Huyện Bàu Bàng, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('TNG', 'CÔNG TY CỔ PHẦN ĐẦU TƯ VÀ THƯƠNG MẠI TNG', 'TNG', '4600305723', 'Số 434/1,đường Bắc Kạn,Phường Hoàng Văn Thụ,Thành Phố Thái Nguyên,Tỉnh Thái Nguyên,Việt Nam', 'Thái Nguyên', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('GANGTHEPTN', 'CÔNG TY CỔ PHẦN CƠ KHÍ GANG THÉP', 'GANGTHEPTN', '4600479367', 'Tổ dân phố Cam Giá 13, Phường Gia Sàng, Tỉnh Thái Nguyên,Việt Nam.', 'Thái Nguyên', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('DONGSUNG', 'CÔNG TY TNHH DONGSUNG VINA', 'DONGSUNG', '4601145688', 'Lô CN3-3 (2), Khu công nghiệp Điềm Thụy, xã Điềm Thụy, tỉnh Thái Nguyên, Việt Nam', 'Thái Nguyên', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('THAIHOA', 'CÔNG TY CP ĐẦU TƯ PHÁT TRIỂN CÔNG NGHIỆP THÁI HOÀ', 'THAIHOA', '4601573108', 'Lô TT3, KCN Điềm Thụy, Phường Phổ Yên, Tỉnh Thái Nguyên, Việt Nam', 'Thái Nguyên', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('DAINESE', 'Công ty TNHH Dainese Việt Nam', 'DAINESE', '4601576003', 'Lô CN13 Lô CN18 Khu Công nghiệp Yên Bình, Phường Vạn Xuân, Tỉnh Thái Nguyên, Việt Nam', 'Thái Nguyên', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('LOCKHIMB', 'CÔNG TY CỔ PHẦN SẢN XUẤT LỌC KHÍ VIỆT MIỀN BẮC', 'LOCKHIMB', '4601576042', 'Thửa số 407, Tờ bản đồ số 39-I, Đường Cách Mạng Tháng 10, KCN Sông Công 1, Phường Bách Quang, Tỉnh Thái Nguyên, Việt Nam', '', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('HLTECH', 'CÔNG TY TNHH HL TECH INTELLIGENT', 'HLTECH', '4601606988', 'Nhà xưởng số 1, Lô CN13-2, Khu công nghiệp Yên Bình, Phường Phổ Yên, Tỉnh Thái Nguyên, Việt Nam', 'Thái Nguyên', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('DATNGUYEN', 'CÔNG TY TNHH DỤNG CỤ CẮT GỌT CHÍNH XÁC ĐẠT NGUYÊN VIỆT NAM', 'DATNGUYEN', '4601611402', 'Tổ Dân Phố Thái Bình, Phường Vạn Xuân, Tỉnh Thái Nguyên, Việt Nam', 'Thái Nguyên', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('TECH', 'CÔNG TY TNHH THƯƠNG MẠI VÀ KỸ THUẬT KD TECH', 'TECH', '4601616584', 'Mặt đường gom Samsung - Tổ Dân phố Giữa, Phường Đồng Tiến, Phường Phổ Yên, Tỉnh Thái Nguyên, Việt Nam', 'Thái Nguyên', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('SEDO VINAKO', 'CÔNG TY TRÁCH NHIỆM HỮU HẠN MỘT THÀNH VIÊN SEDO VINAKO', 'SEDO VINAKO', '4000795057', 'Thôn Đông Yên, Xã Duy Trinh, Huyện Duy Xuyên, Tỉnh Quảng Nam, Việt Nam', 'Quảng Nam', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO customers (customer_code, company_name, short_name, tax_code, address, province, payment_terms, is_active)
VALUES ('SEWANG', 'CÔNG TY TNHH SEWANG VINA', 'SEWANG', '3702567275', 'Lô B_3A_CN, Lô B_2B_CN, Lô B_1C_CN, Khu công nghiệp Bàu Bàng, Thị trấn Lai Uyên, Huyện Bàu Bàng, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 30, TRUE)
ON CONFLICT (customer_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;


-- =============================================================================
-- 3. IMPORT NHÀ CUNG CẤP (VENDORS)
-- =============================================================================

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('AIPAS', 'CÔNG TY CỔ PHẦN KHOA HỌC KỸ THUẬT AIPAS VIỆT NAM', 'AIPAS', '0107826938', 'Số 17, ngõ 214 đường Nguyễn Xiển, Phường Hạ Đình, Quận Thanh Xuân, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('ALS', 'CÔNG TY CỔ PHẦN NHÀ GA HÀNG HÓA ALS', 'ALS', '0106232917', 'Tầng 4, Ga hàng hóa ALS, Cảng HKQT Nội Bài, Xã Phú Minh, Huyện Sóc Sơn, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('ALSB', 'CÔNG TY TRÁCH NHIỆM HỮU HẠN ALS BẮC NINH', 'ALSB', '2300478023', 'Lô CN 05 đường YP6, KCN Yên Phong, Xã Yên Trung, Huyện Yên Phong, Tỉnh Bắc Ninh, Việt Nam', 'Bắc Ninh', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('ANTOAN', 'CÔNG TY CỔ PHẦN KINH DOANH VẬN TẢI AN TOÀN', 'ANTOAN', '0108164691', 'Thôn Đoài, Xã Nội Bài, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('ASAP', 'CÔNG TY TNHH ASAP QUỐC TẾ', 'ASAP', '0104304669', 'Số 36 đường Yên Phụ, Phường Yên Phụ, Quận Tây Hồ, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('ASGL', 'CÔNG TY CỔ PHẦN LOGISTICS ASG', 'ASGL', '4601126886', 'Lô số 5 - Khu công nghiệp Yên Bình, Phường Đồng Tiến, Phường Phổ Yên, Tỉnh Thái Nguyên, Việt Nam', 'Thái Nguyên', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('BAONGUYEN', 'CÔNG TY CỔ PHẦN VẬN TẢI THƯƠNG MẠI BẢO NGUYÊN', 'BAONGUYEN', '4900241083', 'Thôn Nà Han, Xã Tân Thanh, Huyện Văn Lãng, Tỉnh Lạng Sơn, Việt Nam', 'Lạng Sơn', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('CHARTERLINK', 'CÔNG TY TNHH CHARTER LINK LOGISTICS VIỆT NAM', 'CHARTERLINK', '0202216347', 'Tầng 5, Tòa nhà Phúc Hải, số 94 phố Trần Phú, Phường Cầu Đất, Quận Ngô Quyền, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('CMA', 'CÔNG TY CỔ PHẦN CMA-CGM VIỆT NAM', 'CMA', '0304207743', 'Số 81-85, Đường Hàm Nghi, Phường Nguyễn Thái Bình, Quận 1, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('CNCONCAHEO', 'CHI NHÁNH CÔNG TY CỔ PHẦN DỊCH VỤ HÀNG HẢI HÀNG KHÔNG CON CÁ HEO', 'CNCONCAHEO', '0305358801-001', 'Phòng 18-01, Tầng 18, Tháp B, Tòa nhà Epic Tower, Số 19 Phố, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('CNTHIENSONHN', 'CHI NHÁNH CÔNG TY CP ĐẦU TƯ & THƯƠNG MẠI THIÊN SƠN TẠI HÀ NỘI', 'CNTHIENSONHN', '0900615768-002', 'Số 9, Ngõ 84, Phố Ngọc Khánh, Phường Giảng Võ, Quận Ba Đình, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('CNVINALINK01', 'CHI NHÁNH CÔNG TY CỔ PHẦN LOGISTICS VINALINK', 'CNVINALINK01', '0301776205-001', 'Tầng 06, số 14, Láng Hạ, Phường Thành Công, Quận Ba Đình, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('COCO', 'CÔNG TY CỔ PHẦN TIẾP VẬN COCO VIỆT NAM', 'COCO', '0108797768', 'Số 17, ngõ 214 đường Nguyễn Xiển, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('COSCOHP', 'Chi nhánh Công ty TNHH Cosco Shipping Lines (Việt Nam) tại Hải Phòng', 'COSCOHP', '0301471348-001', 'Số 4 Lê Thánh Tông, Phường Máy Tơ, Quận Ngô Quyền, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('CPNSAIGON', 'CÔNG TY CỔ PHẦN CHUYỂN PHÁT NHANH SÀI GÒN', 'CPNSAIGON', '0312780059', 'Số 2/7 đường Nguyễn Trọng Lội, Phường 4, Quận Tân Bình, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('CTKMHP', 'CÔNG TY TNHH KHẢI MINH GROUPS-CHI NHÁNH HẢI PHÒNG', 'CTKMHP', '0110573846-003', 'Số 13, Lô 7B, đường Lê Hồng Phong, Phường Đông Khê, Quận Ngô Quyền, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('CVHP', 'Cảng vụ Đường thuỷ nội địa Hải Phòng', 'CVHP', '0201184942', 'Số 1 đường Cù Chính Lan, Phường Minh Khai, Quận Hồng Bàng, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('DPTHP', 'CHI NHÁNH CÔNG TY TNHH VẬN TẢI VÀ ĐẠI LÝ VẬN TẢI ĐA PHƯƠNG THỨC TẠI HẢI PHÒNG', 'DPTHP', '0105430472-001', 'Tầng 2, toà nhà Hải An, Km 2+200, đường Đình Vũ, Phường Đông Hải 2, Quận Hải An, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('ECUWORLDWIDE', 'CHI NHÁNH CÔNG TY CỔ PHẦN ECU WORLDWIDE VIỆT NAM TẠI HẢI PHÒNG', 'ECUWORLDWIDE', '0304258307-002', 'Tầng 3, Phong Lan Building, Số 20 Đinh Tiên Hoàng, Phường Hoàng Văn Thụ, Quận Hồng Bàng, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('EST', 'CÔNG TY TNHH ETS TOÀN CẦU LOGISTICS VINA', 'EST', '0315348062', '58-62 Đường Nguyễn Phi Khanh, Phường Tân Định, Quận 1, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('FREIGHT', 'CÔNG TY TNHH KING FREIGHT LOGISTICS VIETNAM - CHI NHÁNH HÀ NỘI', 'FREIGHT', '0315460917-002', 'Tầng 18, tòa nhà Detech, số 8 đường Tôn Thất Thuyết, Phường Mỹ Đình 2, Quận Nam Từ Liêm, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('GLOBELINK', 'CÔNG TY TNHH GLOBELINK (VIETNAM) FORWARDING', 'GLOBELINK', '0318794918', 'Văn phòng số 3, Tầng 25, Tòa nhà Pearl Plaza, 561A Điện Biên, Phường 25, Quận Bình Thạnh, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('GNHHTSN', 'CHI NHÁNH HÀ NỘI - CÔNG TY TNHH DỊCH VỤ GIAO NHẬN HÀNG HÓA TÂN SƠN NHẤT', 'GNHHTSN', '0304312360-002', 'Số 9, Đường Trung Yên 14, Phường Yên Hoà, Quận Cầu Giấy, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('GRANDFORWARD', 'Công ty Cổ phần Grand Forward Việt Nam', 'GRANDFORWARD', '0201809168', 'Lô đất CN2.5A khu công nghiệp MP Đình Vũ, Phường Đông Hải 2, Quận Hải An, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('HARMONY', 'CÔNG TY TNHH HARMONY LOGISTICS', 'HARMONY', '2301211946', 'Số 37 ngõ 63 Trần Quốc Vượng, Tổ 12, Phường Dịch Vọng Hậu, Quận Cầu Giấy, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('HEUNGAHP', 'CHI NHÁNH CÔNG TY TNHH HEUNG A LINE VIỆT NAM TẠI THÀNH PHỐ HẢI PHÒNG', 'HEUNGAHP', '0305418225-001', 'Phòng 613+614+615+616, tầng 6, tòa nhà Thành Đạt 3, số 4 Đườ, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('HHHK', 'CÔNG TY CỔ PHẦN DỊCH VỤ HÀNG HÓA HÀNG KHÔNG VIỆT NAM', 'HHHK', '0106825508', 'Cảng Hàng không quốc tế Nội Bài, Xã Phú Cường, Huyện Sóc Sơn, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('HIGHPASS', 'CÔNG TY TNHH LOGISTICS HIGHPASS VIỆT NAM', 'HIGHPASS', '0201948034', 'Số 175-176 Bình Kiều 2, Phường Đông Hải 2, Quận Hải An, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('HNBVINA', 'CÔNG TY TNHH THƯƠNG MẠI VÀ DỊCH VỤ HNB VINA', 'HNBVINA', '4601331691', 'Tổ dân phố Chiến Thắng, Phường Đồng Tiến, Phường Phổ Yên, Tỉnh Thái Nguyên, Việt Nam', 'Thái Nguyên', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('HNP', 'CÔNG TY TNHH THƯƠNG MẠI VẬN TẢI HOÀNG NGỌC PHÁT', 'HNP', '0200884525', 'Số 1/36 C8 đường vòng Vạn Mỹ, Phường Vạn Mỹ, Quận Ngô Quyền, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('HOANGXUAN', 'CÔNG TY CỔ PHẦN THƯƠNG MẠI HOÀNG XUÂN', 'HOANGXUAN', '0200727995', 'Số 16 lô E ngõ tập thể 19/5 đường Lê Thánh Tông, Phường Máy Tơ, Quận Ngô Quyền, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('HTP', 'CÔNG TY TNHH DỊCH VỤ VẬN TẢI HUY TOÀN PHÁT', 'HTP', '0201573466', 'Số 182 Đà Nẵng, Phường Lạc Viên, Quận Ngô Quyền, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('HUUNGHIEX', 'CÔNG TY CỔ PHẦN VẬN TẢI QUỐC TẾ HỮU NGHỊ EXPRESS', 'HUUNGHIEX', '4900895022', 'Thôn Sẩy, Xã Đồng Tân, Huyện Hữu Lũng, Tỉnh Lạng Sơn, Việt Nam', 'Lạng Sơn', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('ICAVN', 'CÔNG TY TNHH ICA VIỆT NAM', 'ICAVN', '0104053020', 'số 120 ngõ 765 Nguyễn Văn Linh, tổ 7, Phường Phúc Lợi, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('INBUS', 'Công Ty TNHH Inbus Việt Nam', 'INBUS', '0105136745', 'Số 4, ngõ 262B Nguyễn Trãi, Phường Thanh Xuân Trung, Quận Thanh Xuân, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('JASVN', 'CHI NHÁNH CÔNG TY TNHH JAS VIỆT NAM', 'JASVN', '0311741025-001', 'Tòa nhà VCCI, Số 9 Đào Duy Anh, Phường Phương Mai, Quận Đống Đa, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('KMHP', 'CÔNG TY TNHH KHẢI MINH GROUPS-CHI NHÁNH HẢI PHÒNG', 'KMHP', '0110573846-003', 'Số 13, Lô 7B, đường Lê Hồng Phong, Phường Đông Khê, Quận Ngô Quyền, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('LIENCAU', 'CHI NHÁNH CÔNG TY TNHH LIÊN CẦU VIỆT NAM', 'LIENCAU', '0304198633-001', 'Tầng 8 tòa nhà ACB số 15 Hoàng Diệu, Phường Minh Khai, Quận Hồng Bàng, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('LIENHOP', 'CÔNG TY TNHH VẬN TẢI BIỂN LIÊN HỢP', 'LIENHOP', '0200573424', 'Số 03 Lê Thánh Tông, Phường Gia Viên, Quận Ngô Quyền, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('LIENKETV', 'CÔNG TY CỔ PHẦN LIÊN KẾT VÀNG', 'LIENKETV', '0200994849', 'Số 445 Đà Nẵng, Phường Đông Hải, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('LKVN', 'CÔNG TY TNHH LIÊN KẾT LK VIỆT NAM', 'LKVN', '0109140005', 'N03-SH27, Khu đô thị Mipec, Phường Kiến Hưng, Quận Hà Đông, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('LOGIMARK', 'CHI NHÁNH HÀ NỘI - CÔNG TY TNHH LOGIMARK INTERNATIONAL', 'LOGIMARK', '0316972812-001', 'Tầng 5, toà nhà V building, số 125 - 127 Phố Bà Triệu, Phường Nguyễn Du, Quận Hai Bà Trưng, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('LOGQT', 'CÔNG TY TNHH LOGISTICS QUỐC TẾ EXCELLENT', 'LOGQT', '2301180430', '183 Đường Lê Thánh Tông, Khu Khả Lễ, Phường Võ Cường, Thành phố Bắc Ninh, Tỉnh Bắc Ninh, Việt Nam', 'Bắc Ninh', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('MACSHP', 'CHI NHÁNH CÔNG TY CỔ PHẦN HÀNG HẢI MACS TẠI HẢI PHÒNG', 'MACSHP', '0302326311-005', 'Lô CN 2.4 và KB 4.3 Khu công nghiêp Minh Phương Đình Vũ, Phường Đông Hải, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('MAERSK', 'CÔNG TY TNHH MAERSK VIỆT NAM', 'MAERSK', '0303728327', 'Tầng 15, Sofic Tower, Số 10 Mai Chí Thọ, Phường Thủ Thiêm, Thành phố Thủ Đức, Thành phố Hồ Chí Minh, Việt Nam', 'Thủ Đức', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('MAXPEEDVN', 'CÔNG TY TNHH MAXPEED VIỆT NAM', 'MAXPEEDVN', '0102847194', 'P702 tầng 7, tòa nhà VET, 98 Hoàng Quốc Việt, Phường Nghĩa Đô, Quận Cầu Giấy, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('MELINH', 'CÔNG TY CỔ PHẦN  GIAO NHẬN KHO VẬN MÊ LINH', 'MELINH', '2500221089', 'Km 16, quốc lộ 2A, Phường Phúc Yên, Tỉnh Phú Thọ, Việt Nam', 'Phú Thọ', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('MG', 'CÔNG TY CỔ PHẦN MG LOGISTICS', 'MG', '0109670595', 'Tầng 21, Toà nhà Capital Tower, Số 109 Trần Hưng Đạo, Phường Cửa Nam, Quận Hoàn Kiếm, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('MIPEC', 'CÔNG TY CỔ PHẦN CẢNG MIPEC', 'MIPEC', '0201641148', 'Bán đảo Đình Vũ, thuộc Khu kinh tế Đình Vũ - Cát Hải, Phường Đông Hải, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('MNSHIPPINGHP', 'CÔNG TY TNHH MN SHIPPING HẢI PHÒNG', 'MNSHIPPINGHP', '0201863292', 'Phòng 507 - 508, Tầng 5, Tòa nhà Thành Đạt 1, Số 3 Lê Thánh, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('NAMDV', 'CÔNG TY CỔ PHẦN CẢNG NAM ĐÌNH VŨ', 'NAMDV', '0201741248', 'Lô CA1, Khu công nghiệp Nam Đình Vũ (khu 1), Phường Đông Hải 2, Quận Hải An, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('NOIBAI', 'CÔNG TY CỔ PHẦN DỊCH VỤ HÀNG HÓA NỘI BÀI', 'NOIBAI', '0101640729', 'Sân bay quốc tế Nội Bài, Xã Mai Đình, Huyện Sóc Sơn, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('OOCLVN', 'CÔNG TY TNHH OOCL VIỆT NAM', 'OOCLVN', '0303195358', 'Toà nhà Saigon Trade Center số 37 đường Tôn Đức Thắng, Phường Bến Nghé, Quận 1, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('PACIFIC', 'CÔNG TY TNHH PACIFIC LINES', 'PACIFIC', '0309912234', '', '', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('PILHP', 'CHI NHÁNH CÔNG TY TNHH PIL VIỆT NAM TẠI THÀNH PHỐ HẢI PHÒNG', 'PILHP', '0303449450-004', 'Phòng số 641 + 642 - Tầng 6, Tòa nhà Thành Đạt 1, số 3 Lê Thánh Tông, Phường Máy Tơ (hết hiệu lực), Quận Ngô Quyền, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('PL', 'CÔNG TY CỔ PHẦN TIẾP VẬN PL', 'PL', '0102741399', 'Thôn Huỳnh Cung, Xã Tam Hiệp, Huyện Thanh Trì, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('QUANTERM', 'CÔNG TY TNHH QUANTERM LOGISTICS VIETNAM', 'QUANTERM', '0311089603', 'Tòa nhà H2, 196 Hoàng Diệu, phường 08, Quận 4, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('RONGTBDHP', 'CHI NHÁNH CÔNG TY TNHH GIAO NHẬN RỒNG THÁI BÌNH DƯƠNG TẠI HẢI PHÒNG', 'RONGTBDHP', '0109477538-001', 'K3, Khu C Vidifi Duyên Hải, Khu dịch vụ cuối tuyến Đình Vũ, Phường Đông Hải, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('SHIPCO', 'CHI NHÁNH CÔNG TY TNHH SHIPCO TRANSPORT VIỆT NAM TẠI HẢI PHÒNG', 'SHIPCO', '0305951338-001', 'Phòng 411, Tầng 4, Tòa nhà TD Business Center, Lô 20A Đường Lê Hồng Phong, Phường Đông Khê, Quận Ngô Quyền, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('SIEUSAOTC', 'CÔNG TY TNHH GIAO NHẬN VẬN CHUYỂN SIÊU SAO TOÀN CẦU', 'SIEUSAOTC', '0302385187', 'Phường 1508, Tầng 15, Tòa Nhà Vincom Center, Số 72 Lê Thánh Tôn, Phường Bến Nghé, Quận 1, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('SITC', 'Công ty TNHH SITC Việt Nam', 'SITC', '0200919545', 'Phường 419+420+421, TD-business Center, lô 20a Lê Hồng Phong, Phường Đằng Giang, Quận Ngô Quyền, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('SITCDV', 'CÔNG TY TNHH TIẾP VẬN SITC-ĐÌNH VŨ', 'SITCDV', '0201145622', 'Cảng Đình Vũ, Phường Đông Hải 2, Quận Hải An, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('SONTHANH', 'CÔNG TY CỔ PHẦN SƠN THÀNH HOLDINGS', 'SONTHANH', '0110442931', 'Tầng 2, số 79+81 Trần Xuân Soạn, Phường Phạm Đình Hổ, Quận Hai Bà Trưng, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('SOONEST', 'CÔNG TY TNHH SOONEST EXPRESS (VIETNAM)', 'SOONEST', '0110737639', 'Phòng 6, Tầng 12, Tòa nhà VP Sông Hồng, số 165 Thái Hà, Phường Đống Đa, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('SPIDER', 'CÔNG TY CP GIAO HÀNG NHANH SPIDER', 'SPIDER', '3301700057', 'Số 6/156 đường Tôn Thất Thiệp, Tây Lộc, Thành phố Huế', 'Huế', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('SUNGHWA', 'CÔNG TY TNHH SUNG HWA VINA', 'SUNGHWA', '1101803816', 'Lô A-10, đường số 2, Khu Công Nghiệp Hòa Bình, Xã Nhị Thành, Huyện Thủ Thừa, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('SUNSHINE', 'CÔNG TY TNHH SUNSHINE LINE AGENCIES VIỆT NAM', 'SUNSHINE', '0202248444', 'Tầng 4, Tòa nhà Thành Đạt 1, Số 3 đường Lê Thánh Tông, Phường Máy Tơ (hết hiệu lực), Quận Ngô Quyền, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('TAMBAO2', 'CÔNG TY CỔ PHẦN DỊCH VỤ THƯƠNG MẠI VÀ VẬN CHUYỂN TAM BẢO 2', 'TAMBAO2', '0108988307', 'Nhà số 2, Xóm Mới, Thôn Thái Phù, Xã Mai Đình, Huyện Sóc Sơn, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('TANCANG128', 'CÔNG TY CỔ PHẦN TÂN CẢNG 128 - HẢI PHÒNG', 'TANCANG128', '0200870931', 'Hạ Đoạn, Phường Đông Hải 2, Quận Hải An, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('TANCANG189', 'Công ty Cổ phần Tân Cảng - 189 Hải Phòng', 'TANCANG189', '0201183522', 'Khu công nghiệp Đình Vũ, Phường Đông Hải 2, Quận Hải An, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('TANCANGHP', 'CÔNG TY TNHH CẢNG CONTAINER QUỐC TẾ TÂN CẢNG HẢI PHÒNG', 'TANCANGHP', '0201222436', 'Khu Đôn Lương, Thị trấn Cát Hải, Huyện Cát Hải, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('TANCANGMB', 'CHI NHÁNH TÂN CẢNG MIỀN BẮC - CÔNG TY TNHH MỘT THÀNH VIÊN TỔNG CÔNG TY TÂN CẢNG SÀI GÒN', 'TANCANGMB', '0300514849-006', 'Số 808 đường Lê Hồng Phong, Phường Thành Tô, Quận Hải An, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('TANVINHTHINH', 'CHI NHÁNH CÔNG TY TNHH DỊCH VỤ VẬN TẢI TÂN VĨNH THỊNH', 'TANVINHTHINH', '0301464414-001', 'Phòng 814 toà nhà TD Business center, lô 20A, đường Lê Hồng Phong, Phường Đông Khê, Quận Ngô Quyền, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('TCKM', 'CHI NHÁNH CÔNG TY TNHH TOÀN CẦU KHẢI MINH TẠI HẢI PHÒNG', 'TCKM', '0103076466-004', 'Tầng 4, Tòa nhà Hải Minh, Km 105 đường Nguyễn Bỉnh Khiêm, Phường Đông Hải 2, Quận Hải An, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('TCL', 'CÔNG TY TNHH THƯƠNG MẠI DỊCH VỤ VÀ TIẾP VẬN TCL', 'TCL', '2400992909', 'Số nhà 74 đường Nguyên Hồng, Phường Việt Yên, Tỉnh Bắc Ninh, Việt Nam', 'Bắc Ninh', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('TDNT', 'CÔNG TY TNHH TDNT', 'TDNT', '0311034812', 'B96 Bạch Đằng, Phường Tân Sơn Hoà, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('THAMI', 'CÔNG TY TNHH THAMI LOGISTICS HÀ NỘI', 'THAMI', '0106931143', 'Phường 504 Tòa nhà Thăng Long, 105 Láng Hạ, Phường Láng Hạ, Quận Đống Đa, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('THEKY', 'CÔNG TY CỔ PHẦN TIẾP VẬN THẾ KỶ', 'THEKY', '4601157771', 'Lô CN 1-1, đường YP6, KCN Yên Phong, Tỉnh Bắc Ninh, Việt Nam', 'Bắc Ninh', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('THTE', 'CÔNG TY CỔ PHẦN THT E-LOGISTICS', 'THTE', '0202100776', 'Lô KB2.5 và KB2.12 Khu Công Nghiệp MP Đình Vũ thuộc Khu Kinh, Phường Đông Hải 2, Quận Hải An, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('THUANVU', 'CÔNG TY TNHH THƯƠNG MẠI VÀ DỊCH VỤ VẬN TẢI THUẬN VŨ', 'THUANVU', '0201331763', 'Số 203B đường Đà Nẵng, Phường Cầu Tre, Quận Ngô Quyền, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('TOCDO', 'CÔNG TY CỔ PHẦN TỐC ĐỘ', 'TOCDO', '0303108080', '44 Đường Nguyễn Văn Kỉnh, Khu phố 1, Phường Thạnh Mỹ Lợi, Thành phố Thủ Đức, Thành phố Hồ Chí Minh, Việt Nam', 'Thủ Đức', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('TTP', 'CÔNG TY TNHH GIAO NHẬN T.T.P', 'TTP', '0201040877', 'Số 3 Lê Thánh Tông, Phường Máy Tơ, Quận Ngô Quyền, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('TUYENCONT', 'CÔNG TY TNHH TUYẾN CONTAINER T.S. HÀ NỘI', 'TUYENCONT', '0201747264', 'Phòng 520, Tầng 5 Tòa nhà TD Business Center, Lô 20A đường Lê Hồng Phong, Phường Đông Khê, Quận Ngô Quyền, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('UDCNL', 'CÔNG TY CỔ PHẦN ỨNG DỤNG CÔNG NGHỆ LOGISTICS', 'UDCNL', '0317291301', '2A Đường số 5, Phường An Phú, Thành phố Thủ Đức, Thành phố Hồ Chí Minh, Việt Nam', 'Thủ Đức', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('VANDATTB', 'CÔNG TY CỔ PHẦN VẠN ĐẠT THÁI BÌNH', 'VANDATTB', '0101514379', 'Số 21, phố Hồng Phúc, Phường Nguyễn Trung Trực, Quận Ba Đình, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('VICONSHIPHCMHN', 'CHI NHÁNH CÔNG TY TNHH MỘT THÀNH VIÊN VICONSHIP HỒ CHÍ MINH TẠI THÀNH PHỐ HÀ NỘI', 'VICONSHIPHCMHN', '0317513875-001', 'số 47 Cửa Đông, Phường Hoàn Kiếm, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('VIETHAN', 'CÔNG TY TNHH TIẾP VẬN VIỆT HÀN', 'VIETHAN', '0107435564', 'Số 28 A20, tập thể Nghĩa Tân, Phường Nghĩa Tân, Quận Cầu Giấy, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('VIETNAMCONTROL', 'CÔNG TY CỔ PHẦN GIÁM ĐỊNH KHỬ TRÙNG VIETNAMCONTROL', 'VIETNAMCONTROL', '0310922300', '136 Lê Đình Cẩn, Phường Tân Tạo, Quận Bình Tân, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('VIETTRANSIMEX', 'CÔNG TY TNHH XNK VIETTRANSIMEX', 'VIETTRANSIMEX', '0109321403', 'Số 2 ngõ 18 đường Ngô Chi Lan, Xã Sóc Sơn, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('VINAFCOSHIPPING', 'CÔNG TY CỔ PHẦN VẬN TẢI BIỂN VINAFCO', 'VINAFCOSHIPPING', '0105275178', 'Thôn Tự Khoát, Xã Ngũ Hiệp, Huyện Thanh Trì, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('VSC', 'CÔNG TY CỔ PHẦN VSC GREEN LOGISTICS', 'VSC', '0201768923', 'Lô CC2 - Khu công nghiệp MP Đình Vũ, Phường Đông Hải, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('VVMV', 'CHI NHÁNH CÔNG TY CỔ PHẦN VINH VÂN MINH VÂN TẠI HÀ NỘI', 'VVMV', '0305024358-001', 'Tầng 11, tòa nhà Văn phòng CLand, số 156 Xã Đàn 2, Phường Nam Đồng, Quận Đống Đa, Thành phố Hà Nội, Việt Nam', 'Hà Nội', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('WR1', 'CHI NHÁNH CÔNG TY CỔ PHẦN GIAO NHẬN TIẾP VẬN QUỐC TẾ - WR1', 'WR1', '0303957341-003', 'Tầng trệt, Tòa nhà Cảng Sài Gòn, Số 3 Nguyễn Tất Thành, phường 13, Quận 4, Thành phố Hồ Chí Minh, Việt Nam', 'Hồ Chí Minh', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('XUANCUONG', 'CÔNG TY CỔ PHẦN HỮU NGHỊ XUÂN CƯƠNG', 'XUANCUONG', '4900239158', 'Số 175, đường Trần Đăng Ninh, Phường Tam Thanh, Thành phố Lạng Sơn, Tỉnh Lạng Sơn, Việt Nam', 'Lạng Sơn', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;

INSERT INTO vendors (vendor_code, company_name, short_name, tax_code, address, province, vendor_type, is_active)
VALUES ('YANGMINGHP', 'Chi nhánh Công ty TNHH Yang Ming Shipping (Việt Nam) tại thành phố Hải Phòng', 'YANGMINGHP', '0313316562-002', 'Tầng 6, tòa nhà DG Tower, số 15 Trần Phú, Phường Cầu Đất, Quận Ngô Quyền, Thành phố Hải Phòng, Việt Nam', 'Hải Phòng', 'LOGISTICS', TRUE)
ON CONFLICT (vendor_code) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    short_name = EXCLUDED.short_name,
    tax_code = EXCLUDED.tax_code,
    address = EXCLUDED.address,
    province = EXCLUDED.province,
    updated_at = CURRENT_TIMESTAMP;


-- =============================================================================
-- 4. VIEWS HỖ TRỢ
-- =============================================================================

-- View: Danh sách khách hàng đầy đủ
CREATE OR REPLACE VIEW v_customers AS
SELECT 
    customer_id,
    customer_code,
    company_name,
    short_name,
    tax_code,
    address,
    province,
    contact_name,
    contact_phone,
    contact_zalo,
    contact_email,
    payment_terms,
    credit_limit,
    is_active,
    created_at
FROM customers
WHERE is_active = TRUE
ORDER BY company_name;

-- View: Danh sách nhà cung cấp đầy đủ
CREATE OR REPLACE VIEW v_vendors AS
SELECT 
    vendor_id,
    vendor_code,
    company_name,
    short_name,
    tax_code,
    address,
    province,
    vendor_type,
    contact_name,
    contact_phone,
    telegram_chat_id,
    bank_name,
    bank_account,
    payment_terms,
    is_active,
    created_at
FROM vendors
WHERE is_active = TRUE
ORDER BY company_name;

-- =============================================================================
-- HOÀN TẤT IMPORT
-- =============================================================================
-- Tổng số khách hàng: 60
-- Tổng số nhà cung cấp: 95
-- =============================================================================
