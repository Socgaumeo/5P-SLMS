# Phase 4: Per-Service Vendor and Quotation Selection

## Context Links

- [App.jsx - JobDetailModal services section](/Users/bear1108/Documents/GitHub/5P-SLMS/frontend/src/App.jsx) - Line 281-524
- [Jobs API - assign endpoint](/Users/bear1108/Documents/GitHub/5P-SLMS/backend/app/api/jobs.py) - Line 250-399
- [Data Service](/Users/bear1108/Documents/GitHub/5P-SLMS/backend/app/services/data_service.py)

## Overview

**Priority:** P2
**Status:** pending
**Effort:** 3h

**Problem:** Currently services within a job share vendor assignment. User needs:
1. Different vendors/handlers for different services within same job
2. Different buying/selling quotations per service for accurate costing

**Example:** Job with trucking + packing services:
- Trucking: Vendor A at 800k/trip
- Packing: Vendor B at 200k/package

## Key Insights

- JobDetailModal already shows per-service vendor assignment (line 292-400)
- `handleAssign` function updates single service (line 121-149)
- job_services table has vendor_id column per service
- Missing: quotation selection per service
- Missing: display of buying/selling rates

## Requirements

### Functional
1. Each service can have independent vendor selection
2. Each service can have buying quotation (cost) selection
3. Each service can have selling quotation (revenue) selection
4. Show profit margin per service
5. Calculate total job profit

### Non-Functional
1. Load quotations lazily when editing service
2. Cache quotations to avoid repeated API calls
3. Support offline quotation entry (manual price input)

## Architecture

```
JobDetailModal
└── Services List
    └── Service Card
        ├── Service Type Badge
        ├── Status Badge
        ├── Vendor Selector (existing)
        ├── Buying Quotation Selector (NEW)
        │   ├── Dropdown of vendor_rates matching route/vehicle
        │   └── Manual price input option
        ├── Selling Quotation Selector (NEW)
        │   ├── Dropdown of customer_rates matching route/vehicle
        │   └── Manual price input option
        └── Profit Display (NEW)
            ├── Revenue: X VND
            ├── Cost: Y VND
            └── Margin: Z%
```

## Database Schema

```sql
-- Existing table: job_services
-- Add columns for quotation tracking:

ALTER TABLE job_services ADD COLUMN IF NOT EXISTS
    buying_rate_id INTEGER REFERENCES vendor_rates(rate_id),
    buying_price DECIMAL(15,2),
    selling_rate_id INTEGER REFERENCES customer_rates(rate_id),
    selling_price DECIMAL(15,2);

-- Or use existing job_costs table for this
```

## Related Code Files

### Files to Modify
- `frontend/src/App.jsx`
  - Add QuotationSelector component
  - Add quotation fields to service card in edit mode
  - Add profit calculation display

- `backend/app/api/jobs.py`
  - Extend `/api/services/{svc_id}/assign` to accept quotation data
  - Add endpoint to fetch matching quotations

- `backend/app/api/admin.py`
  - Ensure quotation APIs return necessary data

### Files to Create
- None (extending existing)

## Implementation Steps

### Step 1: Add Quotation State to Service Card

```jsx
// In JobDetailModal, update state initialization:

const [quotations, setQuotations] = useState({}) // {svc_id: {buying: [], selling: []}}

// Fetch quotations when entering edit mode
useEffect(() => {
  if (editMode && services.length > 0) {
    services.forEach(svc => {
      fetchQuotationsForService(svc)
    })
  }
}, [editMode, services])

const fetchQuotationsForService = async (svc) => {
  try {
    // Fetch matching vendor rates (buying)
    const buyingRes = await fetch(
      `${API_URL}/api/quotations/search?` +
      `service_type=${svc.service_type_code}` +
      `&origin=${encodeURIComponent(svc.origin_address || '')}` +
      `&destination=${encodeURIComponent(svc.dest_address || '')}`
    )
    const buyingData = await buyingRes.json()

    // Fetch matching customer rates (selling)
    const sellingRes = await fetch(
      `${API_URL}/api/quotations/search?` +
      `type=selling` +
      `&customer_id=${job.customer_id}` +
      `&service_type=${svc.service_type_code}`
    )
    const sellingData = await sellingRes.json()

    setQuotations(prev => ({
      ...prev,
      [svc.svc_id]: {
        buying: buyingData.rates || [],
        selling: sellingData.rates || []
      }
    }))
  } catch (e) {
    console.error('Failed to fetch quotations:', e)
  }
}
```

### Step 2: Add Quotation Selector Component

```jsx
// Add before JobDetailModal function

function QuotationSelector({ type, rates, selectedRateId, selectedPrice, onSelect, disabled }) {
  const [manualMode, setManualMode] = useState(false)
  const [manualPrice, setManualPrice] = useState(selectedPrice || '')

  const label = type === 'buying' ? 'Gia mua' : 'Gia ban'
  const icon = type === 'buying' ? '📥' : '📤'

  return (
    <div className="quotation-selector">
      <label>{icon} {label}:</label>

      {manualMode ? (
        <div className="manual-price-input">
          <input
            type="number"
            value={manualPrice}
            onChange={e => setManualPrice(e.target.value)}
            placeholder="Nhap gia (VND)"
            disabled={disabled}
          />
          <button
            onClick={() => {
              onSelect(null, parseFloat(manualPrice) || 0)
              setManualMode(false)
            }}
            disabled={disabled}
          >
            OK
          </button>
          <button onClick={() => setManualMode(false)}>Huy</button>
        </div>
      ) : (
        <div className="rate-dropdown-row">
          <select
            value={selectedRateId || ''}
            onChange={e => {
              const rateId = e.target.value
              const rate = rates.find(r => r.rate_id == rateId)
              onSelect(rateId ? parseInt(rateId) : null, rate?.price || 0)
            }}
            disabled={disabled}
          >
            <option value="">-- Chon bao gia --</option>
            {rates.map(r => (
              <option key={r.rate_id} value={r.rate_id}>
                {r.vendor_name || r.customer_name} - {r.vehicle_type} - {formatPrice(r.price)}
              </option>
            ))}
          </select>
          <button
            className="btn-manual"
            onClick={() => setManualMode(true)}
            disabled={disabled}
            title="Nhap gia thu cong"
          >
            ✏️
          </button>
        </div>
      )}

      {selectedPrice > 0 && (
        <span className="selected-price">{formatPrice(selectedPrice)}</span>
      )}
    </div>
  )
}

function formatPrice(price) {
  if (!price) return '0 VND'
  return new Intl.NumberFormat('vi-VN').format(price) + ' VND'
}
```

### Step 3: Add Quotation Fields to Service Card

```jsx
// In service card (around line 426), after vehicle edit section:

{/* Quotation Section - Only in edit mode */}
{editMode && (
  <div className="quotation-section" style={{
    marginTop: '12px',
    padding: '12px',
    background: 'rgba(16, 185, 129, 0.05)',
    borderRadius: '8px',
    border: '1px dashed var(--border)'
  }}>
    <strong style={{ display: 'block', marginBottom: '10px' }}>
      💰 Bao gia dich vu:
    </strong>

    {/* Buying Rate (Cost) */}
    <QuotationSelector
      type="buying"
      rates={quotations[svc.svc_id]?.buying || []}
      selectedRateId={svc.buying_rate_id}
      selectedPrice={svc.buying_price}
      onSelect={(rateId, price) => {
        setServices(prev => prev.map(s =>
          s.svc_id === svc.svc_id
            ? { ...s, buying_rate_id: rateId, buying_price: price }
            : s
        ))
      }}
      disabled={saving}
    />

    {/* Selling Rate (Revenue) */}
    <QuotationSelector
      type="selling"
      rates={quotations[svc.svc_id]?.selling || []}
      selectedRateId={svc.selling_rate_id}
      selectedPrice={svc.selling_price}
      onSelect={(rateId, price) => {
        setServices(prev => prev.map(s =>
          s.svc_id === svc.svc_id
            ? { ...s, selling_rate_id: rateId, selling_price: price }
            : s
        ))
      }}
      disabled={saving}
    />

    {/* Profit Display */}
    {(svc.buying_price > 0 || svc.selling_price > 0) && (
      <div className="profit-display" style={{
        marginTop: '10px',
        padding: '8px',
        background: 'rgba(16, 185, 129, 0.1)',
        borderRadius: '6px',
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: '13px'
      }}>
        <span>Doanh thu: {formatPrice(svc.selling_price)}</span>
        <span>Chi phi: {formatPrice(svc.buying_price)}</span>
        <span style={{
          fontWeight: 'bold',
          color: (svc.selling_price - svc.buying_price) >= 0 ? '#10B981' : '#EF4444'
        }}>
          Loi nhuan: {formatPrice(svc.selling_price - svc.buying_price)}
          ({((svc.selling_price - svc.buying_price) / (svc.buying_price || 1) * 100).toFixed(1)}%)
        </span>
      </div>
    )}

    <button
      type="button"
      onClick={() => handleSaveQuotations(svc)}
      disabled={saving}
      style={{
        marginTop: '10px',
        padding: '8px 16px',
        background: 'var(--success)',
        color: 'white',
        border: 'none',
        borderRadius: '6px',
        cursor: 'pointer'
      }}
    >
      {saving ? '⏳' : '✓'} Luu bao gia
    </button>
  </div>
)}
```

### Step 4: Add Save Quotations Handler

```jsx
// In JobDetailModal:

const handleSaveQuotations = async (svc) => {
  setSaving(true)
  try {
    const res = await fetch(`${API_URL}/api/services/${svc.svc_id}/quotations`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        buying_rate_id: svc.buying_rate_id,
        buying_price: svc.buying_price,
        selling_rate_id: svc.selling_rate_id,
        selling_price: svc.selling_price
      })
    })
    const result = await res.json()
    if (!result.success) {
      alert(result.message || 'Khong the luu bao gia')
    }
  } catch (e) {
    console.error('Save quotations error:', e)
    alert('Loi khi luu bao gia')
  } finally {
    setSaving(false)
  }
}
```

### Step 5: Backend - Add Quotation Search Endpoint

```python
# In jobs.py or create new quotations.py:

@router.get("/quotations/search")
async def search_quotations(
    type: str = "buying",  # buying or selling
    service_type: Optional[str] = None,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    customer_id: Optional[int] = None,
    vendor_id: Optional[int] = None
):
    """
    Search for matching quotations based on service parameters
    """
    try:
        client = get_supabase()

        if type == "buying":
            # Search vendor_rates
            query = client.table('vendor_rates').select(
                '*, vendors(short_name, company_name)'
            ).eq('is_active', True)

            if service_type:
                query = query.eq('service_type', service_type)
            if vendor_id:
                query = query.eq('vendor_id', vendor_id)
            # Could add route matching here

            result = query.order('price').limit(20).execute()

            rates = []
            for r in result.data:
                vendor = r.pop('vendors', {}) or {}
                rates.append({
                    'rate_id': r['rate_id'],
                    'vendor_id': r['vendor_id'],
                    'vendor_name': vendor.get('short_name') or vendor.get('company_name'),
                    'price': r['price'],
                    'vehicle_type': r.get('vehicle_type'),
                    'origin': r.get('origin_province'),
                    'destination': r.get('destination_province'),
                    'unit': r.get('unit', 'TRIP')
                })

        else:
            # Search customer_rates
            query = client.table('customer_rates').select(
                '*, customers(short_name, customer_code)'
            ).eq('is_active', True)

            if customer_id:
                query = query.eq('customer_id', customer_id)
            if service_type:
                query = query.eq('service_type', service_type)

            result = query.order('price', desc=True).limit(20).execute()

            rates = []
            for r in result.data:
                customer = r.pop('customers', {}) or {}
                rates.append({
                    'rate_id': r['rate_id'],
                    'customer_id': r['customer_id'],
                    'customer_name': customer.get('short_name') or customer.get('customer_code'),
                    'price': r['price'],
                    'vehicle_type': r.get('vehicle_type'),
                    'origin': r.get('origin_province'),
                    'destination': r.get('destination_province'),
                    'unit': r.get('unit', 'TRIP')
                })

        return {"rates": rates}

    except Exception as e:
        logger.error(f"Error searching quotations: {e}")
        return {"rates": [], "error": str(e)}
```

### Step 6: Backend - Add Service Quotation Update Endpoint

```python
# In jobs.py:

class ServiceQuotationRequest(BaseModel):
    buying_rate_id: Optional[int] = None
    buying_price: Optional[float] = None
    selling_rate_id: Optional[int] = None
    selling_price: Optional[float] = None


@router.put("/services/{svc_id}/quotations")
async def update_service_quotations(svc_id: int, request: ServiceQuotationRequest):
    """
    Update buying/selling quotations for a service
    """
    try:
        client = get_supabase()

        # Verify service exists
        svc_result = client.table('job_services').select(
            'svc_id, job_id'
        ).eq('svc_id', svc_id).limit(1).execute()

        if not svc_result.data:
            raise HTTPException(404, f"Service {svc_id} not found")

        # Update service with quotation info
        # Store in service_details JSONB or dedicated columns
        svc = svc_result.data[0]

        # Get current service_details
        details_result = client.table('job_services').select(
            'service_details'
        ).eq('svc_id', svc_id).limit(1).execute()

        current_details = details_result.data[0].get('service_details') or {}
        if isinstance(current_details, str):
            current_details = json.loads(current_details)

        # Merge quotation data
        current_details['buying_rate_id'] = request.buying_rate_id
        current_details['buying_price'] = request.buying_price
        current_details['selling_rate_id'] = request.selling_rate_id
        current_details['selling_price'] = request.selling_price

        # Calculate profit
        if request.selling_price and request.buying_price:
            current_details['profit'] = request.selling_price - request.buying_price
            current_details['margin_pct'] = (
                (request.selling_price - request.buying_price) / request.buying_price * 100
                if request.buying_price > 0 else 0
            )

        # Update
        client.table('job_services').update({
            'service_details': current_details,
            'updated_at': datetime.now().isoformat()
        }).eq('svc_id', svc_id).execute()

        # Also update/create job_costs record for reporting
        job_id = svc['job_id']
        # ... (optional: maintain job_costs table)

        return {
            "success": True,
            "svc_id": svc_id,
            "profit": current_details.get('profit'),
            "margin_pct": current_details.get('margin_pct')
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating quotations: {e}")
        return {"success": False, "message": str(e)}
```

## Todo List

- [ ] Add quotations state management in JobDetailModal
- [ ] Create fetchQuotationsForService function
- [ ] Create QuotationSelector component
- [ ] Add quotation section to service card in edit mode
- [ ] Add handleSaveQuotations function
- [ ] Add formatPrice helper function
- [ ] Add GET `/api/quotations/search` endpoint
- [ ] Add PUT `/api/services/{svc_id}/quotations` endpoint
- [ ] Update job_services table or service_details for quotation storage
- [ ] Add CSS styles for quotation section
- [ ] Test buying quotation selection
- [ ] Test selling quotation selection
- [ ] Test profit calculation display
- [ ] Test manual price entry

## Success Criteria

- [ ] Each service shows independent quotation selectors
- [ ] Buying rates dropdown shows vendor rates
- [ ] Selling rates dropdown shows customer rates
- [ ] Manual price entry works for custom quotes
- [ ] Profit and margin calculated correctly
- [ ] Quotations saved per service, not per job
- [ ] Total job profit sums all service profits

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Missing quotations for route/vehicle | Allow manual price entry |
| Performance with many quotations | Lazy load, cache, limit results |
| Data inconsistency | Store both rate_id and price for audit |

## Security Considerations

- Validate rate ownership (vendor/customer)
- Log price changes for audit
- Prevent negative margins alert (optional)
