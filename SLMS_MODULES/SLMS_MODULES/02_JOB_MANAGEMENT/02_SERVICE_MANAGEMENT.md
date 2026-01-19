# 🚛 MODULE 2.2: SERVICE MANAGEMENT

## 📋 Mục lục
1. [Service Types](#1-service-types)
2. [Service Booking](#2-service-booking)
3. [Service Tracking](#3-service-tracking)
4. [Service Rating](#4-service-rating)

---

## 1. Service Types

### 1.1 Service Categories

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         SERVICE CATEGORIES                                       │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 🚚 TRUCKING SERVICES                                                    │   │
│   │                                                                          │   │
│   │  TRK-SHORT    Trucking ngắn (nội vùng < 50km)                          │   │
│   │               • Giao hàng nội thành                                     │   │
│   │               • Vận chuyển giữa các KCN gần                             │   │
│   │               • Pricing: Per trip                                       │   │
│   │                                                                          │   │
│   │  TRK-LONG     Trucking dài (liên tỉnh > 50km)                          │   │
│   │               • Vận chuyển đường dài                                    │   │
│   │               • Hải Phòng, Quảng Ninh, Thanh Hóa...                     │   │
│   │               • Pricing: Per trip (by route)                            │   │
│   │                                                                          │   │
│   │  TRK-CONT     Trucking container                                        │   │
│   │               • Container 20ft, 40ft                                    │   │
│   │               • Port to factory / factory to port                       │   │
│   │               • Pricing: Per container                                  │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 📋 CUSTOMS SERVICES                                                     │   │
│   │                                                                          │   │
│   │  CUS-IMPORT   Khai báo nhập khẩu                                        │   │
│   │               • E-customs declaration                                   │   │
│   │               • Document preparation                                    │   │
│   │               • Pricing: Per declaration                                │   │
│   │                                                                          │   │
│   │  CUS-EXPORT   Khai báo xuất khẩu                                        │   │
│   │               • Export declaration                                      │   │
│   │               • C/O processing                                          │   │
│   │               • Pricing: Per declaration                                │   │
│   │                                                                          │   │
│   │  CUS-TRANSIT  Khai báo quá cảnh                                         │   │
│   │               • Transit declaration                                     │   │
│   │               • Bonded warehouse                                        │   │
│   │               • Pricing: Per declaration                                │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 🏭 WAREHOUSE SERVICES                                                   │   │
│   │                                                                          │   │
│   │  WHS-STORAGE  Lưu kho                                                   │   │
│   │               • Short-term / Long-term storage                          │   │
│   │               • Pricing: Per CBM per day                                │   │
│   │                                                                          │   │
│   │  WHS-HANDLE   Bốc xếp                                                   │   │
│   │               • Loading / Unloading                                     │   │
│   │               • Pricing: Per kg or per unit                             │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 📦 OTHER SERVICES                                                       │   │
│   │                                                                          │   │
│   │  SVC-PACK     Đóng gói                                                  │   │
│   │  SVC-INSURE   Bảo hiểm hàng hóa                                         │   │
│   │  SVC-WAIT     Phí chờ (waiting time)                                    │   │
│   │  SVC-EXTRA    Phí phát sinh khác                                        │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Service Configuration Table

```sql
CREATE TABLE service_configs (
    id              SERIAL PRIMARY KEY,
    service_id      INTEGER REFERENCES services(id),
    
    -- Configuration
    config_key      VARCHAR(50) NOT NULL,
    config_value    TEXT,
    
    -- Validation
    is_required     BOOLEAN DEFAULT FALSE,
    validation_rule TEXT,
    
    -- Status
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sample configurations
INSERT INTO service_configs (service_id, config_key, config_value, is_required) VALUES
-- Trucking configs
(1, 'min_booking_hours', '4', TRUE),
(1, 'max_weight_kg', '1500', TRUE),
(1, 'overtime_rate', '1.5', FALSE),

-- Customs configs  
(4, 'required_docs', '["Invoice", "Packing List", "B/L"]', TRUE),
(4, 'processing_days', '1-3', FALSE);
```

---

## 2. Service Booking

### 2.1 Service Booking Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       SERVICE BOOKING FLOW                                       │
│                                                                                  │
│   ┌──────────────┐                                                              │
│   │   Customer   │                                                              │
│   │   Request    │                                                              │
│   └──────┬───────┘                                                              │
│          │                                                                       │
│          ▼                                                                       │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                    SERVICE SELECTION                                     │  │
│   │                                                                           │  │
│   │  Input:                          Output:                                 │  │
│   │  • Service type                  • Available vendors                     │  │
│   │  • Date/Time                     • Estimated price                       │  │
│   │  • Route/Location                • Service availability                  │  │
│   │  • Cargo details                                                         │  │
│   │                                                                           │  │
│   └──────────────────────────────────┬───────────────────────────────────────┘  │
│                                      │                                          │
│                                      ▼                                          │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                    VENDOR ASSIGNMENT                                     │  │
│   │                                                                           │  │
│   │  Selection criteria:                                                     │  │
│   │  • Price competitiveness                                                 │  │
│   │  • Service quality rating                                                │  │
│   │  • Availability                                                          │  │
│   │  • Historical performance                                                │  │
│   │                                                                           │  │
│   └──────────────────────────────────┬───────────────────────────────────────┘  │
│                                      │                                          │
│                                      ▼                                          │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │                    JOB CREATION                                          │  │
│   │                                                                           │  │
│   │  CREATE job with:                                                        │  │
│   │  • Service reference                                                     │  │
│   │  • Customer details                                                      │  │
│   │  • Vendor assignment                                                     │  │
│   │  • Pricing (cost + revenue)                                             │  │
│   │                                                                           │  │
│   └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Multi-Service Job

```sql
-- A single job can have multiple services
CREATE TABLE job_services (
    id              SERIAL PRIMARY KEY,
    job_id          INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    service_id      INTEGER REFERENCES services(id),
    
    -- Service details
    sequence_order  INTEGER DEFAULT 1,              -- Order of execution
    vendor_id       INTEGER REFERENCES vendors(id),
    
    -- Pricing
    quantity        DECIMAL(10,2) DEFAULT 1,
    unit_cost       DECIMAL(12,2),
    unit_price      DECIMAL(12,2),
    total_cost      DECIMAL(12,2),
    total_price     DECIMAL(12,2),
    
    -- Status
    status          VARCHAR(20) DEFAULT 'PENDING',
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP,
    
    notes           TEXT
);

-- Example: Job with trucking + loading + waiting
/*
Job TRK-2601-0001:
├── Service 1: TRK-SHORT (Trucking) - Tam Bảo - 850,000 VND
├── Service 2: WHS-HANDLE (Loading) - Included
└── Service 3: SVC-WAIT (Waiting 2h) - 200,000 VND
Total: 1,050,000 VND
*/
```

---

## 3. Service Tracking

### 3.1 Service Status Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      SERVICE STATUS FLOW                                         │
│                                                                                  │
│   TRUCKING SERVICE:                                                             │
│   ─────────────────                                                             │
│   PENDING → ASSIGNED → DISPATCHED → PICKED_UP → IN_TRANSIT → DELIVERED         │
│                                                                                  │
│   CUSTOMS SERVICE:                                                              │
│   ────────────────                                                              │
│   PENDING → DOCS_RECEIVED → DECLARED → REVIEWING → CLEARED → RELEASED          │
│                                                                                  │
│   WAREHOUSE SERVICE:                                                            │
│   ──────────────────                                                            │
│   PENDING → RECEIVED → STORED → PICKED → RELEASED                               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Service Events Table

```sql
CREATE TABLE service_events (
    id              SERIAL PRIMARY KEY,
    job_service_id  INTEGER REFERENCES job_services(id) ON DELETE CASCADE,
    
    -- Event
    event_type      VARCHAR(50) NOT NULL,
    event_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Location (for trucking)
    location_name   VARCHAR(200),
    coordinates     POINT,
    
    -- Details
    description     TEXT,
    attachments     TEXT[],                         -- File URLs
    
    -- Source
    reported_by     VARCHAR(50),                    -- DRIVER, SYSTEM, VENDOR
    user_id         INTEGER REFERENCES users(id)
);
```

---

## 4. Service Rating

### 4.1 Rating System

```sql
CREATE TABLE service_ratings (
    id              SERIAL PRIMARY KEY,
    job_id          INTEGER REFERENCES jobs(id),
    job_service_id  INTEGER REFERENCES job_services(id),
    vendor_id       INTEGER REFERENCES vendors(id),
    
    -- Ratings (1-5 scale)
    overall_rating  DECIMAL(2,1) NOT NULL,
    timeliness      DECIMAL(2,1),                   -- Đúng giờ
    quality         DECIMAL(2,1),                   -- Chất lượng dịch vụ
    communication   DECIMAL(2,1),                   -- Giao tiếp
    
    -- Feedback
    comments        TEXT,
    
    -- Meta
    rated_by        INTEGER REFERENCES users(id),
    rated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Update vendor rating on new rating
CREATE OR REPLACE FUNCTION update_vendor_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE vendors SET
        rating_score = (
            SELECT AVG(overall_rating)
            FROM service_ratings
            WHERE vendor_id = NEW.vendor_id
        ),
        total_jobs = (
            SELECT COUNT(DISTINCT job_id)
            FROM service_ratings
            WHERE vendor_id = NEW.vendor_id
        )
    WHERE id = NEW.vendor_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_vendor_rating
AFTER INSERT ON service_ratings
FOR EACH ROW EXECUTE FUNCTION update_vendor_rating();
```

---

## 📊 SUMMARY

### Service Categories
1. **Trucking** - Short haul, Long haul, Container
2. **Customs** - Import, Export, Transit
3. **Warehouse** - Storage, Handling
4. **Other** - Packing, Insurance, Waiting

### Key Features
- Multi-service per job support
- Service-specific status tracking
- Vendor rating system
- Flexible pricing (per trip, per kg, per day)

### Integration Points
- **Module 2.1**: Jobs contain services
- **Module 3**: Service pricing feeds into statements
- **Module 4**: AI can recommend services
