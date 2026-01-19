# 🚚 MODULE 2.1: JOB LIFECYCLE

## 📋 Mục lục
1. [Job Overview](#1-job-overview)
2. [Job Creation](#2-job-creation)
3. [Job Assignment](#3-job-assignment)
4. [Job Execution](#4-job-execution)
5. [Job Completion](#5-job-completion)

---

## 1. Job Overview

### 1.1 Job Table Schema

```sql
CREATE TABLE jobs (
    id              SERIAL PRIMARY KEY,
    job_number      VARCHAR(20) UNIQUE NOT NULL,    -- TRK-2601-0001
    
    -- Job Type
    job_type        VARCHAR(20) NOT NULL,           -- TRUCKING_SHORT, TRUCKING_LONG, CUSTOMS
    service_id      INTEGER REFERENCES services(id),
    
    -- Customer Info
    customer_id     INTEGER REFERENCES customers(id) NOT NULL,
    customer_code   VARCHAR(20),
    customer_ref    VARCHAR(100),                   -- Customer's reference number
    
    -- Booking Info
    booking_date    DATE NOT NULL,
    pickup_time     TIME,
    delivery_date   DATE,
    delivery_time   TIME,
    
    -- Route
    route_id        INTEGER REFERENCES routes(id),
    pickup_address  TEXT,
    delivery_address TEXT,
    
    -- Cargo Info
    cargo_type      VARCHAR(50),                    -- PCB, TEXTILE, GENERAL
    invoice_numbers TEXT,                           -- Multiple invoices
    package_info    TEXT,                           -- "8 box", "5 pallets"
    weight_kg       DECIMAL(10,2),
    volume_cbm      DECIMAL(10,2),
    cargo_value     DECIMAL(15,2),
    special_requirements TEXT,
    
    -- Assignment
    vendor_id       INTEGER REFERENCES vendors(id),
    vehicle_id      INTEGER REFERENCES vehicles(id),
    driver_id       INTEGER REFERENCES drivers(id),
    vehicle_type    VARCHAR(20),
    license_plate   VARCHAR(20),
    driver_name     VARCHAR(100),
    driver_phone    VARCHAR(20),
    
    -- Status
    status          VARCHAR(20) DEFAULT 'DRAFT',
    -- DRAFT → PENDING → CONFIRMED → DISPATCHED → IN_TRANSIT → DELIVERED → COMPLETED → CANCELLED
    
    -- Timestamps
    confirmed_at    TIMESTAMP,
    dispatched_at   TIMESTAMP,
    picked_up_at    TIMESTAMP,
    delivered_at    TIMESTAMP,
    completed_at    TIMESTAMP,
    cancelled_at    TIMESTAMP,
    cancel_reason   TEXT,
    
    -- Financials
    cost_amount     DECIMAL(12,2),                  -- Giá mua
    revenue_amount  DECIMAL(12,2),                  -- Giá bán
    profit_amount   DECIMAL(12,2),                  -- Lợi nhuận
    currency        VARCHAR(3) DEFAULT 'VND',
    
    -- Billing Status
    billing_status  VARCHAR(20) DEFAULT 'UNBILLED',
    -- UNBILLED → IN_STATEMENT → INVOICED → PAID
    customer_statement_id INTEGER,
    vendor_statement_id INTEGER,
    
    -- Meta
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by      INTEGER REFERENCES users(id),
    notes           TEXT,
    
    -- AI Processing
    ai_source       VARCHAR(50),                    -- ZALO, EMAIL, MANUAL
    ai_confidence   DECIMAL(3,2),                   -- 0.00 - 1.00
    raw_message     TEXT                            -- Original message for reference
);

-- Job Items (Chi tiết dịch vụ trong job)
CREATE TABLE job_items (
    id              SERIAL PRIMARY KEY,
    job_id          INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    
    -- Item details
    item_type       VARCHAR(20),                    -- TRANSPORT, LOADING, WAITING
    description     TEXT,
    quantity        DECIMAL(10,2) DEFAULT 1,
    unit            VARCHAR(20),
    
    -- Pricing
    unit_cost       DECIMAL(12,2),
    unit_price      DECIMAL(12,2),
    total_cost      DECIMAL(12,2),
    total_price     DECIMAL(12,2),
    
    -- Status
    is_billable     BOOLEAN DEFAULT TRUE,
    notes           TEXT
);

-- Job Status History
CREATE TABLE job_status_history (
    id              SERIAL PRIMARY KEY,
    job_id          INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    from_status     VARCHAR(20),
    to_status       VARCHAR(20) NOT NULL,
    changed_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by      INTEGER REFERENCES users(id),
    reason          TEXT,
    notes           TEXT
);

-- Indexes
CREATE INDEX idx_job_number ON jobs(job_number);
CREATE INDEX idx_job_customer ON jobs(customer_id);
CREATE INDEX idx_job_vendor ON jobs(vendor_id);
CREATE INDEX idx_job_status ON jobs(status);
CREATE INDEX idx_job_date ON jobs(booking_date);
CREATE INDEX idx_job_billing ON jobs(billing_status);
```

### 1.2 Job Number Format

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         JOB NUMBER FORMAT                                        │
│                                                                                  │
│   Format: {TYPE}-{YYMM}-{SEQUENCE}                                              │
│                                                                                  │
│   Examples:                                                                      │
│   ├── TRK-2601-0001  →  Trucking job, Jan 2026, sequence 1                     │
│   ├── TRK-2601-0002  →  Trucking job, Jan 2026, sequence 2                     │
│   ├── CUS-2601-0001  →  Customs job, Jan 2026, sequence 1                      │
│   └── SVC-2601-0001  →  Service job, Jan 2026, sequence 1                      │
│                                                                                  │
│   Type Prefixes:                                                                 │
│   ├── TRK  = Trucking (short & long haul)                                       │
│   ├── CUS  = Customs declaration                                                │
│   ├── WHS  = Warehouse services                                                 │
│   └── SVC  = Other services                                                     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Job Number Generation Function

```sql
CREATE OR REPLACE FUNCTION generate_job_number(p_type VARCHAR)
RETURNS VARCHAR AS $$
DECLARE
    v_prefix VARCHAR(3);
    v_yymm VARCHAR(4);
    v_seq INTEGER;
    v_job_number VARCHAR(20);
BEGIN
    -- Set prefix based on type
    v_prefix := CASE p_type
        WHEN 'TRUCKING_SHORT' THEN 'TRK'
        WHEN 'TRUCKING_LONG' THEN 'TRK'
        WHEN 'CUSTOMS' THEN 'CUS'
        WHEN 'WAREHOUSE' THEN 'WHS'
        ELSE 'SVC'
    END;
    
    -- Get YYMM
    v_yymm := TO_CHAR(CURRENT_DATE, 'YYMM');
    
    -- Get next sequence
    SELECT COALESCE(MAX(
        CAST(SPLIT_PART(job_number, '-', 3) AS INTEGER)
    ), 0) + 1 INTO v_seq
    FROM jobs
    WHERE job_number LIKE v_prefix || '-' || v_yymm || '-%';
    
    -- Format job number
    v_job_number := v_prefix || '-' || v_yymm || '-' || LPAD(v_seq::TEXT, 4, '0');
    
    RETURN v_job_number;
END;
$$ LANGUAGE plpgsql;
```

---

## 2. Job Creation

### 2.1 Job Status Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          JOB STATUS FLOW                                         │
│                                                                                  │
│   ┌───────┐     ┌─────────┐     ┌───────────┐     ┌────────────┐               │
│   │ DRAFT │────►│ PENDING │────►│ CONFIRMED │────►│ DISPATCHED │               │
│   └───────┘     └─────────┘     └───────────┘     └─────┬──────┘               │
│       │              │               │                   │                       │
│       │              │               │                   ▼                       │
│       │              │               │           ┌────────────┐                  │
│       │              │               │           │ IN_TRANSIT │                  │
│       │              │               │           └─────┬──────┘                  │
│       │              │               │                 │                         │
│       │              │               │                 ▼                         │
│       │              │               │           ┌───────────┐                   │
│       │              │               │           │ DELIVERED │                   │
│       │              │               │           └─────┬─────┘                   │
│       │              │               │                 │                         │
│       │              │               │                 ▼                         │
│       │              │               │           ┌───────────┐                   │
│       │              │               │           │ COMPLETED │                   │
│       │              │               │           └───────────┘                   │
│       │              │               │                                           │
│       └──────────────┴───────────────┴─────────► ┌───────────┐                  │
│                    (Can cancel at any stage)     │ CANCELLED │                  │
│                                                  └───────────┘                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Job Creation Sources

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        JOB CREATION SOURCES                                      │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 1. MANUAL ENTRY (NocoDB / AppSheet)                                     │   │
│   │    - User fills form directly                                           │   │
│   │    - Full control over all fields                                       │   │
│   │    - Status: DRAFT                                                      │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 2. EXCEL FILE (AI Parsed)                                               │   │
│   │    - Customer sends booking form via Zalo/Email                         │   │
│   │    - AI extracts: customer, date, time, cargo, addresses                │   │
│   │    - Status: PENDING (needs confirmation)                               │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 3. ZALO MESSAGE (AI Parsed)                                             │   │
│   │    - Direct text message with booking details                           │   │
│   │    - AI extracts structured data                                        │   │
│   │    - Status: PENDING (needs confirmation)                               │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 4. API INTEGRATION                                                      │   │
│   │    - Direct API call from customer's system                             │   │
│   │    - Structured data, no parsing needed                                 │   │
│   │    - Status: CONFIRMED (if authorized)                                  │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Create Job API

```python
# FastAPI endpoint for job creation
@router.post("/jobs", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Generate job number
    job_number = generate_job_number(job_data.job_type)
    
    # Create job
    job = Job(
        job_number=job_number,
        job_type=job_data.job_type,
        customer_id=job_data.customer_id,
        booking_date=job_data.booking_date,
        pickup_time=job_data.pickup_time,
        route_id=job_data.route_id,
        cargo_type=job_data.cargo_type,
        invoice_numbers=job_data.invoice_numbers,
        package_info=job_data.package_info,
        status='DRAFT' if job_data.source == 'MANUAL' else 'PENDING',
        ai_source=job_data.source,
        created_by=current_user.id
    )
    
    db.add(job)
    db.commit()
    
    # Log status change
    log_status_change(db, job.id, None, job.status, current_user.id)
    
    return job
```

---

## 3. Job Assignment

### 3.1 Assignment Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         JOB ASSIGNMENT FLOW                                      │
│                                                                                  │
│   ┌─────────────────┐                                                           │
│   │  PENDING JOB    │                                                           │
│   │  (Unassigned)   │                                                           │
│   └────────┬────────┘                                                           │
│            │                                                                     │
│            ▼                                                                     │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                    SEND TO VENDOR                                       │   │
│   │                                                                          │   │
│   │  📤 Zalo Message to Tam Bảo:                                            │   │
│   │  ────────────────────────────                                           │   │
│   │  🚛 YÊU CẦU XE - DRT1                                                   │   │
│   │  📅 Ngày: 15/01/2026                                                    │   │
│   │  ⏰ Giờ: 22:00                                                          │   │
│   │  📦 Invoice: 260115DRT-001, 260115DRTV-02                              │   │
│   │  📋 Hàng: PCB - 8 box                                                   │   │
│   │  🚗 Loại xe: 1.25T                                                      │   │
│   │  📍 Giao: DREAMTECH VIETNAM - Quang Minh                               │   │
│   │                                                                          │   │
│   │  Vui lòng điều xe và phản hồi thông tin lái xe.                        │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                     │
│            ▼                                                                     │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                    VENDOR RESPONSE                                      │   │
│   │                                                                          │   │
│   │  📥 Zalo Message from Tam Bảo:                                          │   │
│   │  ─────────────────────────────                                          │   │
│   │  BKS: 29H 76514                                                         │   │
│   │  Lái xe: Nguyễn Việt Đức                                               │   │
│   │  SĐT: 0986248124                                                        │   │
│   │  CCCD: 1097003791                                                       │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                     │
│            ▼                                                                     │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                    AI PARSING & UPDATE                                  │   │
│   │                                                                          │   │
│   │  Extracted:                                                             │   │
│   │  • license_plate = "29H 76514"                                         │   │
│   │  • driver_name = "Nguyễn Việt Đức"                                     │   │
│   │  • driver_phone = "0986248124"                                         │   │
│   │  • driver_id_card = "1097003791"                                       │   │
│   │                                                                          │   │
│   │  UPDATE jobs SET                                                        │   │
│   │    license_plate = '29H 76514',                                        │   │
│   │    driver_name = 'Nguyễn Việt Đức',                                    │   │
│   │    driver_phone = '0986248124',                                        │   │
│   │    status = 'DISPATCHED',                                              │   │
│   │    dispatched_at = NOW()                                               │   │
│   │  WHERE job_number = 'TRK-2601-0001'                                    │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│            │                                                                     │
│            ▼                                                                     │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                    NOTIFY CUSTOMER                                      │   │
│   │                                                                          │   │
│   │  📤 Zalo Message to Customer:                                           │   │
│   │  ────────────────────────────                                           │   │
│   │  MK-DRT1 / 15.01 / 22:00 / Invoice: 260115DRT-001, 260115DRTV-02      │   │
│   │  / PCB / 8 box / 1.25T / BKS: 29H 76514 / Nguyễn Việt Đức             │   │
│   │  - 0986248124 - CCCD: 1097003791                                       │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Assignment API

```python
@router.put("/jobs/{job_id}/assign")
async def assign_job(
    job_id: int,
    assignment: JobAssignment,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(404, "Job not found")
    
    if job.status not in ['PENDING', 'CONFIRMED']:
        raise HTTPException(400, f"Cannot assign job in {job.status} status")
    
    # Update assignment
    job.vendor_id = assignment.vendor_id
    job.vehicle_id = assignment.vehicle_id
    job.driver_id = assignment.driver_id
    job.license_plate = assignment.license_plate
    job.driver_name = assignment.driver_name
    job.driver_phone = assignment.driver_phone
    
    # Update status
    old_status = job.status
    job.status = 'DISPATCHED'
    job.dispatched_at = datetime.now()
    
    # Calculate cost
    job.cost_amount = get_vendor_rate(
        job.vendor_id, 
        job.route_id, 
        job.vehicle_type
    )
    
    db.commit()
    
    # Log status change
    log_status_change(db, job.id, old_status, 'DISPATCHED', current_user.id)
    
    return job
```

---

## 4. Job Execution

### 4.1 Execution Tracking

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        JOB EXECUTION TRACKING                                    │
│                                                                                  │
│   Job: TRK-2601-0001                                                            │
│   Customer: DREAMTECH VIETNAM                                                    │
│   Route: KCN Quang Minh → Nội thành HN                                          │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                         TIMELINE                                        │   │
│   │                                                                          │   │
│   │  15/01 21:30 ─── DISPATCHED ────────────────────────────────────────   │   │
│   │               │ Vehicle 29H 76514 assigned                              │   │
│   │               │ Driver: Nguyễn Việt Đức                                │   │
│   │               │ Customer notified ✓                                     │   │
│   │                                                                          │   │
│   │  15/01 22:00 ─── IN_TRANSIT ────────────────────────────────────────   │   │
│   │               │ Arrived at pickup location                              │   │
│   │               │ Started loading                                         │   │
│   │                                                                          │   │
│   │  15/01 22:15 ─── IN_TRANSIT ────────────────────────────────────────   │   │
│   │               │ Loading complete                                        │   │
│   │               │ Departed for delivery                                   │   │
│   │                                                                          │   │
│   │  15/01 23:30 ─── DELIVERED ─────────────────────────────────────────   │   │
│   │               │ Arrived at destination                                  │   │
│   │               │ Unloading started                                       │   │
│   │                                                                          │   │
│   │  15/01 23:45 ─── COMPLETED ─────────────────────────────────────────   │   │
│   │               │ Delivery confirmed                                      │   │
│   │               │ POD received                                           │   │
│   │               │ Ready for billing                                       │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Job Events Table

```sql
CREATE TABLE job_events (
    id              SERIAL PRIMARY KEY,
    job_id          INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    
    -- Event info
    event_type      VARCHAR(50) NOT NULL,
    -- DISPATCHED, PICKUP_ARRIVED, LOADING_START, LOADING_COMPLETE,
    -- DEPARTED, IN_TRANSIT, DELIVERY_ARRIVED, UNLOADING_START, 
    -- UNLOADING_COMPLETE, POD_RECEIVED, COMPLETED
    
    event_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    location        POINT,
    location_name   VARCHAR(200),
    
    -- Details
    description     TEXT,
    photo_urls      TEXT[],
    
    -- Source
    reported_by     VARCHAR(50),                    -- DRIVER, SYSTEM, CUSTOMER
    user_id         INTEGER REFERENCES users(id),
    
    -- Meta
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. Job Completion

### 5.1 Completion Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        JOB COMPLETION FLOW                                       │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                    DELIVERY CONFIRMATION                                │   │
│   │                                                                          │   │
│   │  Driver/Customer confirms:                                              │   │
│   │  • Cargo delivered in good condition                                    │   │
│   │  • Quantity matches (8 box)                                            │   │
│   │  • POD signed                                                          │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                    COMPLETE JOB                                         │   │
│   │                                                                          │   │
│   │  UPDATE jobs SET                                                        │   │
│   │    status = 'COMPLETED',                                               │   │
│   │    completed_at = NOW(),                                               │   │
│   │    cost_amount = 850000,        -- From vendor rate                    │   │
│   │    revenue_amount = 1030000,    -- From customer rate                  │   │
│   │    profit_amount = 180000,      -- Calculated                          │   │
│   │    billing_status = 'UNBILLED'                                         │   │
│   │  WHERE job_number = 'TRK-2601-0001'                                    │   │
│   │                                                                          │   │
│   │  Job is now ready for:                                                 │   │
│   │  • Customer Statement (billing)                                        │   │
│   │  • Vendor Statement (payment)                                          │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Completion Trigger

```sql
-- Trigger to calculate financials on completion
CREATE OR REPLACE FUNCTION job_completion_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'COMPLETED' AND OLD.status != 'COMPLETED' THEN
        -- Set completion time
        NEW.completed_at := CURRENT_TIMESTAMP;
        
        -- Get vendor rate (cost)
        IF NEW.cost_amount IS NULL THEN
            NEW.cost_amount := get_vendor_rate(
                NEW.vendor_id, 
                NEW.route_id, 
                NEW.vehicle_type
            );
        END IF;
        
        -- Get customer rate (revenue)
        IF NEW.revenue_amount IS NULL THEN
            NEW.revenue_amount := get_customer_rate(
                NEW.customer_id, 
                NEW.route_id, 
                NEW.vehicle_type
            );
        END IF;
        
        -- Calculate profit
        NEW.profit_amount := COALESCE(NEW.revenue_amount, 0) - COALESCE(NEW.cost_amount, 0);
        
        -- Set billing status
        NEW.billing_status := 'UNBILLED';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_job_completion
BEFORE UPDATE ON jobs
FOR EACH ROW EXECUTE FUNCTION job_completion_trigger();
```

---

## 📊 SUMMARY

### Key Tables
1. `jobs` - Main job table
2. `job_items` - Job line items
3. `job_status_history` - Status changes
4. `job_events` - Timeline events

### Job Statuses
- DRAFT → PENDING → CONFIRMED → DISPATCHED → IN_TRANSIT → DELIVERED → COMPLETED
- CANCELLED (can occur at most stages)

### Integration Points
- **Module 1**: Customer, Vendor, Driver, Vehicle, Route, Rate references
- **Module 3**: Statement linking, billing status
- **Module 4**: AI parsing for job creation and vehicle assignment
