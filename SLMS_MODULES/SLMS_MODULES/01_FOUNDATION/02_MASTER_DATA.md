# 📦 MODULE 1.2: MASTER DATA

## 📋 Mục lục
1. [Customers](#1-customers-khách-hàng)
2. [Vendors](#2-vendors-nhà-cung-cấp)
3. [Drivers](#3-drivers-lái-xe)
4. [Vehicles](#4-vehicles-phương-tiện)
5. [Routes](#5-routes-tuyến-đường)
6. [Services](#6-services-dịch-vụ)
7. [Rates](#7-rates-bảng-giá)

---

## 1. Customers (Khách hàng)

### 1.1 Customer Table Schema

```sql
CREATE TABLE customers (
    id              SERIAL PRIMARY KEY,
    customer_code   VARCHAR(20) UNIQUE NOT NULL,    -- VD: DRT1, DRT2, SEVT, KKF
    customer_name   VARCHAR(200) NOT NULL,
    short_name      VARCHAR(50),                    -- Tên viết tắt: DREAMTECH, HOSIDEN
    
    -- Contact Info
    address         TEXT,
    tax_code        VARCHAR(20),
    contact_name    VARCHAR(100),
    contact_phone   VARCHAR(20),
    contact_email   VARCHAR(100),
    
    -- Business Info
    customer_type   VARCHAR(20) DEFAULT 'REGULAR',  -- REGULAR, VIP, CONTRACT
    industry        VARCHAR(50),                    -- ELECTRONICS, TEXTILE, etc.
    payment_terms   INTEGER DEFAULT 30,             -- Số ngày công nợ
    credit_limit    DECIMAL(15,2),
    
    -- Zalo Integration
    zalo_room_name  VARCHAR(100),                   -- Tên room Zalo
    zalo_room_type  VARCHAR(20),                    -- SINGLE, GROUP
    
    -- Status
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by      INTEGER REFERENCES users(id),
    notes           TEXT
);

-- Customer contacts (multiple contacts per customer)
CREATE TABLE customer_contacts (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    contact_name    VARCHAR(100) NOT NULL,
    position        VARCHAR(50),                    -- Logistics Manager, etc.
    phone           VARCHAR(20),
    email           VARCHAR(100),
    is_primary      BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE
);

-- Customer addresses (multiple pickup/delivery locations)
CREATE TABLE customer_addresses (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    address_type    VARCHAR(20) NOT NULL,           -- PICKUP, DELIVERY, BILLING
    address_name    VARCHAR(100),                   -- Factory 1, Warehouse A
    address         TEXT NOT NULL,
    district        VARCHAR(50),
    city            VARCHAR(50),
    coordinates     POINT,                          -- GPS coordinates
    contact_name    VARCHAR(100),
    contact_phone   VARCHAR(20),
    is_default      BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE
);

-- Indexes
CREATE INDEX idx_customer_code ON customers(customer_code);
CREATE INDEX idx_customer_type ON customers(customer_type);
CREATE INDEX idx_customer_active ON customers(is_active);
```

### 1.2 Sample Customer Data

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CUSTOMER EXAMPLES                                      │
│                                                                                  │
│  Code    │ Name                         │ Short    │ Type     │ Payment         │
│  ────────┼──────────────────────────────┼──────────┼──────────┼─────────        │
│  DRT1    │ DREAMTECH VIETNAM - Factory 1│ DRT-MK   │ VIP      │ 30 days         │
│  DRT2    │ DREAMTECH VIETNAM - Factory 2│ DRT-QN   │ VIP      │ 30 days         │
│  SEVT    │ SAMSUNG ELECTRO-MECHANICS VN │ SAMSUNG  │ CONTRACT │ 45 days         │
│  HSDN    │ HOSIDEN VIETNAM CO., LTD     │ HOSIDEN  │ REGULAR  │ 30 days         │
│  KKF     │ K+K FASHION CO., LTD         │ KKF      │ REGULAR  │ 15 days         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Vendors (Nhà cung cấp)

### 2.1 Vendor Table Schema

```sql
CREATE TABLE vendors (
    id              SERIAL PRIMARY KEY,
    vendor_code     VARCHAR(20) UNIQUE NOT NULL,    -- VD: TB, VT, NB
    vendor_name     VARCHAR(200) NOT NULL,
    short_name      VARCHAR(50),                    -- Tam Bảo, Việt Thắng
    
    -- Contact Info
    address         TEXT,
    tax_code        VARCHAR(20),
    contact_name    VARCHAR(100),
    contact_phone   VARCHAR(20),
    contact_email   VARCHAR(100),
    
    -- Banking Info
    bank_account    VARCHAR(50),
    bank_name       VARCHAR(100),
    bank_branch     VARCHAR(100),
    
    -- Business Info
    vendor_type     VARCHAR(20) DEFAULT 'TRUCKING', -- TRUCKING, CUSTOMS, WAREHOUSE
    service_areas   TEXT[],                         -- ['HN', 'HP', 'QN', 'BN']
    vehicle_types   TEXT[],                         -- ['1.25T', '2.5T', '5T', '15T']
    payment_terms   INTEGER DEFAULT 15,
    
    -- Zalo Integration
    zalo_room_name  VARCHAR(100),
    
    -- Rating
    rating_score    DECIMAL(3,2) DEFAULT 5.00,      -- 1.00 - 5.00
    total_jobs      INTEGER DEFAULT 0,
    on_time_rate    DECIMAL(5,2) DEFAULT 100.00,    -- Percentage
    
    -- Status
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes           TEXT
);

-- Indexes
CREATE INDEX idx_vendor_code ON vendors(vendor_code);
CREATE INDEX idx_vendor_type ON vendors(vendor_type);
CREATE INDEX idx_vendor_active ON vendors(is_active);
```

### 2.2 Sample Vendor Data

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            VENDOR EXAMPLES                                       │
│                                                                                  │
│  Code │ Name                    │ Type     │ Areas       │ Vehicles             │
│  ─────┼─────────────────────────┼──────────┼─────────────┼──────────────────    │
│  TB   │ VẬN TẢI TAM BẢO        │ TRUCKING │ HN,HP,QN,BN │ 1.25T,2.5T,5T,15T   │
│  VT   │ VIỆT THẮNG LOGISTICS   │ TRUCKING │ HN,HP       │ 1.25T,2.5T,5T       │
│  NB   │ NAM BÌNH EXPRESS       │ TRUCKING │ HN,BN,HY    │ 2.5T,5T,10T         │
│  HQ   │ HAI QUAN MINH KHANG    │ CUSTOMS  │ ALL         │ -                    │
│  KV   │ KHO VẬN MIỀN BẮC      │ WAREHOUSE│ HN          │ -                    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Drivers (Lái xe)

### 3.1 Driver Table Schema

```sql
CREATE TABLE drivers (
    id              SERIAL PRIMARY KEY,
    driver_code     VARCHAR(20) UNIQUE NOT NULL,    -- VD: DRV001, DRV002
    driver_name     VARCHAR(100) NOT NULL,
    
    -- Contact
    phone           VARCHAR(20) NOT NULL,
    phone_2         VARCHAR(20),
    
    -- Identity
    id_card         VARCHAR(20),                    -- CCCD/CMND
    id_card_date    DATE,
    id_card_place   VARCHAR(100),
    date_of_birth   DATE,
    
    -- License
    license_number  VARCHAR(20),
    license_class   VARCHAR(10),                    -- B2, C, D, E
    license_expiry  DATE,
    
    -- Association
    vendor_id       INTEGER REFERENCES vendors(id), -- Thuộc vendor nào
    vehicle_id      INTEGER REFERENCES vehicles(id),-- Xe thường lái
    
    -- Rating
    rating_score    DECIMAL(3,2) DEFAULT 5.00,
    total_trips     INTEGER DEFAULT 0,
    
    -- Status
    status          VARCHAR(20) DEFAULT 'AVAILABLE',-- AVAILABLE, ON_TRIP, OFF_DUTY
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes           TEXT
);

-- Indexes
CREATE INDEX idx_driver_vendor ON drivers(vendor_id);
CREATE INDEX idx_driver_status ON drivers(status);
CREATE INDEX idx_driver_phone ON drivers(phone);
```

### 3.2 Driver Status Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         DRIVER STATUS FLOW                                       │
│                                                                                  │
│           ┌───────────┐                                                         │
│           │ AVAILABLE │◄─────────────────────────────────┐                      │
│           └─────┬─────┘                                   │                      │
│                 │ Assign to job                           │ Complete trip        │
│                 ▼                                         │                      │
│           ┌───────────┐                             ┌─────┴─────┐               │
│           │  ON_TRIP  │────────────────────────────►│ AVAILABLE │               │
│           └───────────┘                             └───────────┘               │
│                 │                                                                │
│                 │ End of day / Personal                                         │
│                 ▼                                                                │
│           ┌───────────┐                                                         │
│           │ OFF_DUTY  │                                                         │
│           └───────────┘                                                         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Vehicles (Phương tiện)

### 4.1 Vehicle Table Schema

```sql
CREATE TABLE vehicles (
    id              SERIAL PRIMARY KEY,
    vehicle_code    VARCHAR(20) UNIQUE NOT NULL,
    license_plate   VARCHAR(20) UNIQUE NOT NULL,    -- BKS: 29H 76514
    
    -- Specs
    vehicle_type    VARCHAR(20) NOT NULL,           -- 1.25T, 2.5T, 5T, 10T, 15T, CONT20, CONT40
    brand           VARCHAR(50),                    -- HYUNDAI, ISUZU, HINO
    model           VARCHAR(50),
    year            INTEGER,
    
    -- Capacity
    payload_kg      INTEGER,                        -- Tải trọng (kg)
    volume_m3       DECIMAL(5,2),                   -- Thể tích (m³)
    length_m        DECIMAL(4,2),                   -- Chiều dài thùng (m)
    width_m         DECIMAL(4,2),
    height_m        DECIMAL(4,2),
    
    -- Association
    vendor_id       INTEGER REFERENCES vendors(id),
    default_driver_id INTEGER REFERENCES drivers(id),
    
    -- Documents
    registration_expiry DATE,
    inspection_expiry   DATE,
    insurance_expiry    DATE,
    
    -- Status
    status          VARCHAR(20) DEFAULT 'AVAILABLE',-- AVAILABLE, ON_TRIP, MAINTENANCE
    current_location POINT,
    last_location_update TIMESTAMP,
    
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes           TEXT
);

-- Indexes
CREATE INDEX idx_vehicle_vendor ON vehicles(vendor_id);
CREATE INDEX idx_vehicle_type ON vehicles(vehicle_type);
CREATE INDEX idx_vehicle_status ON vehicles(status);
CREATE INDEX idx_vehicle_plate ON vehicles(license_plate);
```

### 4.2 Vehicle Types

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          VEHICLE TYPES                                           │
│                                                                                  │
│  Type    │ Payload   │ Volume  │ Length  │ Common Use                           │
│  ────────┼───────────┼─────────┼─────────┼──────────────────────────────        │
│  1.25T   │ 1,250 kg  │ 8 m³    │ 3.2m    │ Small shipments, city delivery       │
│  2.5T    │ 2,500 kg  │ 15 m³   │ 4.2m    │ Medium shipments                     │
│  5T      │ 5,000 kg  │ 25 m³   │ 5.2m    │ Large shipments, pallets             │
│  10T     │ 10,000 kg │ 45 m³   │ 7.0m    │ Heavy cargo, long haul               │
│  15T     │ 15,000 kg │ 60 m³   │ 9.0m    │ Full truck load                      │
│  CONT20  │ 21,000 kg │ 33 m³   │ 6.0m    │ 20ft container                       │
│  CONT40  │ 26,000 kg │ 67 m³   │ 12.0m   │ 40ft container                       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Routes (Tuyến đường)

### 5.1 Route Table Schema

```sql
CREATE TABLE routes (
    id              SERIAL PRIMARY KEY,
    route_code      VARCHAR(50) UNIQUE NOT NULL,    -- VD: MK-HN, MK-HP, MK-BN
    route_name      VARCHAR(200),
    
    -- Origin
    origin_code     VARCHAR(20) NOT NULL,           -- MK (Mê Linh)
    origin_name     VARCHAR(100),
    origin_address  TEXT,
    origin_coords   POINT,
    
    -- Destination
    dest_code       VARCHAR(20) NOT NULL,           -- HN (Hà Nội)
    dest_name       VARCHAR(100),
    dest_address    TEXT,
    dest_coords     POINT,
    
    -- Distance & Time
    distance_km     DECIMAL(6,1),
    est_duration_min INTEGER,                       -- Estimated duration
    
    -- Pricing zone
    zone            VARCHAR(20),                    -- ZONE_A, ZONE_B, ZONE_C
    
    -- Status
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes           TEXT
);

-- Common routes
INSERT INTO routes (route_code, origin_code, origin_name, dest_code, dest_name, distance_km, est_duration_min, zone) VALUES
('MK-HN', 'MK', 'KCN Quang Minh', 'HN', 'Nội thành Hà Nội', 25, 60, 'ZONE_A'),
('MK-HP', 'MK', 'KCN Quang Minh', 'HP', 'Hải Phòng', 120, 180, 'ZONE_B'),
('MK-BN', 'MK', 'KCN Quang Minh', 'BN', 'Bắc Ninh', 30, 45, 'ZONE_A'),
('MK-QN', 'MK', 'KCN Quang Minh', 'QN', 'Quảng Ninh', 150, 210, 'ZONE_C'),
('MK-HY', 'MK', 'KCN Quang Minh', 'HY', 'Hưng Yên', 45, 75, 'ZONE_A');
```

### 5.2 Route Zones

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ROUTE ZONES                                            │
│                                                                                  │
│   Zone    │ Distance      │ Examples                    │ Price Multiplier      │
│   ────────┼───────────────┼─────────────────────────────┼──────────────────     │
│   ZONE_A  │ 0 - 50 km     │ HN, BN, HY                  │ 1.0x (Base)           │
│   ZONE_B  │ 50 - 150 km   │ HP, HD, TB                  │ 1.5x                  │
│   ZONE_C  │ 150 - 300 km  │ QN, TH, NA                  │ 2.0x                  │
│   ZONE_D  │ > 300 km      │ ĐN, SG, Miền Trung          │ Quote required        │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Services (Dịch vụ)

### 6.1 Service Table Schema

```sql
CREATE TABLE services (
    id              SERIAL PRIMARY KEY,
    service_code    VARCHAR(20) UNIQUE NOT NULL,
    service_name    VARCHAR(100) NOT NULL,
    
    -- Category
    category        VARCHAR(20) NOT NULL,           -- TRUCKING, CUSTOMS, WAREHOUSE, OTHER
    sub_category    VARCHAR(50),
    
    -- Pricing
    pricing_type    VARCHAR(20) DEFAULT 'FIXED',    -- FIXED, PER_UNIT, PER_KG, PER_CBM
    default_price   DECIMAL(12,2),
    unit            VARCHAR(20),                    -- TRIP, CONT, KG, CBM, DECLARATION
    
    -- Status
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description     TEXT
);

-- Sample services
INSERT INTO services (service_code, service_name, category, pricing_type, default_price, unit) VALUES
-- Trucking
('TRK-SHORT', 'Trucking ngắn (nội vùng)', 'TRUCKING', 'PER_TRIP', NULL, 'TRIP'),
('TRK-LONG', 'Trucking dài (liên tỉnh)', 'TRUCKING', 'PER_TRIP', NULL, 'TRIP'),
('TRK-CONT', 'Trucking container', 'TRUCKING', 'PER_CONT', NULL, 'CONT'),

-- Customs
('CD-IMPORT', 'Khai báo nhập khẩu', 'CUSTOMS', 'PER_DECL', 500000, 'DECLARATION'),
('CD-EXPORT', 'Khai báo xuất khẩu', 'CUSTOMS', 'PER_DECL', 400000, 'DECLARATION'),
('CD-TRANSIT', 'Khai báo quá cảnh', 'CUSTOMS', 'PER_DECL', 350000, 'DECLARATION'),

-- Warehouse
('WH-STORAGE', 'Lưu kho', 'WAREHOUSE', 'PER_CBM_DAY', 5000, 'CBM/DAY'),
('WH-HANDLING', 'Bốc xếp', 'WAREHOUSE', 'PER_KG', 500, 'KG'),

-- Other
('SVC-PACKING', 'Đóng gói hàng', 'OTHER', 'PER_UNIT', 10000, 'UNIT'),
('SVC-INSURANCE', 'Bảo hiểm hàng hóa', 'OTHER', 'PERCENTAGE', 0.15, 'PERCENT');
```

---

## 7. Rates (Bảng giá)

### 7.1 Rate Table Schema

```sql
-- Vendor rates (Giá mua)
CREATE TABLE vendor_rates (
    id              SERIAL PRIMARY KEY,
    vendor_id       INTEGER REFERENCES vendors(id) NOT NULL,
    
    -- Rate Key
    service_id      INTEGER REFERENCES services(id),
    route_id        INTEGER REFERENCES routes(id),
    vehicle_type    VARCHAR(20),
    
    -- Pricing
    price           DECIMAL(12,2) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'VND',
    unit            VARCHAR(20) DEFAULT 'TRIP',
    
    -- Validity
    effective_date  DATE NOT NULL,
    expiry_date     DATE,
    
    -- Conditions
    min_weight      DECIMAL(10,2),
    max_weight      DECIMAL(10,2),
    conditions      TEXT,
    
    -- Status
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by      INTEGER REFERENCES users(id),
    notes           TEXT,
    
    -- Unique constraint
    UNIQUE (vendor_id, service_id, route_id, vehicle_type, effective_date)
);

-- Customer rates (Giá bán)
CREATE TABLE customer_rates (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER REFERENCES customers(id) NOT NULL,
    
    -- Rate Key
    service_id      INTEGER REFERENCES services(id),
    route_id        INTEGER REFERENCES routes(id),
    vehicle_type    VARCHAR(20),
    
    -- Pricing
    price           DECIMAL(12,2) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'VND',
    unit            VARCHAR(20) DEFAULT 'TRIP',
    
    -- Reference to vendor rate for margin calculation
    vendor_rate_id  INTEGER REFERENCES vendor_rates(id),
    margin_percent  DECIMAL(5,2),                   -- Calculated margin
    
    -- Validity
    effective_date  DATE NOT NULL,
    expiry_date     DATE,
    
    -- Contract reference
    contract_number VARCHAR(50),
    
    -- Status
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by      INTEGER REFERENCES users(id),
    notes           TEXT,
    
    UNIQUE (customer_id, service_id, route_id, vehicle_type, effective_date)
);

-- Indexes
CREATE INDEX idx_vendor_rate_vendor ON vendor_rates(vendor_id);
CREATE INDEX idx_vendor_rate_route ON vendor_rates(route_id);
CREATE INDEX idx_vendor_rate_effective ON vendor_rates(effective_date);

CREATE INDEX idx_customer_rate_customer ON customer_rates(customer_id);
CREATE INDEX idx_customer_rate_route ON customer_rates(route_id);
CREATE INDEX idx_customer_rate_effective ON customer_rates(effective_date);
```

### 7.2 Rate Lookup Function

```sql
-- Function to get applicable rate
CREATE OR REPLACE FUNCTION get_vendor_rate(
    p_vendor_id INTEGER,
    p_route_id INTEGER,
    p_vehicle_type VARCHAR,
    p_date DATE DEFAULT CURRENT_DATE
) RETURNS DECIMAL AS $$
DECLARE
    v_price DECIMAL;
BEGIN
    SELECT price INTO v_price
    FROM vendor_rates
    WHERE vendor_id = p_vendor_id
      AND route_id = p_route_id
      AND vehicle_type = p_vehicle_type
      AND effective_date <= p_date
      AND (expiry_date IS NULL OR expiry_date >= p_date)
      AND is_active = TRUE
    ORDER BY effective_date DESC
    LIMIT 1;
    
    RETURN v_price;
END;
$$ LANGUAGE plpgsql;
```

### 7.3 Sample Rate Data

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      VENDOR RATES (Tam Bảo)                                      │
│                                                                                  │
│  Route    │ Vehicle │ Price (VND)  │ Effective   │ Notes                        │
│  ─────────┼─────────┼──────────────┼─────────────┼───────────────────────       │
│  MK-HN    │ 1.25T   │ 850,000      │ 2025-01-01  │ Standard rate                │
│  MK-HN    │ 2.5T    │ 1,200,000    │ 2025-01-01  │ Standard rate                │
│  MK-HN    │ 5T      │ 1,800,000    │ 2025-01-01  │ Standard rate                │
│  MK-HP    │ 1.25T   │ 2,500,000    │ 2025-01-01  │ Long haul                    │
│  MK-HP    │ 2.5T    │ 3,200,000    │ 2025-01-01  │ Long haul                    │
│  MK-BN    │ 1.25T   │ 700,000      │ 2025-01-01  │ Short distance               │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                      CUSTOMER RATES (DREAMTECH)                                  │
│                                                                                  │
│  Route    │ Vehicle │ Price (VND)  │ Cost        │ Margin                       │
│  ─────────┼─────────┼──────────────┼─────────────┼───────────────────────       │
│  MK-HN    │ 1.25T   │ 1,030,000    │ 850,000     │ 21.2%                        │
│  MK-HN    │ 2.5T    │ 1,450,000    │ 1,200,000   │ 20.8%                        │
│  MK-HN    │ 5T      │ 2,200,000    │ 1,800,000   │ 22.2%                        │
│  MK-HP    │ 1.25T   │ 3,000,000    │ 2,500,000   │ 20.0%                        │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 ENTITY RELATIONSHIP DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         MASTER DATA RELATIONSHIPS                                │
│                                                                                  │
│   ┌──────────┐         ┌──────────┐         ┌──────────┐                        │
│   │ CUSTOMERS│◄────────│  RATES   │────────►│ VENDORS  │                        │
│   └────┬─────┘         └────┬─────┘         └────┬─────┘                        │
│        │                    │                    │                               │
│        │                    │                    │                               │
│   ┌────┴─────┐         ┌────┴─────┐         ┌────┴─────┐                        │
│   │ ADDRESSES│         │ SERVICES │         │ DRIVERS  │                        │
│   └──────────┘         └──────────┘         └────┬─────┘                        │
│                                                   │                              │
│   ┌──────────┐         ┌──────────┐         ┌────┴─────┐                        │
│   │ CONTACTS │         │  ROUTES  │         │ VEHICLES │                        │
│   └──────────┘         └──────────┘         └──────────┘                        │
│                                                                                  │
│   All entities → JOBS (Module 2)                                                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 SUMMARY

### Tables in this module
1. `customers` + `customer_contacts` + `customer_addresses`
2. `vendors`
3. `drivers`
4. `vehicles`
5. `routes`
6. `services`
7. `vendor_rates` + `customer_rates`

### Key Features
- Multi-contact and multi-address support for customers
- Vendor rating system
- Driver and vehicle tracking
- Flexible pricing by route, vehicle type, and time
- Margin calculation between buy/sell rates

### Integration Points
- **Module 2**: Jobs reference all master data
- **Module 3**: Rates used for statements and billing
- **Module 4**: AI extracts entities to match master data
