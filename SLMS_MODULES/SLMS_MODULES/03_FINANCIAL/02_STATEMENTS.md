# 📋 MODULE 3.2: STATEMENTS (Bảng kê)

## 📋 Mục lục
1. [Statement Overview](#1-statement-overview)
2. [Customer Statements](#2-customer-statements)
3. [Vendor Statements](#3-vendor-statements)
4. [Reconciliation](#4-reconciliation)

---

## 1. Statement Overview

### 1.1 Statement Types

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         STATEMENT TYPES                                          │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 📤 CUSTOMER STATEMENT (Bảng kê khách hàng)                              │   │
│   │                                                                          │   │
│   │  Purpose: Billing customers for completed jobs                          │   │
│   │  Content: List of jobs with selling prices                              │   │
│   │  Output:  Invoice basis, AR tracking                                    │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 📥 VENDOR STATEMENT (Bảng kê nhà cung cấp)                              │   │
│   │                                                                          │   │
│   │  Purpose: Reconcile with vendor invoices                                │   │
│   │  Content: List of jobs with cost prices                                 │   │
│   │  Output:  AP tracking, payment basis                                    │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Statement Schema

```sql
-- Main statement table
CREATE TABLE statements (
    id              SERIAL PRIMARY KEY,
    statement_number VARCHAR(30) UNIQUE NOT NULL,   -- STM-C-2601-0001, STM-V-2601-0001
    
    -- Type
    statement_type  VARCHAR(10) NOT NULL,           -- CUSTOMER, VENDOR
    
    -- Entity
    customer_id     INTEGER REFERENCES customers(id),
    vendor_id       INTEGER REFERENCES vendors(id),
    entity_code     VARCHAR(20),
    entity_name     VARCHAR(200),
    
    -- Period
    period_from     DATE NOT NULL,
    period_to       DATE NOT NULL,
    
    -- Totals
    total_jobs      INTEGER DEFAULT 0,
    subtotal        DECIMAL(15,2) DEFAULT 0,
    tax_amount      DECIMAL(15,2) DEFAULT 0,
    total_amount    DECIMAL(15,2) DEFAULT 0,
    currency        VARCHAR(3) DEFAULT 'VND',
    
    -- Status
    status          VARCHAR(20) DEFAULT 'DRAFT',
    -- DRAFT → CONFIRMED → SENT → RECONCILED → INVOICED → PAID
    
    -- Dates
    confirmed_at    TIMESTAMP,
    sent_at         TIMESTAMP,
    reconciled_at   TIMESTAMP,
    invoiced_at     TIMESTAMP,
    paid_at         TIMESTAMP,
    
    -- Invoice link
    invoice_number  VARCHAR(50),
    invoice_date    DATE,
    
    -- Payment
    payment_due_date DATE,
    payment_amount  DECIMAL(15,2),
    payment_date    DATE,
    payment_reference VARCHAR(100),
    
    -- Meta
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by      INTEGER REFERENCES users(id),
    notes           TEXT,
    
    CHECK (
        (statement_type = 'CUSTOMER' AND customer_id IS NOT NULL) OR
        (statement_type = 'VENDOR' AND vendor_id IS NOT NULL)
    )
);

-- Statement line items
CREATE TABLE statement_items (
    id              SERIAL PRIMARY KEY,
    statement_id    INTEGER REFERENCES statements(id) ON DELETE CASCADE,
    job_id          INTEGER REFERENCES jobs(id),
    
    -- Job reference
    job_number      VARCHAR(20),
    job_date        DATE,
    
    -- Details
    description     TEXT,
    route_code      VARCHAR(50),
    vehicle_type    VARCHAR(20),
    invoice_numbers TEXT,
    
    -- Pricing
    quantity        DECIMAL(10,2) DEFAULT 1,
    unit_price      DECIMAL(12,2),
    line_total      DECIMAL(12,2),
    
    -- Status
    is_disputed     BOOLEAN DEFAULT FALSE,
    dispute_reason  TEXT,
    
    -- Sequence
    line_number     INTEGER,
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_statement_type ON statements(statement_type);
CREATE INDEX idx_statement_customer ON statements(customer_id);
CREATE INDEX idx_statement_vendor ON statements(vendor_id);
CREATE INDEX idx_statement_status ON statements(status);
CREATE INDEX idx_statement_period ON statements(period_from, period_to);
```

---

## 2. Customer Statements

### 2.1 Generate Customer Statement

```sql
-- Function to generate customer statement
CREATE OR REPLACE FUNCTION generate_customer_statement(
    p_customer_id INTEGER,
    p_from_date DATE,
    p_to_date DATE,
    p_user_id INTEGER
) RETURNS INTEGER AS $$
DECLARE
    v_statement_id INTEGER;
    v_statement_number VARCHAR(30);
    v_customer RECORD;
    v_totals RECORD;
BEGIN
    -- Get customer info
    SELECT * INTO v_customer FROM customers WHERE id = p_customer_id;
    
    -- Generate statement number
    v_statement_number := 'STM-C-' || TO_CHAR(CURRENT_DATE, 'YYMM') || '-' ||
        LPAD((SELECT COUNT(*) + 1 FROM statements 
              WHERE statement_type = 'CUSTOMER' 
              AND statement_number LIKE 'STM-C-' || TO_CHAR(CURRENT_DATE, 'YYMM') || '%')::TEXT, 4, '0');
    
    -- Calculate totals
    SELECT 
        COUNT(*) as job_count,
        COALESCE(SUM(revenue_amount), 0) as total
    INTO v_totals
    FROM jobs
    WHERE customer_id = p_customer_id
      AND booking_date BETWEEN p_from_date AND p_to_date
      AND status = 'COMPLETED'
      AND billing_status = 'UNBILLED';
    
    -- Create statement
    INSERT INTO statements (
        statement_number, statement_type, customer_id, entity_code, entity_name,
        period_from, period_to, total_jobs, subtotal, total_amount,
        status, created_by
    ) VALUES (
        v_statement_number, 'CUSTOMER', p_customer_id, v_customer.customer_code, v_customer.customer_name,
        p_from_date, p_to_date, v_totals.job_count, v_totals.total, v_totals.total,
        'DRAFT', p_user_id
    ) RETURNING id INTO v_statement_id;
    
    -- Add line items
    INSERT INTO statement_items (
        statement_id, job_id, job_number, job_date, description,
        route_code, vehicle_type, invoice_numbers, quantity, unit_price, line_total, line_number
    )
    SELECT 
        v_statement_id,
        j.id,
        j.job_number,
        j.booking_date,
        COALESCE(j.cargo_type, '') || ' - ' || COALESCE(j.package_info, ''),
        r.route_code,
        j.vehicle_type,
        j.invoice_numbers,
        1,
        j.revenue_amount,
        j.revenue_amount,
        ROW_NUMBER() OVER (ORDER BY j.booking_date, j.job_number)
    FROM jobs j
    LEFT JOIN routes r ON j.route_id = r.id
    WHERE j.customer_id = p_customer_id
      AND j.booking_date BETWEEN p_from_date AND p_to_date
      AND j.status = 'COMPLETED'
      AND j.billing_status = 'UNBILLED';
    
    -- Update jobs billing status
    UPDATE jobs SET 
        billing_status = 'IN_STATEMENT',
        customer_statement_id = v_statement_id
    WHERE customer_id = p_customer_id
      AND booking_date BETWEEN p_from_date AND p_to_date
      AND status = 'COMPLETED'
      AND billing_status = 'UNBILLED';
    
    RETURN v_statement_id;
END;
$$ LANGUAGE plpgsql;
```

### 2.2 Customer Statement Format

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      CUSTOMER STATEMENT                                          │
│                                                                                  │
│   Statement #: STM-C-2601-0001                                                  │
│   Customer: CÔNG TY TNHH DREAMTECH VIETNAM (DRT1)                              │
│   Period: 01/01/2026 - 15/01/2026                                              │
│   Generated: 16/01/2026                                                         │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ #  │ Date  │ Job Number    │ Route  │ Vehicle │ Invoice      │ Amount   │   │
│   ├────┼───────┼───────────────┼────────┼─────────┼──────────────┼──────────┤   │
│   │ 1  │ 02/01 │ TRK-2601-0001 │ MK-HN  │ 1.25T   │ 260102DRT-01 │ 1,030,000│   │
│   │ 2  │ 03/01 │ TRK-2601-0005 │ MK-HN  │ 2.5T    │ 260103DRT-02 │ 1,450,000│   │
│   │ 3  │ 05/01 │ TRK-2601-0012 │ MK-HP  │ 1.25T   │ 260105DRT-03 │ 3,000,000│   │
│   │ 4  │ 08/01 │ TRK-2601-0023 │ MK-HN  │ 1.25T   │ 260108DRT-04 │ 1,030,000│   │
│   │ 5  │ 10/01 │ TRK-2601-0031 │ MK-BN  │ 2.5T    │ 260110DRT-05 │ 1,150,000│   │
│   │ .. │ ..    │ ...           │ ...    │ ...     │ ...          │ ...      │   │
│   │ 15 │ 15/01 │ TRK-2601-0089 │ MK-HN  │ 5T      │ 260115DRT-15 │ 2,200,000│   │
│   ├────┴───────┴───────────────┴────────┴─────────┴──────────────┼──────────┤   │
│   │                                              SUBTOTAL        │23,450,000│   │
│   │                                              VAT (0%)        │        0 │   │
│   │                                              TOTAL           │23,450,000│   │
│   └──────────────────────────────────────────────────────────────┴──────────┘   │
│                                                                                  │
│   Payment Terms: 30 days                                                        │
│   Due Date: 15/02/2026                                                          │
│                                                                                  │
│   Bank: Vietcombank                                                             │
│   Account: 0123456789                                                           │
│   Account Name: CONG TY TNHH MINH KHANG LOGISTICS                              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Vendor Statements

### 3.1 Generate Vendor Statement

```sql
-- Function to generate vendor statement
CREATE OR REPLACE FUNCTION generate_vendor_statement(
    p_vendor_id INTEGER,
    p_from_date DATE,
    p_to_date DATE,
    p_user_id INTEGER
) RETURNS INTEGER AS $$
DECLARE
    v_statement_id INTEGER;
    v_statement_number VARCHAR(30);
    v_vendor RECORD;
    v_totals RECORD;
BEGIN
    -- Get vendor info
    SELECT * INTO v_vendor FROM vendors WHERE id = p_vendor_id;
    
    -- Generate statement number
    v_statement_number := 'STM-V-' || TO_CHAR(CURRENT_DATE, 'YYMM') || '-' ||
        LPAD((SELECT COUNT(*) + 1 FROM statements 
              WHERE statement_type = 'VENDOR' 
              AND statement_number LIKE 'STM-V-' || TO_CHAR(CURRENT_DATE, 'YYMM') || '%')::TEXT, 4, '0');
    
    -- Calculate totals
    SELECT 
        COUNT(*) as job_count,
        COALESCE(SUM(cost_amount), 0) as total
    INTO v_totals
    FROM jobs
    WHERE vendor_id = p_vendor_id
      AND booking_date BETWEEN p_from_date AND p_to_date
      AND status = 'COMPLETED';
    
    -- Create statement
    INSERT INTO statements (
        statement_number, statement_type, vendor_id, entity_code, entity_name,
        period_from, period_to, total_jobs, subtotal, total_amount,
        status, created_by
    ) VALUES (
        v_statement_number, 'VENDOR', p_vendor_id, v_vendor.vendor_code, v_vendor.vendor_name,
        p_from_date, p_to_date, v_totals.job_count, v_totals.total, v_totals.total,
        'DRAFT', p_user_id
    ) RETURNING id INTO v_statement_id;
    
    -- Add line items
    INSERT INTO statement_items (
        statement_id, job_id, job_number, job_date, description,
        route_code, vehicle_type, invoice_numbers, quantity, unit_price, line_total, line_number
    )
    SELECT 
        v_statement_id,
        j.id,
        j.job_number,
        j.booking_date,
        j.license_plate || ' - ' || COALESCE(j.driver_name, ''),
        r.route_code,
        j.vehicle_type,
        j.invoice_numbers,
        1,
        j.cost_amount,
        j.cost_amount,
        ROW_NUMBER() OVER (ORDER BY j.booking_date, j.job_number)
    FROM jobs j
    LEFT JOIN routes r ON j.route_id = r.id
    WHERE j.vendor_id = p_vendor_id
      AND j.booking_date BETWEEN p_from_date AND p_to_date
      AND j.status = 'COMPLETED';
    
    -- Update jobs
    UPDATE jobs SET vendor_statement_id = v_statement_id
    WHERE vendor_id = p_vendor_id
      AND booking_date BETWEEN p_from_date AND p_to_date
      AND status = 'COMPLETED';
    
    RETURN v_statement_id;
END;
$$ LANGUAGE plpgsql;
```

---

## 4. Reconciliation

### 4.1 Reconciliation Process

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      RECONCILIATION PROCESS                                      │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ STEP 1: Generate Internal Statement                                     │   │
│   │                                                                          │   │
│   │  System generates statement from completed jobs                         │   │
│   │  Status: DRAFT                                                          │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ STEP 2: Receive Vendor Statement                                        │   │
│   │                                                                          │   │
│   │  Vendor sends their statement/invoice                                   │   │
│   │  Can be: Excel, PDF, or Zalo message                                    │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ STEP 3: Compare & Match                                                 │   │
│   │                                                                          │   │
│   │  ┌────────────────────┐     ┌────────────────────┐                     │   │
│   │  │ INTERNAL STATEMENT │     │ VENDOR STATEMENT   │                     │   │
│   │  │                    │     │                    │                     │   │
│   │  │ Job TRK-001: 850K  │ ←→  │ 02/01: 850K       │ ✓ Match             │   │
│   │  │ Job TRK-005: 1.2M  │ ←→  │ 03/01: 1.2M       │ ✓ Match             │   │
│   │  │ Job TRK-012: 2.5M  │ ←→  │ 05/01: 2.8M       │ ✗ Difference: 300K │   │
│   │  │                    │     │ 06/01: 900K       │ ✗ Not in our record │   │
│   │  └────────────────────┘     └────────────────────┘                     │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ STEP 4: Resolve Differences                                             │   │
│   │                                                                          │   │
│   │  • Mark disputed items                                                  │   │
│   │  • Add notes/explanations                                               │   │
│   │  • Adjust if needed                                                     │   │
│   │  Status: RECONCILED                                                     │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ STEP 5: Approve & Pay                                                   │   │
│   │                                                                          │   │
│   │  • Finance approves final amount                                        │   │
│   │  • Process payment                                                      │   │
│   │  Status: PAID                                                           │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Reconciliation Table

```sql
CREATE TABLE statement_reconciliations (
    id              SERIAL PRIMARY KEY,
    statement_id    INTEGER REFERENCES statements(id),
    
    -- External reference
    external_doc_type VARCHAR(20),                  -- INVOICE, STATEMENT
    external_doc_number VARCHAR(50),
    external_doc_date DATE,
    external_total  DECIMAL(15,2),
    
    -- Comparison
    internal_total  DECIMAL(15,2),
    difference      DECIMAL(15,2),
    
    -- Status
    status          VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, MATCHED, DISPUTED, RESOLVED
    
    -- Resolution
    resolution_type VARCHAR(20),                    -- ACCEPTED, ADJUSTED, REJECTED
    adjusted_amount DECIMAL(15,2),
    resolution_notes TEXT,
    resolved_by     INTEGER REFERENCES users(id),
    resolved_at     TIMESTAMP,
    
    -- Meta
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by      INTEGER REFERENCES users(id)
);

-- Reconciliation line items
CREATE TABLE reconciliation_items (
    id              SERIAL PRIMARY KEY,
    reconciliation_id INTEGER REFERENCES statement_reconciliations(id),
    statement_item_id INTEGER REFERENCES statement_items(id),
    
    -- External data
    external_date   DATE,
    external_description TEXT,
    external_amount DECIMAL(12,2),
    
    -- Internal data
    internal_amount DECIMAL(12,2),
    
    -- Comparison
    difference      DECIMAL(12,2),
    match_status    VARCHAR(20),                    -- MATCHED, DIFFERENT, MISSING_INTERNAL, MISSING_EXTERNAL
    
    -- Resolution
    resolution      TEXT,
    is_resolved     BOOLEAN DEFAULT FALSE
);
```

---

## 📊 SUMMARY

### Statement Types
1. **Customer Statement** - For billing (AR)
2. **Vendor Statement** - For payment (AP)

### Statement Flow
DRAFT → CONFIRMED → SENT → RECONCILED → INVOICED → PAID

### Key Features
- Auto-generate from completed jobs
- Line item details
- Reconciliation with external documents
- Dispute tracking

### Tables
1. `statements` - Main statement records
2. `statement_items` - Line items
3. `statement_reconciliations` - Comparison records
4. `reconciliation_items` - Line-level comparison

### Integration Points
- **Module 2**: Jobs linked to statements
- **Module 3.4**: MISA invoice sync
- **Module 4**: AI parses vendor statements
