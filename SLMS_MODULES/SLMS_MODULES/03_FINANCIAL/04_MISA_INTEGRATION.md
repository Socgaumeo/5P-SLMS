# 🔗 MODULE 3.4: MISA INTEGRATION

## 📋 Mục lục
1. [Integration Overview](#1-integration-overview)
2. [Invoice Sync](#2-invoice-sync)
3. [AP/AR Sync](#3-apar-sync)
4. [Chart of Accounts](#4-chart-of-accounts)

---

## 1. Integration Overview

### 1.1 Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      MISA INTEGRATION ARCHITECTURE                               │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                           SLMS                                          │   │
│   │                                                                          │   │
│   │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐        │   │
│   │  │   Jobs     │  │ Statements │  │  Customers │  │  Vendors   │        │   │
│   │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘        │   │
│   │        │               │               │               │                │   │
│   └────────┼───────────────┼───────────────┼───────────────┼────────────────┘   │
│            │               │               │               │                    │
│            └───────────────┴───────────────┴───────────────┘                    │
│                                    │                                            │
│                                    ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                      INTEGRATION LAYER                                  │   │
│   │                                                                          │   │
│   │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │   │
│   │  │  Data Mapper   │  │  Sync Queue    │  │  Error Handler │            │   │
│   │  └────────────────┘  └────────────────┘  └────────────────┘            │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                            │
│                                    ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                         MISA API                                        │   │
│   │                                                                          │   │
│   │  POST /api/v1/invoices          - Create invoice                        │   │
│   │  GET  /api/v1/invoices/{id}     - Get invoice                          │   │
│   │  POST /api/v1/customers         - Create/Update customer                │   │
│   │  POST /api/v1/vendors           - Create/Update vendor                  │   │
│   │  GET  /api/v1/accounts          - Get chart of accounts                │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                            │
│                                    ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                       MISA SME.NET                                      │   │
│   │                                                                          │   │
│   │  • Invoices (Hóa đơn)                                                   │   │
│   │  • Customers (Khách hàng)                                               │   │
│   │  • Vendors (Nhà cung cấp)                                               │   │
│   │  • Journal Entries (Bút toán)                                           │   │
│   │  • Reports (Báo cáo)                                                    │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Sync Configuration

```sql
CREATE TABLE misa_sync_config (
    id              SERIAL PRIMARY KEY,
    config_key      VARCHAR(50) UNIQUE NOT NULL,
    config_value    TEXT,
    description     TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default configurations
INSERT INTO misa_sync_config (config_key, config_value, description) VALUES
('api_endpoint', 'https://api.misa.vn/v1', 'MISA API endpoint'),
('api_key', '', 'MISA API key'),
('company_id', '', 'MISA company ID'),
('sync_interval_minutes', '30', 'Auto sync interval'),
('auto_create_invoice', 'true', 'Auto create invoice from statement'),
('invoice_template', 'HDGTGT', 'Default invoice template'),
('ar_account', '131', 'Accounts Receivable account'),
('ap_account', '331', 'Accounts Payable account'),
('revenue_account', '511', 'Revenue account'),
('cost_account', '632', 'Cost of goods sold account');
```

---

## 2. Invoice Sync

### 2.1 Invoice Sync Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        INVOICE SYNC FLOW                                         │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ STEP 1: Statement Confirmed                                             │   │
│   │                                                                          │   │
│   │  Statement STM-C-2601-0001 confirmed                                    │   │
│   │  Customer: DREAMTECH (DRT1)                                             │   │
│   │  Total: 23,450,000 VND                                                  │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ STEP 2: Queue for MISA Sync                                             │   │
│   │                                                                          │   │
│   │  INSERT INTO misa_sync_queue (                                          │   │
│   │    entity_type = 'INVOICE',                                             │   │
│   │    entity_id = statement_id,                                            │   │
│   │    action = 'CREATE',                                                   │   │
│   │    status = 'PENDING'                                                   │   │
│   │  )                                                                       │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ STEP 3: Map to MISA Format                                              │   │
│   │                                                                          │   │
│   │  MISA Invoice:                                                          │   │
│   │  {                                                                       │   │
│   │    "invoice_template": "HDGTGT",                                        │   │
│   │    "invoice_date": "2026-01-16",                                        │   │
│   │    "customer_code": "DRT1",                                             │   │
│   │    "customer_name": "CÔNG TY TNHH DREAMTECH VIETNAM",                  │   │
│   │    "items": [                                                           │   │
│   │      {"description": "Dịch vụ vận chuyển", "amount": 23450000}         │   │
│   │    ],                                                                    │   │
│   │    "total_amount": 23450000                                             │   │
│   │  }                                                                       │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ STEP 4: Call MISA API                                                   │   │
│   │                                                                          │   │
│   │  POST /api/v1/invoices                                                  │   │
│   │  Response: { "invoice_number": "0001234", "status": "success" }        │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ STEP 5: Update SLMS                                                     │   │
│   │                                                                          │   │
│   │  UPDATE statements SET                                                  │   │
│   │    invoice_number = '0001234',                                          │   │
│   │    invoice_date = '2026-01-16',                                        │   │
│   │    status = 'INVOICED',                                                │   │
│   │    invoiced_at = NOW()                                                 │   │
│   │  WHERE id = statement_id                                               │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Sync Queue Table

```sql
CREATE TABLE misa_sync_queue (
    id              SERIAL PRIMARY KEY,
    
    -- Entity reference
    entity_type     VARCHAR(20) NOT NULL,           -- INVOICE, CUSTOMER, VENDOR, PAYMENT
    entity_id       INTEGER NOT NULL,
    
    -- Action
    action          VARCHAR(20) NOT NULL,           -- CREATE, UPDATE, DELETE
    
    -- Payload
    payload         JSONB,
    
    -- Status
    status          VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, PROCESSING, COMPLETED, FAILED
    attempts        INTEGER DEFAULT 0,
    max_attempts    INTEGER DEFAULT 3,
    
    -- Response
    misa_id         VARCHAR(50),
    misa_response   JSONB,
    error_message   TEXT,
    
    -- Timestamps
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at    TIMESTAMP,
    completed_at    TIMESTAMP
);

-- Index for processing
CREATE INDEX idx_misa_queue_status ON misa_sync_queue(status, created_at);
```

---

## 3. AP/AR Sync

### 3.1 AR Sync (Customer Receivables)

```python
# misa_sync.py

class MISASync:
    """MISA Integration Service"""
    
    def __init__(self, api_key: str, company_id: str):
        self.api_key = api_key
        self.company_id = company_id
        self.base_url = "https://api.misa.vn/v1"
    
    async def sync_customer_invoice(self, statement_id: int) -> dict:
        """Sync customer statement to MISA as invoice"""
        
        # Get statement with items
        statement = await get_statement_with_items(statement_id)
        
        # Map to MISA format
        invoice_data = {
            "ref_type": 1,  # Sales invoice
            "ref_date": datetime.now().isoformat(),
            "customer_id": await self.get_misa_customer_id(statement.customer_id),
            "customer_name": statement.entity_name,
            "total_amount": float(statement.total_amount),
            "invoice_items": [
                {
                    "item_name": "Dịch vụ vận chuyển",
                    "description": f"Bảng kê {statement.statement_number}",
                    "quantity": 1,
                    "unit_price": float(statement.total_amount),
                    "amount": float(statement.total_amount),
                    "account_code": "511"  # Revenue account
                }
            ],
            "journal_entries": [
                {
                    "debit_account": "131",  # AR
                    "credit_account": "511",  # Revenue
                    "amount": float(statement.total_amount)
                }
            ]
        }
        
        # Call MISA API
        response = await self._post("/invoices", invoice_data)
        
        return response
    
    async def sync_vendor_payment(self, statement_id: int) -> dict:
        """Sync vendor statement to MISA as payable"""
        
        statement = await get_statement_with_items(statement_id)
        
        payment_data = {
            "ref_type": 2,  # Purchase
            "ref_date": datetime.now().isoformat(),
            "vendor_id": await self.get_misa_vendor_id(statement.vendor_id),
            "vendor_name": statement.entity_name,
            "total_amount": float(statement.total_amount),
            "journal_entries": [
                {
                    "debit_account": "632",  # COGS
                    "credit_account": "331",  # AP
                    "amount": float(statement.total_amount)
                }
            ]
        }
        
        response = await self._post("/purchases", payment_data)
        
        return response
    
    async def get_ar_balance(self, customer_code: str) -> dict:
        """Get AR balance from MISA"""
        
        response = await self._get(f"/customers/{customer_code}/balance")
        
        return {
            "customer_code": customer_code,
            "balance": response.get("balance", 0),
            "as_of_date": response.get("as_of_date")
        }
    
    async def _post(self, endpoint: str, data: dict) -> dict:
        """POST to MISA API"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-Company-ID": self.company_id
            }
            async with session.post(
                f"{self.base_url}{endpoint}",
                json=data,
                headers=headers
            ) as response:
                return await response.json()
```

### 3.2 Reconciliation with MISA

```sql
-- View comparing SLMS vs MISA AR
CREATE OR REPLACE VIEW v_ar_reconciliation AS
SELECT 
    c.customer_code,
    c.customer_name,
    
    -- SLMS balance
    COALESCE(SUM(s.total_amount) FILTER (WHERE s.status NOT IN ('PAID')), 0) as slms_balance,
    
    -- MISA balance (from sync table)
    COALESCE(mb.misa_balance, 0) as misa_balance,
    
    -- Difference
    COALESCE(SUM(s.total_amount) FILTER (WHERE s.status NOT IN ('PAID')), 0) 
        - COALESCE(mb.misa_balance, 0) as difference

FROM customers c
LEFT JOIN statements s ON c.id = s.customer_id AND s.statement_type = 'CUSTOMER'
LEFT JOIN misa_balances mb ON c.customer_code = mb.entity_code AND mb.entity_type = 'CUSTOMER'
GROUP BY c.customer_code, c.customer_name, mb.misa_balance;

-- Table to store MISA balance snapshots
CREATE TABLE misa_balances (
    id              SERIAL PRIMARY KEY,
    entity_type     VARCHAR(20) NOT NULL,           -- CUSTOMER, VENDOR
    entity_code     VARCHAR(50) NOT NULL,
    misa_balance    DECIMAL(15,2),
    sync_date       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (entity_type, entity_code)
);
```

---

## 4. Chart of Accounts

### 4.1 Account Mapping

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      CHART OF ACCOUNTS MAPPING                                   │
│                                                                                  │
│   SLMS Entity          │ MISA Account  │ Description                            │
│   ─────────────────────┼───────────────┼─────────────────────────────────────── │
│   Customer Invoice     │ 131           │ Phải thu khách hàng (AR)               │
│   Vendor Payment       │ 331           │ Phải trả người bán (AP)                │
│   Revenue              │ 511           │ Doanh thu bán hàng                     │
│   Cost                 │ 632           │ Giá vốn hàng bán                       │
│   Cash Receipt         │ 111           │ Tiền mặt                               │
│   Bank Receipt         │ 112           │ Tiền gửi ngân hàng                     │
│   Advance Received     │ 131.01        │ Tạm ứng khách hàng                     │
│   Advance Paid         │ 331.01        │ Tạm ứng nhà cung cấp                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Account Mapping Table

```sql
CREATE TABLE misa_account_mapping (
    id              SERIAL PRIMARY KEY,
    slms_entity     VARCHAR(50) NOT NULL,           -- CUSTOMER_INVOICE, VENDOR_PAYMENT, etc.
    misa_account    VARCHAR(20) NOT NULL,
    account_name    VARCHAR(100),
    is_debit        BOOLEAN,                        -- TRUE = debit, FALSE = credit
    is_active       BOOLEAN DEFAULT TRUE,
    notes           TEXT
);

INSERT INTO misa_account_mapping (slms_entity, misa_account, account_name, is_debit) VALUES
('CUSTOMER_INVOICE', '131', 'Phải thu khách hàng', TRUE),
('CUSTOMER_INVOICE', '511', 'Doanh thu bán hàng', FALSE),
('VENDOR_PAYMENT', '632', 'Giá vốn hàng bán', TRUE),
('VENDOR_PAYMENT', '331', 'Phải trả người bán', FALSE),
('CUSTOMER_RECEIPT', '112', 'Tiền gửi ngân hàng', TRUE),
('CUSTOMER_RECEIPT', '131', 'Phải thu khách hàng', FALSE),
('VENDOR_DISBURSEMENT', '331', 'Phải trả người bán', TRUE),
('VENDOR_DISBURSEMENT', '112', 'Tiền gửi ngân hàng', FALSE);
```

---

## 📊 SUMMARY

### Integration Points
1. **Invoice Sync** - Statement → MISA Invoice
2. **AR Sync** - Customer receivables
3. **AP Sync** - Vendor payables
4. **Balance Reconciliation**

### Key Features
- Automatic invoice creation from statements
- Queue-based async sync
- Error handling and retry
- Balance reconciliation

### Tables
1. `misa_sync_config` - Configuration
2. `misa_sync_queue` - Sync queue
3. `misa_balances` - Balance snapshots
4. `misa_account_mapping` - Chart of accounts

### Data Flow
SLMS Statement → Sync Queue → MISA API → Update SLMS
