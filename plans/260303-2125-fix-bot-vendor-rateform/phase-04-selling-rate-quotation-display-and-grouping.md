# Phase 4: Selling Rate Quotation Display and Grouping

## Context Links
- Rate dropdown display: `frontend/src/App.jsx` (lines 253-256)
- Quotation search API: `backend/app/api/jobs.py` (lines 2027-2054)
- fetchQuotationsForService: `frontend/src/App.jsx` (lines 496-509)

## Overview
- **Priority**: P2 (UX clarity)
- **Status**: pending
- **Description**: Selling rate dropdown shows `"MEIKO | N/A | 1,000,000 VND"` which is unclear. Need to show service type, route info, and group by customer.

## Key Insights
- Backend already returns `service_type_code`, `origin`, `destination`, `customer_name` in search results
- Frontend display template at line 255 shows: `{origin->destination || vendor/customer_name} | {vehicle_type || N/A} | {price}`
- For selling rates: vehicle_type is often null -> shows "N/A"
- Need better label: show `service_type_code` when vehicle_type is null, and show route when available
- Grouping by customer: use `<optgroup>` in the select element

## Requirements
### Functional
- Selling rate label shows: `customer_name | route_or_service | price`
- When route exists: show `origin->destination`
- When no route: show `service_type_code` or unit
- Group selling rates by customer name in dropdown
- Buying rates display unchanged (already shows route/vehicle)

### Non-functional
- Labels concise enough to fit dropdown width

## Related Code Files
- **Modify**: `frontend/src/App.jsx` (lines 252-258, rate dropdown rendering)

## Implementation Steps

### Step 1: Update selling rate display format (line 253-257)

**Current** (line 253-256):
```jsx
{(type === 'buying' ? filteredVendorRates : rates).map(r => (
  <option key={r.rate_id} value={r.rate_id}>
    {r.origin && r.destination ? `${r.origin}->${r.destination}` : r.vendor_name || r.customer_name || 'N/A'} | {r.vehicle_type || 'N/A'} | {formatPriceDisplay(r.price)}
  </option>
))}
```

**New**: Split buying/selling display logic:

```jsx
{type === 'buying' ? (
  // Buying rates: show route/vendor | vehicle | price
  filteredVendorRates.map(r => (
    <option key={r.rate_id} value={r.rate_id}>
      {r.origin && r.destination ? `${r.origin}->${r.destination}` : r.vendor_name || 'N/A'} | {r.vehicle_type || r.unit || 'N/A'} | {formatPriceDisplay(r.price)}
    </option>
  ))
) : (
  // Selling rates: group by customer, show route/service | price
  Object.entries(
    rates.reduce((groups, r) => {
      const key = r.customer_name || 'Khac'
      if (!groups[key]) groups[key] = []
      groups[key].push(r)
      return groups
    }, {})
  ).map(([customerName, customerRates]) => (
    <optgroup key={customerName} label={customerName}>
      {customerRates.map(r => {
        const routeOrService = r.origin && r.destination
          ? `${r.origin}->${r.destination}`
          : r.service_type_code || r.vehicle_type || r.unit || ''
        return (
          <option key={r.rate_id} value={r.rate_id}>
            {routeOrService} | {formatPriceDisplay(r.price)}/{r.unit || 'TRIP'}
          </option>
        )
      })}
    </optgroup>
  ))
)}
```

### Step 2: Ensure backend returns enough data (already done)

The quotation search endpoint at `backend/app/api/jobs.py` lines 2044-2054 already returns:
- `customer_name`
- `origin` (from `origin_province`)
- `destination` (from `destination_province`)
- `service_type_code`
- `unit`
- `vehicle_type`

No backend changes needed.

### Step 3: Handle edge case - empty customer groups

If `customer_name` is null/undefined, rates group under "Khac" (Other). This handles legacy rates without customer assignment.

## Exact Code Changes

### Change at line 253-257 in App.jsx

**old_string** (the entire map block):
```
                {(type === 'buying' ? filteredVendorRates : rates).map(r => (
                  <option key={r.rate_id} value={r.rate_id}>
                    {r.origin && r.destination ? `${r.origin}→${r.destination}` : r.vendor_name || r.customer_name || 'N/A'} | {r.vehicle_type || 'N/A'} | {formatPriceDisplay(r.price)}
                  </option>
                ))}
```

**new_string**:
```
                {type === 'buying' ? (
                  filteredVendorRates.map(r => (
                    <option key={r.rate_id} value={r.rate_id}>
                      {r.origin && r.destination ? `${r.origin}→${r.destination}` : r.vendor_name || 'N/A'} | {r.vehicle_type || r.unit || 'N/A'} | {formatPriceDisplay(r.price)}
                    </option>
                  ))
                ) : (
                  Object.entries(
                    rates.reduce((groups, r) => {
                      const key = r.customer_name || 'Khác'
                      if (!groups[key]) groups[key] = []
                      groups[key].push(r)
                      return groups
                    }, {})
                  ).map(([custName, custRates]) => (
                    <optgroup key={custName} label={custName}>
                      {custRates.map(r => {
                        const info = r.origin && r.destination
                          ? `${r.origin}→${r.destination}`
                          : r.service_type_code || r.vehicle_type || ''
                        return (
                          <option key={r.rate_id} value={r.rate_id}>
                            {info} | {formatPriceDisplay(r.price)}/{r.unit || 'TRIP'}
                          </option>
                        )
                      })}
                    </optgroup>
                  ))
                )}
```

## Todo List
- [ ] Replace combined rate map with split buying/selling display
- [ ] Add optgroup grouping by customer_name for selling rates
- [ ] Show route or service_type_code in selling rate label
- [ ] Show price/unit format for selling rates
- [ ] Test: selling rates grouped by customer
- [ ] Test: buying rates display unchanged
- [ ] Test: rates with no customer_name grouped under "Khac"
- [ ] Test: rates with route show origin->destination

## Success Criteria
- Selling rates show clear, informative labels instead of "N/A | N/A"
- Selling rates grouped by customer in dropdown
- Buying rates display unchanged
- Rate selection still works correctly (onChange handler unmodified)

## Risk Assessment
- **Low**: Display-only change, no data model changes
- **optgroup + onChange**: Standard HTML select behavior. The `onChange` handler reads `e.target.value` which works with optgroups.

## Security Considerations
- N/A (display-only frontend change)
