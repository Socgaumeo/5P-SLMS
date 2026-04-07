# Phase 2: Create Customer KK Record

## Overview
- **Priority**: HIGH (must exist before import)
- **Status**: Pending
- New customer KK (K+K Fashion) needs a record in `customers` table

## Key Insights from Excel
- Full name: CÔNG TY TNHH K+K FASHION
- Tax code: 0500577571
- Address: Cụm Công nghiệp Ngọc Hồi, Thanh Trì, Hà Nội
- 3 service sheets: TRUCKING VẢI, TRUCKING CHỐNG ẨM, SEA DOM

## Implementation Steps
1. Query max customer_id to find next available ID
2. INSERT into `customers` with short_name='KK', full details
3. Update CUSTOMER_MAP in script with new ID

## SQL
```sql
INSERT INTO customers (short_name, full_name, tax_code, address, status)
VALUES ('KK', 'CÔNG TY TNHH K+K FASHION', '0500577571',
        'Cụm Công nghiệp Ngọc Hồi, Thanh Trì, Hà Nội', 'ACTIVE')
RETURNING customer_id;
```

## Success Criteria
- [ ] Customer KK exists in DB with valid customer_id
- [ ] CUSTOMER_MAP updated in import script
