-- =============================================================================
-- IMPORT DANH SÁCH LÁI XE TAM BẢO VÀO SLMS
-- Nguồn: Truck_E-Booking_Plan___Jan_26__1_.xlsx - Sheet "DS LX"
-- Ngày tạo: 12/01/2026
-- Tổng số: 145 lái xe
-- =============================================================================

-- PHẦN 1: TẠO BẢNG DRIVERS (NẾU CHƯA CÓ)
-- =============================================================================

CREATE TABLE IF NOT EXISTS drivers (
    driver_id SERIAL PRIMARY KEY,
    driver_code VARCHAR(20) UNIQUE NOT NULL,
    employee_id VARCHAR(20),
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    id_card VARCHAR(20),
    id_card_date DATE,
    id_card_place VARCHAR(200),
    date_of_birth DATE,
    address TEXT,
    vendor_id INTEGER REFERENCES vendors(vendor_id),
    license_plate VARCHAR(20),
    vehicle_type VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index cho tìm kiếm nhanh
CREATE INDEX IF NOT EXISTS idx_drivers_phone ON drivers(phone);
CREATE INDEX IF NOT EXISTS idx_drivers_license_plate ON drivers(license_plate);
CREATE INDEX IF NOT EXISTS idx_drivers_vendor ON drivers(vendor_id);

-- PHẦN 2: TẠO BẢNG VEHICLES (NẾU CHƯA CÓ)
-- =============================================================================

CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id SERIAL PRIMARY KEY,
    license_plate VARCHAR(20) UNIQUE NOT NULL,
    vehicle_type VARCHAR(50),
    capacity_tons DECIMAL(5,2),
    capacity_cbm DECIMAL(6,2),
    vendor_id INTEGER REFERENCES vendors(vendor_id),
    driver_id INTEGER REFERENCES drivers(driver_id),
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vehicles_vendor ON vehicles(vendor_id);

-- PHẦN 3: IMPORT DANH SÁCH LÁI XE TAM BẢO
-- =============================================================================

-- Lấy vendor_id của Tam Bảo (giả sử đã có trong bảng vendors)
DO $$
DECLARE
    v_tambao_id INTEGER;
BEGIN
    -- Tìm hoặc tạo vendor Tam Bảo
    SELECT vendor_id INTO v_tambao_id FROM vendors WHERE vendor_code = 'TAMBAO' LIMIT 1;
    
    IF v_tambao_id IS NULL THEN
        INSERT INTO vendors (vendor_code, company_name, short_name, vendor_type, is_active)
        VALUES ('TAMBAO', 'Công ty TNHH Vận tải Tam Bảo', 'Tam Bảo', 'TRUCKING', TRUE)
        RETURNING vendor_id INTO v_tambao_id;
    END IF;
    
    RAISE NOTICE 'Tam Bảo vendor_id: %', v_tambao_id;
END $$;


-- Danh sách lái xe
INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0013', '13', 'Trần Xuân Cường', '0972029223', '1084007116', '29H 70692', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0013');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0015', '15', 'Nguyễn Văn Thích', '0378296893', '1084031018', '29E 26078', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0015');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0017', '17', 'Nguyễn Văn Thất', '0977575165', '1088032109', '29H 73165', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0017');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0027', '27', 'Nguyễn Sơn Hà', '0856924896', '1079015952', '29E 26072', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0027');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0028', '28', 'Đường Tiến Huynh', '0972532313', '1083055401', '29H 75921', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0028');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0029', '29', 'Ngô Văn Dương', '0973607909', '1088016140', '29E 25841', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0029');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0030', '30', 'Nguyễn Xuân Khương', '0984473430', '1080049998', '29H 76986', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0030');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0051', '51', 'Khổng Văn Khương', '0968695008', '22071022241', '14H 07755', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0051');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0062', '62', 'Phạm Văn Mười', '0364059765', '30054002458', '29H 81313', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0062');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0065', '65', 'Phùng Đình Trọng', '0983448104', '1079035137', '29H 83575', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0065');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0083', '83', 'Vũ Đăng Khoa', '0969899776', '34062000006', '29C 98544', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0083');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0094', '94', 'Nguyễn Thanh Hà', '0385986900', '1092016817', '29H 24690', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0094');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0117', '117', 'Vũ Doãn Cao', '0898299868', '34085007908', '29H 94922', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0117');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0122', '122', 'Ngô Văn Dương', '0987758234', '1088031061', '29H 70760', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0122');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0124', '124', 'Dương Ngọc Sơn', '0971606168', '1079018260', '29E 26087', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0124');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0129', '129', 'Trần Quốc Hùng', '0978020129', '1084036104', '29H 79237', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0129');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0134', '134', 'Nguyễn Văn Quân', '0979118894', '1088034771', '29H 80860', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0134');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0143', '143', 'Nguyễn Văn Thủy', '0962597790', '1090035648', '29H 76713', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0143');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0149', '149', 'Đường Văn Huyền', '0348950112', '1085018200', '29H 95015', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0149');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0153', '153', 'Vương Xuân Cảnh', '0986717542', '1086027960', '29H 99563', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0153');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0164', '164', 'Trần Văn Tú', '0978559059', '1085018234', '29H 81482', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0164');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0165', '165', 'Nguyễn Duy Hồng', '0868929141', '1095020260', '29C 64515', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0165');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0184', '184', 'Đỗ Huy Thông', '0393948532', '19084004964', '29H 71723', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0184');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0185', '185', 'Lê Văn Vũ', '0961560192', '1088052738', '29C 98172', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0185');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0188', '188', 'Tạ Văn Minh', '0988714514', '1087027458', '29H 72829', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0188');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0211', '211', 'Nguyễn Văn Thinh', '0968298992', '1087046945', '29K 05432', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0211');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0212', '212', 'Lê Văn Tuyên', '0362312350', '1090028092', '29H 37726', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0212');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0227', '227', 'Trần Anh Tú', '0968886271', '19098008640', '29H 83578', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0227');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0235', '235', 'Trịnh Viết Quang', '0964917044', '1082006525', '29H 70769', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0235');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0242', '242', 'Nguyễn Xuân Quỳnh', '0989260641', '1092028505', '29K 05655', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0242');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0252', '252', 'Trần Anh Tuấn', '0376971078', '36073011430', '29H 73059', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0252');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0267', '267', 'Trần Văn Công', '0867128823', '1092001150', '29H 24520', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0267');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0268', '268', 'Nguyễn Văn Hùng', '0962054884', '1084039741', '29H 40598', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0268');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0279', '279', 'Nguyễn Văn Đào', '0971617763', '1061027458', '29K 05797', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0279');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0280', '280', 'Lê Đức Hùng', '0981662533', '1096024824', '29H 76819', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0280');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0286', '286', 'Nguyễn Văn Thành', '0963067839', '1084041218', '29H 73022', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0286');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0300', '300', 'Nguyễn Quốc Tuấn', '0367517039', '1082011149', '29H 45344', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0300');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0302', '302', 'Nguyễn Văn Khương', '0392058535', '24091017870', '98H 00786', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0302');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0303', '303', 'Đinh Cao Đỉnh', '0984705515', '19081000204', '29H 27651', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0303');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0306', '306', 'Nguyễn Minh Thắng', '0982231561-0914687733', '1074006130', '29H 75545', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0306');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0307', '307', 'Lê Văn Cường', '0395653689', '34094016895', '29H 79107', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0307');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0309', '309', 'Nguyễn Văn Hoàng', '0377456433', '1080003348', '29H 79416', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0309');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0314', '314', 'Trịnh Xuân Hiền', '0986519875', '1070005550', '29H 24460', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0314');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0331', '331', 'Lê Anh Tuấn', '0972683336', '1083007818', '29H 57424', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0331');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0336', '336', 'Chè Văn Hiệp', '0989477582', '20084000041', '29K 05562', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0336');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0348', '348', 'Tống Nguyên Luận', '0976969959', '34080002371', '29H 80353', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0348');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0349', '349', 'Nguyễn Xuân Tiến', '0988007866', '37084012579', '29C 21842', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0349');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0353', '353', 'Nguyễn Duy Diện', '0334135126', '1087030572', '29H 81154', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0353');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0360', '360', 'Đào Văn Đại', '0828922068', '1096002928', '29C 99471', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0360');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0364', '364', 'Trịnh Quang Tạo', '0975157183', '1083011942', '29H 27727', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0364');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0365', '365', 'Trần Đình Nghĩa', '0362048693', '1091027859', '29H 76887', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0365');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0374', '374', 'Lê Xuân Tiệp', '0973717122', '1086003436', '29H 92049', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0374');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0379', '379', 'Nguyễn Văn Khiêm', '0795255173', '27085011620', '29C 12412', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0379');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0386', '386', 'Nguyễn Văn Nhàn', '0377381986', '1087031778', '29F 05985', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0386');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0391', '391', 'Nguyễn Quang Minh', '0985902983', '1083012066', '29H 24486', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0391');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0393', '393', 'Nguyễn Đình Thành', '0932790552', '27084014286', '29H 75944', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0393');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0395', '395', 'Cồ Văn Trình', '0964252711', '36084009971', '29H 88313', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0395');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0408', '408', 'Lưu Văn Thắng', '0987319761', '27077004264', '29C-83340', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0408');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0409', '409', 'Đào Văn Nam', '0968684136', '1082004936', '29E 25831', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0409');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0426', '426', 'Nguyễn Đức Hưng', '0976642273', '27093014680', '29H 88389', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0426');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0328', '328', 'Nguyễn Như Phú', '0974194309', '1089048095', '29E 26577', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0328');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0429', '429', 'Đào Đăng Hải', '0961129302', '1085017794', '29H 88337', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0429');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0445', '445', 'Đỗ Xuân Thời', '0918892818', '1085010769', '29H 88397', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0445');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0446', '446', 'Mai Thanh Tùng', '0944932369', '19093004033', '29H 92126', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0446');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0453', '453', 'Nguyễn Vũ Nam', '0838891091', '1091004626', '29H 75558', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0453');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0362', '362', 'Đỗ Lưu Ánh', '0383366132', '1200034176', '29H 32315', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0362');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0452', '452', 'Phạm Như Mộng Thiên', '0976229120', '1098004036', '29E 26356', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0452');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0462', '462', 'Quách Mạnh Đạt', '0367595162', '1096034044', '29H 76517', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0462');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0464', '464', 'Nguyễn Văn Quảng', '0836599993', '27093011182', '29H 70670', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0464');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0467', '467', 'Nghiêm Văn Mạnh', '0857324999', '27087003425', '29C 25501', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0467');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0469', '469', 'Ngô Đình Dũng', '0383281881', '27202000580', '29H 88371', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0469');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0238', '238', 'Trần Anh Tuấn', '0947100581', '36081009399', '29E 25946', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0238');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0073', '', 'Lã Tiến Sơn', '0985876326', '1084024994', '29H 83591', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0073');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0074', '', 'Trần Việt Chung', '0983119041', '37091005195', '29H 88330', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0074');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0075', '', 'Nguyễn Văn Thịnh', '0972293480', '1095034304', '29H 20261', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0075');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0076', '', 'Vương Đình Văn', '0988174220', '1087052879', '29H 40919', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0076');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0077', '', 'Chu Văn Quyết', '0986380106', '27096001810', '29E 38051', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0077');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0078', '', 'Lưu Thành Hậu', '0987266442', '1086021535', '29H 92117', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0078');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0079', '', 'Bùi Văn Niên', '0372150856', '38089010486', '29H 16607', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0079');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0080', '', 'Đỗ Văn Đạt', '0326284493', '1093010571', '29H 81494', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0080');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0081', '', 'Trần Văn Tạo', '0383433145', '1069004125', '29C 98846', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0081');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0082', '', 'Quách Văn Sơn', '0983553751', '1095011643', '29H 37799', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0082');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0083', '', 'Vũ Đình Tuấn', '0982438992', '24092019005', '29E 26051', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0083');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0084', '', 'Ngô Văn Hiếu', '0866155958', '24092005252', '29H 92180', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0084');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0085', '', 'Lê Minh Vinh', '0386865198', '1080031534', '29K 05976', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0085');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0086', '', 'Phạm Mít Thiên Long', '0399149550', '1094042583', '29K 05633', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0086');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0087', '', 'Hà Văn Sĩ', '0898585638', '24081022489', '29H 99765', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0087');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0088', '', 'Nguyễn Văn Quang', '0328234903', '1203044250', '29C 99732', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0088');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0089', '', 'Nguyễn Văn Thắng', '0986532397', '1093001643', '29H 70191', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0089');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0090', '', 'Phạm Văn Duyệt', '0386863567', '24094012025', '29H 81296', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0090');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0091', '', 'Hoàng Phúc Thọ', '0944298456', '6087004968', '29H 76792', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0091');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0092', '', 'Vũ Văn Đông', '0963165941', '24094004556', '29K 05672', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0092');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0093', '', 'Nguyễn Văn Nam', '0981402822', '27099004653', '99H 02527', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0093');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0094', '', 'Bùi Văn Thơ', '0964082974', '24094017664', '29K 05676', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0094');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0095', '', 'Vũ Văn Đồng', '0984647297', '27097002521', '29K 05950', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0095');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0096', '', 'Nguyễn Tiến Chiển', '0977828132', '27078004487', '29H 20200', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0096');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0097', '', 'Nguyễn Văn Đỏ', '0972545362', '1094033000', '29E-191.17', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0097');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0098', '', 'Vũ Văn Đoan', '0947320526', '1089041794', '29K 05590', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0098');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0099', '', 'Nông Văn Đông', '0374084543', '20094007917', '29C 84294', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0099');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0100', '', 'Vi Văn Kiên', '0377959717', '38090018584', '29H 16167', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0100');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0101', '', 'Đoàn Văn Việt', '0338271101', '24201009398', '29C 91136', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0101');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0102', '', 'Ngô Đức Hoành', '0987236338', '24084011495', '29H 70641', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0102');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0103', '', 'Chu Văn Văn', '0383155198', '20092002901', '29H 75749', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0103');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0104', '', 'Nguyễn Việt Đức', '0986248124', '1097003791', '29H 76514', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0104');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0105', '', 'Lê Văn Chiêm', '0964092105', '38097027433', '29H 72843', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0105');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0106', '', 'Nguyễn Văn Quang', '0839889186', '1098007996', '29H 16885', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0106');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0107', '', 'Nguyễn Văn Thắng', '0332518572', '35094009714', '29H 99618', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0107');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0108', '', 'Nguyễn Tuấn Anh', '0385603831', '1095006343', '29C 65638', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0108');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0109', '', 'Nguyễn Văn Tâm', '0964442995', '1095008118', '29C 98944', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0109');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0110', '', 'Nguyễn Minh Hải', '0862636628', '1097006222', '29K 05626', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0110');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0111', '', 'Nguyễn Hữu Tĩnh', '0904011023', '1083047397', '29E 26074', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0111');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0112', '', 'Hoàng Văn Đức Định', '0961109876', '20089001442', '29H 99543', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0112');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0113', '', 'Nguyễn Văn Nguyên', '0339503444', '1083020701', '29E 33903', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0113');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0114', '', 'Lê Quang Khải', '0348871548', '24072014267', '29H 99734', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0114');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0115', '', 'Nguyễn Văn Hải', '0376664084', '1088025393', '29H 24643', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0115');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0116', '', 'Nguyễn Văn Hoàng', '0986755950', '1087020400', '29E 26076', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0116');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0117', '', 'Đoàn Văn Sơn', '0966683697', '1097022256', '29E 26061', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0117');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0118', '', 'Đỗ Văn Kiên', '0399900991', '1094020941', '29H 81121', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0118');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0119', '', 'Lê Ngọc Anh', '0975298846', '25094015044', '29H 92096', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0119');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0120', '', 'Nguyễn Ngọc Chức', '0337330113', '27097011002', '29H 76783', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0120');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0121', '', 'Lý Văn Bình', '0877455668', '4093000497', '29H 75855', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0121');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0122', '', 'Lê Tùng Sơn', '0865028588', '38098020530', '29E 19523', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0122');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0123', '', 'Đặng Thanh Sơn', '09775873880915016399', '27084001762', '29E 38010', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0123');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0124', '', 'Lê Đình Quang Tiến', '0966406862', '1086029003', '29E 25824', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0124');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0125', '', 'Vũ Văn Sơn', '0987215788', '24088013373', '29C 55178', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0125');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0126', '', 'Nguyễn Văn Đô', '0335527147', '24090014698', '29H 75998', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0126');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0127', '', 'Lưu Văn Thanh', '0982611031', '27200007301', '29H 27224', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0127');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0128', '', 'Nguyễn Tiến Dũng', '0356499583', '1097032531', '29H 70663', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0128');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0129', '', 'Hoàng Văn Quý', '0363086122', '1098003508', '29K 05816', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0129');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0130', '', 'Đỗ Văn Hòa', '0376266228', '1094011543', '29H 70744', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0130');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0131', '', 'Đặng Văn Mão', '0975480444', '42088004148', '29E 19000', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0131');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0132', '', 'Nguyễn Văn Dương', '0985526581', '19083005633', '29E 19056', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0132');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0133', '', 'Nguyễn Thế Hưng', '0987429683', '27083012052', '29E 19370', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0133');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0134', '', 'Nguyễn Văn Thiện', '0326353638', '1096002155', '29K 05596', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0134');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0135', '', 'Tạ Văn Đạo', '0979002934', '24078011393', '29E 38055', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0135');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0136', '', 'Lê Văn Viện', '0961381322', '38091008085', '29H 40756', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0136');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0137', '', 'Trương Đình Dương', '0973399668', '36081013577', '29H 02738', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0137');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0138', '', 'Hoàng Viết Sang', '0388811148', '40091026711', '29E 19591', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0138');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0139', '', 'Nghiêm Văn Quyền', '0961791661', '24200001035', '29H 40829', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0139');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0140', '', 'Đinh Văn Miền', '0989823226', '1084009417', '29H 73008', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0140');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0141', '', 'Nguyễn Ngọc Thành', '0385657882', '1077035259', '29H 75980', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0141');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0142', '', 'Nguyễn Đình Sự', '0985137589', '1087029843', '29K 05909', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0142');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0143', '', 'Dương Văn Hải', '0985338669', '10089050185', '29H-406.14', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0143');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0144', '', 'Nguyễn Văn Hân', '0972881219', '24084007025', '98H 07246', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0144');

INSERT INTO drivers (driver_code, employee_id, full_name, phone, id_card, license_plate, vendor_id, is_active)
SELECT 'TB0145', '', 'Nguyễn Việt Hoàng', '0964639651', '1205028728', '29H 76517.', 
       (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO'), TRUE
WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE driver_code = 'TB0145');

-- PHẦN 4: TẠO DANH SÁCH XE TỪ BKS LÁI XE
-- =============================================================================

INSERT INTO vehicles (license_plate, vendor_id, driver_id, is_active)
SELECT DISTINCT 
    d.license_plate,
    d.vendor_id,
    d.driver_id,
    TRUE
FROM drivers d
WHERE d.license_plate IS NOT NULL 
  AND d.license_plate != ''
  AND d.vendor_id = (SELECT vendor_id FROM vendors WHERE vendor_code = 'TAMBAO')
  AND NOT EXISTS (SELECT 1 FROM vehicles v WHERE v.license_plate = d.license_plate);

-- PHẦN 5: TẠO VIEW ĐỂ XEM DANH SÁCH LÁI XE
-- =============================================================================

CREATE OR REPLACE VIEW v_drivers_tambao AS
SELECT 
    d.driver_id,
    d.driver_code,
    d.employee_id AS "Mã NV",
    d.full_name AS "Họ và tên",
    d.phone AS "SĐT",
    d.id_card AS "CCCD",
    d.license_plate AS "Biển số xe",
    v.company_name AS "Nhà vận chuyển",
    d.is_active AS "Hoạt động"
FROM drivers d
LEFT JOIN vendors v ON d.vendor_id = v.vendor_id
WHERE v.vendor_code = 'TAMBAO'
ORDER BY d.driver_code;

-- PHẦN 6: THỐNG KÊ
-- =============================================================================

SELECT 'Tổng số lái xe Tam Bảo đã import:' as info, COUNT(*) as total 
FROM drivers d 
JOIN vendors v ON d.vendor_id = v.vendor_id 
WHERE v.vendor_code = 'TAMBAO';

SELECT 'Tổng số xe Tam Bảo:' as info, COUNT(*) as total 
FROM vehicles v2 
JOIN vendors v ON v2.vendor_id = v.vendor_id 
WHERE v.vendor_code = 'TAMBAO';
