# 💰 MODULE 3.1: PRICING MANAGEMENT

## 📋 Mục lục
1. [Pricing Overview](#1-pricing-overview)
2. [Vendor Rates](#2-vendor-rates-giá-mua)
3. [Customer Rates](#3-customer-rates-giá-bán)
4. [Margin Calculation](#4-margin-calculation)
5. [Rate Management](#5-rate-management)

---

## 1. Pricing Overview

### 1.1 Pricing Model

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          PRICING MODEL                                           │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                          │   │
│   │   VENDOR RATE (Cost)          CUSTOMER RATE (Revenue)                   │   │
│   │   ──────────────────          ───────────────────────                   │   │
│   │                                                                          │   │
│   │   Vendor: Tam Bảo             Customer: DREAMTECH                       │   │
│   │   Route: MK-HN                Route: MK-HN                              │   │
│   │   Vehicle: 1.25T              Vehicle: 1.25T                            │   │
│   │   ─────────────────           ─────────────────                         │   │
│   │   Price: 850,000 VND          Price: 1,030,000 VND                      │   │
│   │                                                                          │   │
│   │              │                           │                               │   │
│   │              └───────────┬───────────────┘                               │   │
│   │                          │                                               │   │
│   │                          ▼                                               │   │
│   │                   ┌─────────────┐                                        │   │
│   │                   │   MARGIN    │                                        │   │
│   │                   │  180,000    │                                        │   │
│   │                   │   (21.2%)   │                                        │   │
│   │                   └─────────────┘                                        │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Pricing Dimensions

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       PRICING DIMENSIONS                                         │
│                                                                                  │
│   Dimension        │ Values                        │ Impact                     │
│   ─────────────────┼───────────────────────────────┼─────────────────────────── │
│   Route            │ MK-HN, MK-HP, MK-BN, MK-QN    │ Distance-based pricing     │
│   Vehicle Type     │ 1.25T, 2.5T, 5T, 10T, 15T     │ Capacity-based pricing     │
│   Service Type     │ Trucking, Customs, Warehouse  │ Service-specific rates     │
│   Time             │ Day, Night, Weekend, Holiday  │ Time-based surcharges      │
│   Urgency          │ Normal, Express, Same-day     │ Priority surcharges        │
│   Contract         │ Spot, Contract, VIP           │ Negotiated discounts       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Vendor Rates (Giá mua)

### 2.1 Vendor Rate Table

```sql
CREATE TABLE vendor_rates (
    id              SERIAL PRIMARY KEY,
    vendor_id       INTEGER REFERENCES vendors(id) NOT NULL,
    
    -- Rate Key
    service_id      INTEGER REFERENCES services(id),
    route_id        INTEGER REFERENCES routes(id),
    vehicle_type    VARCHAR(20),
    
    -- Pricing
    base_price      DECIMAL(12,2) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'VND',
    unit            VARCHAR(20) DEFAULT 'TRIP',     -- TRIP, KG, CBM, CONT
    
    -- Surcharges
    night_surcharge DECIMAL(5,2) DEFAULT 0,         -- % increase for night
    weekend_surcharge DECIMAL(5,2) DEFAULT 0,       -- % increase for weekend
    holiday_surcharge DECIMAL(5,2) DEFAULT 0,       -- % increase for holiday
    
    -- Validity
    effective_date  DATE NOT NULL,
    expiry_date     DATE,
    
    -- Conditions
    min_quantity    DECIMAL(10,2),
    max_quantity    DECIMAL(10,2),
    conditions      TEXT,
    
    -- Status
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by      INTEGER REFERENCES users(id),
    approved_by     INTEGER REFERENCES users(id),
    approved_at     TIMESTAMP,
    notes           TEXT,
    
    -- Source tracking (for AI parsing)
    source_type     VARCHAR(20),                    -- MANUAL, AI_PARSED, IMPORT
    source_file     VARCHAR(255),
    
    UNIQUE (vendor_id, service_id, route_id, vehicle_type, effective_date)
);

-- Vendor rate history for tracking changes
CREATE TABLE vendor_rate_history (
    id              SERIAL PRIMARY KEY,
    rate_id         INTEGER REFERENCES vendor_rates(id),
    old_price       DECIMAL(12,2),
    new_price       DECIMAL(12,2),
    change_percent  DECIMAL(5,2),
    changed_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by      INTEGER REFERENCES users(id),
    reason          TEXT
);
```

### 2.2 Sample Vendor Rates

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      VENDOR RATES - TAM BẢO                                      │
│                      Effective: 01/01/2026                                       │
│                                                                                  │
│   Route    │ 1.25T      │ 2.5T       │ 5T         │ 10T        │ 15T           │
│   ─────────┼────────────┼────────────┼────────────┼────────────┼────────────── │
│   MK-HN    │ 850,000    │ 1,200,000  │ 1,800,000  │ 2,800,000  │ 3,500,000    │
│   MK-HP    │ 2,500,000  │ 3,200,000  │ 4,500,000  │ 6,500,000  │ 8,000,000    │
│   MK-BN    │ 700,000    │ 950,000    │ 1,400,000  │ 2,200,000  │ 2,800,000    │
│   MK-QN    │ 3,200,000  │ 4,000,000  │ 5,500,000  │ 8,000,000  │ 10,000,000   │
│   MK-HY    │ 900,000    │ 1,300,000  │ 1,900,000  │ 3,000,000  │ 3,800,000    │
│                                                                                  │
│   Surcharges:                                                                   │
│   • Night (22:00-06:00): +10%                                                   │
│   • Weekend: +5%                                                                │
│   • Holiday: +20%                                                               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Customer Rates (Giá bán)

### 3.1 Customer Rate Table

```sql
CREATE TABLE customer_rates (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER REFERENCES customers(id) NOT NULL,
    
    -- Rate Key
    service_id      INTEGER REFERENCES services(id),
    route_id        INTEGER REFERENCES routes(id),
    vehicle_type    VARCHAR(20),
    
    -- Pricing
    selling_price   DECIMAL(12,2) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'VND',
    unit            VARCHAR(20) DEFAULT 'TRIP',
    
    -- Cost Reference
    vendor_id       INTEGER REFERENCES vendors(id),
    vendor_rate_id  INTEGER REFERENCES vendor_rates(id),
    cost_price      DECIMAL(12,2),
    
    -- Margin
    margin_amount   DECIMAL(12,2),
    margin_percent  DECIMAL(5,2),
    
    -- Validity
    effective_date  DATE NOT NULL,
    expiry_date     DATE,
    
    -- Contract
    contract_number VARCHAR(50),
    contract_date   DATE,
    
    -- Status
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by      INTEGER REFERENCES users(id),
    approved_by     INTEGER REFERENCES users(id),
    notes           TEXT,
    
    UNIQUE (customer_id, service_id, route_id, vehicle_type, effective_date)
);

-- Auto-calculate margin
CREATE OR REPLACE FUNCTION calc_customer_rate_margin()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.cost_price IS NOT NULL AND NEW.cost_price > 0 THEN
        NEW.margin_amount := NEW.selling_price - NEW.cost_price;
        NEW.margin_percent := ((NEW.selling_price - NEW.cost_price) / NEW.cost_price) * 100;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_calc_margin
BEFORE INSERT OR UPDATE ON customer_rates
FOR EACH ROW EXECUTE FUNCTION calc_customer_rate_margin();
```

### 3.2 Sample Customer Rates

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    CUSTOMER RATES - DREAMTECH                                    │
│                    Contract: DRT-2026-001                                        │
│                    Effective: 01/01/2026                                         │
│                                                                                  │
│   Route    │ Vehicle │ Selling     │ Cost        │ Margin     │ Margin %       │
│   ─────────┼─────────┼─────────────┼─────────────┼────────────┼─────────────── │
│   MK-HN    │ 1.25T   │ 1,030,000   │ 850,000     │ 180,000    │ 21.2%          │
│   MK-HN    │ 2.5T    │ 1,450,000   │ 1,200,000   │ 250,000    │ 20.8%          │
│   MK-HN    │ 5T      │ 2,200,000   │ 1,800,000   │ 400,000    │ 22.2%          │
│   MK-HP    │ 1.25T   │ 3,000,000   │ 2,500,000   │ 500,000    │ 20.0%          │
│   MK-HP    │ 2.5T    │ 3,900,000   │ 3,200,000   │ 700,000    │ 21.9%          │
│   MK-BN    │ 1.25T   │ 850,000     │ 700,000     │ 150,000    │ 21.4%          │
│                                                                                  │
│   Target Margin: 20-25%                                                         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Margin Calculation

### 4.1 Margin Analysis Functions

```sql
-- Get margin for a specific job
CREATE OR REPLACE FUNCTION get_job_margin(p_job_id INTEGER)
RETURNS TABLE (
    job_number VARCHAR,
    revenue DECIMAL,
    cost DECIMAL,
    margin_amount DECIMAL,
    margin_percent DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        j.job_number,
        j.revenue_amount,
        j.cost_amount,
        j.revenue_amount - j.cost_amount,
        CASE 
            WHEN j.cost_amount > 0 
            THEN ((j.revenue_amount - j.cost_amount) / j.cost_amount) * 100
            ELSE 0
        END
    FROM jobs j
    WHERE j.id = p_job_id;
END;
$$ LANGUAGE plpgsql;

-- Get margin by customer
CREATE OR REPLACE FUNCTION get_customer_margin_report(
    p_customer_id INTEGER,
    p_from_date DATE,
    p_to_date DATE
)
RETURNS TABLE (
    customer_code VARCHAR,
    total_jobs INTEGER,
    total_revenue DECIMAL,
    total_cost DECIMAL,
    total_margin DECIMAL,
    avg_margin_percent DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.customer_code,
        COUNT(j.id)::INTEGER,
        SUM(j.revenue_amount),
        SUM(j.cost_amount),
        SUM(j.revenue_amount - j.cost_amount),
        AVG(((j.revenue_amount - j.cost_amount) / NULLIF(j.cost_amount, 0)) * 100)
    FROM jobs j
    JOIN customers c ON j.customer_id = c.id
    WHERE j.customer_id = p_customer_id
      AND j.booking_date BETWEEN p_from_date AND p_to_date
      AND j.status = 'COMPLETED'
    GROUP BY c.customer_code;
END;
$$ LANGUAGE plpgsql;
```

### 4.2 Margin Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       MARGIN DASHBOARD - January 2026                            │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ OVERALL SUMMARY                                                         │   │
│   │                                                                          │   │
│   │   Total Revenue:    89,500,000 VND                                      │   │
│   │   Total Cost:       71,200,000 VND                                      │   │
│   │   Gross Margin:     18,300,000 VND                                      │   │
│   │   Margin %:         25.7%                                               │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ BY CUSTOMER                                                             │   │
│   │                                                                          │   │
│   │   Customer     │ Jobs │ Revenue      │ Cost         │ Margin   │ %      │   │
│   │   ─────────────┼──────┼──────────────┼──────────────┼──────────┼─────── │   │
│   │   DREAMTECH    │  45  │ 45,850,000   │ 36,500,000   │ 9,350,000│ 25.6%  │   │
│   │   HOSIDEN      │  28  │ 28,500,000   │ 23,200,000   │ 5,300,000│ 22.8%  │   │
│   │   SAMSUNG      │  12  │ 15,150,000   │ 11,500,000   │ 3,650,000│ 31.7%  │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ BY ROUTE                                                                │   │
│   │                                                                          │   │
│   │   Route   │ Jobs │ Avg Revenue │ Avg Cost  │ Avg Margin │ Margin %     │   │
│   │   ────────┼──────┼─────────────┼───────────┼────────────┼───────────── │   │
│   │   MK-HN   │  52  │ 1,150,000   │ 920,000   │ 230,000    │ 25.0%        │   │
│   │   MK-HP   │  18  │ 3,200,000   │ 2,650,000 │ 550,000    │ 20.8%        │   │
│   │   MK-BN   │  15  │ 850,000     │ 680,000   │ 170,000    │ 25.0%        │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Rate Management

### 5.1 Rate Import from AI

```python
# rate_import.py

async def import_vendor_quote(ai_response: dict, user_id: int) -> list:
    """Import vendor rates from AI-parsed quote"""
    
    vendor_code = ai_response.get('vendor_code')
    vendor = await get_vendor_by_code(vendor_code)
    
    if not vendor:
        raise ValueError(f"Vendor not found: {vendor_code}")
    
    imported_rates = []
    
    for item in ai_response.get('items', []):
        route = await get_route_by_code(item['route'])
        
        rate = VendorRate(
            vendor_id=vendor.id,
            route_id=route.id if route else None,
            vehicle_type=item['vehicle_type'],
            base_price=item['price'],
            effective_date=ai_response.get('effective_date', date.today()),
            source_type='AI_PARSED',
            created_by=user_id
        )
        
        # Check for existing rate
        existing = await get_existing_rate(
            vendor.id, route.id, item['vehicle_type']
        )
        
        if existing:
            # Update existing rate
            existing.base_price = rate.base_price
            existing.effective_date = rate.effective_date
            await update_rate(existing)
            imported_rates.append(('UPDATED', existing))
        else:
            # Create new rate
            await create_rate(rate)
            imported_rates.append(('CREATED', rate))
    
    return imported_rates
```

### 5.2 Rate Expiry Alert

```sql
-- View for expiring rates
CREATE VIEW v_expiring_rates AS
SELECT 
    'VENDOR' as rate_type,
    v.vendor_code as entity_code,
    v.vendor_name as entity_name,
    r.route_code,
    vr.vehicle_type,
    vr.base_price as price,
    vr.expiry_date,
    vr.expiry_date - CURRENT_DATE as days_until_expiry
FROM vendor_rates vr
JOIN vendors v ON vr.vendor_id = v.id
LEFT JOIN routes r ON vr.route_id = r.id
WHERE vr.is_active = TRUE
  AND vr.expiry_date IS NOT NULL
  AND vr.expiry_date <= CURRENT_DATE + INTERVAL '30 days'

UNION ALL

SELECT 
    'CUSTOMER',
    c.customer_code,
    c.customer_name,
    r.route_code,
    cr.vehicle_type,
    cr.selling_price,
    cr.expiry_date,
    cr.expiry_date - CURRENT_DATE
FROM customer_rates cr
JOIN customers c ON cr.customer_id = c.id
LEFT JOIN routes r ON cr.route_id = r.id
WHERE cr.is_active = TRUE
  AND cr.expiry_date IS NOT NULL
  AND cr.expiry_date <= CURRENT_DATE + INTERVAL '30 days'
ORDER BY days_until_expiry;
```

---

## 📊 SUMMARY

### Pricing Structure
1. **Vendor Rates** - Cost prices from suppliers
2. **Customer Rates** - Selling prices to customers
3. **Margin** - Profit calculation

### Key Features
- Multi-dimensional pricing (route, vehicle, time)
- Automatic margin calculation
- Rate history tracking
- Expiry alerts
- AI-powered rate import

### Tables
1. `vendor_rates` - Buy prices
2. `customer_rates` - Sell prices
3. `vendor_rate_history` - Change tracking

### Integration Points
- **Module 2**: Jobs use rates for pricing
- **Module 3.2**: Statements calculated from rates
- **Module 4**: AI parses vendor quotes
