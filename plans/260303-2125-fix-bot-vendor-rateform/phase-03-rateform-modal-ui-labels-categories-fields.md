# Phase 3: RateFormModal UI - Labels, Categories, Fields

## Context Links
- RateFormModal: `frontend/src/components/admin/RateFormModal.jsx` (570 lines)
- SERVICE_CATEGORIES: lines 11-37
- Form state: lines 64-104
- handleSubmit payload: lines 164-237
- Route fields (TRUCKING only): lines 323-397
- Notes field (hidden for TRUCKING): lines 545-554
- Sub-route field: lines 348-356

## Overview
- **Priority**: P2 (UI improvements, new fields)
- **Status**: pending
- **Description**: Multiple UI improvements: label rename, show route for all categories, show notes for all, add min_charge fields, add LOADING/INFRA categories, update WAREHOUSE units.

## Key Insights
- Route fields (origin/destination) currently gated by `category === 'TRUCKING'`. Should show for all transport categories.
- Notes hidden for TRUCKING (line 545 `category !== 'TRUCKING'`). Should show for ALL.
- Sub-route detail useful for customs (CD/CO documents), not just trucking.
- `min_charge` can be stored in existing `metadata` JSONB column. No DB migration.
- New categories LOADING and INFRA need to be added to SERVICE_CATEGORIES constant.

## Requirements
### Functional
1. Labels: "Tinh di" -> "Diem di", "Tinh den" -> "Diem den"
2. Route fields (origin/destination) visible for ALL categories
3. Sub-route field visible for ALL categories
4. Notes field visible for ALL categories
5. New min_charge checkbox + min_charge_amount number input
6. WAREHOUSE units: add `KG/DAY`, `/LAN`
7. New category LOADING (Boc xep): units `KG`, `PALLET`, `CONT`, `TRIP`
8. New category INFRA (CSHT): units `/CONT`, `/SHIPMENT`
9. handleSubmit sends notes, min_charge, min_charge_amount in payload

### Non-functional
- No DB migration needed (use metadata JSONB)
- Keep form clean and intuitive

## Related Code Files
- **Modify**: `frontend/src/components/admin/RateFormModal.jsx`

## Implementation Steps

### Step 1: Update SERVICE_CATEGORIES (lines 11-37)

```javascript
const SERVICE_CATEGORIES = {
  TRUCKING: {
    label: 'Van chuyen',
    fields: ['route', 'vehicle_type', 'rate_type', 'temperature_range'],
    units: ['TRIP', 'CONT', 'KG', 'CBM', 'PALLET', 'SHIPMENT', 'SET', 'UNIT'],
  },
  CONTAINER: {
    label: 'Nang ha Container',
    fields: ['container_type', 'cargo_type'],
    units: ['CONT', 'UNIT', 'TRIP'],
  },
  CUSTOMS: {
    label: 'Thu tuc Hai quan',
    fields: ['customs_type'],
    units: ['TO KHAI', 'BO', 'SHIPMENT', 'SET', 'BILL'],
  },
  PACKING: {
    label: 'Dong goi / Chang buoc',
    fields: ['packing_type'],
    units: ['PALLET', 'CBM', 'UNIT', 'CONT'],
  },
  WAREHOUSE: {
    label: 'Kho bai',
    fields: ['warehouse_service'],
    units: ['CBM/DAY', 'PALLET/DAY', 'KG/DAY', '/LAN', 'UNIT'],  // Added KG/DAY, /LAN
  },
  LOADING: {
    label: 'Boc xep',
    fields: [],
    units: ['KG', 'PALLET', 'CONT', 'TRIP'],  // No /DAY
  },
  INFRA: {
    label: 'CSHT',
    fields: [],
    units: ['/CONT', '/SHIPMENT'],
  },
}
```

### Step 2: Add min_charge to form state (after line 103)

Add to formData initial state:
```javascript
// Min charge
min_charge: false,
min_charge_amount: '',
```

### Step 3: Update editData population (line 120-127)

Add min_charge fields from editData metadata:
```javascript
useEffect(() => {
  if (editData) {
    const meta = editData.metadata || {}
    setFormData({
      ...formData,
      ...editData,
      sub_route: editData.notes || '',
      min_charge: meta.min_charge || false,
      min_charge_amount: meta.min_charge_amount || '',
    })
  }
}, [editData])
```

### Step 4: Rename labels (lines 327, 337)

**Line 327**: `<label>Tinh di *</label>` -> `<label>Diem di</label>` (remove required, not all categories need it)
**Line 337**: `<label>Tinh den *</label>` -> `<label>Diem den</label>` (remove required)

### Step 5: Move route fields outside TRUCKING gate (lines 322-346)

**Current**: Entire route section wrapped in `{category === 'TRUCKING' && ( ... )}`

**Change**: Move the origin/destination row OUTSIDE the TRUCKING conditional. Keep it as a standalone section that shows for ALL categories.

Remove the outer `{category === 'TRUCKING' && (` and its closing `)}` that wraps lines 323-397. Instead, split into:

**A) Route fields (show for ALL categories):**
```jsx
{/* Route fields - all categories */}
<div className="form-row">
  <div className="form-group">
    <label>Diem di</label>
    <input
      type="text"
      value={formData.origin_province}
      onChange={(e) => setFormData({ ...formData, origin_province: e.target.value })}
      placeholder="VD: Ha Noi, Cang Cat Lai..."
    />
  </div>
  <div className="form-group">
    <label>Diem den</label>
    <input
      type="text"
      value={formData.destination_province}
      onChange={(e) => setFormData({ ...formData, destination_province: e.target.value })}
      placeholder="VD: Bac Ninh, KCN VSIP..."
    />
  </div>
</div>

{/* Sub-route detail - all categories */}
<div className="form-group">
  <label>Chi tiet (Sub-route)</label>
  <input
    type="text"
    value={formData.sub_route}
    onChange={(e) => setFormData({ ...formData, sub_route: e.target.value })}
    placeholder="VD: Noi Bai -> KCN Thang Long"
  />
</div>
```

**B) TRUCKING-specific fields (vehicle, rate_type, temperature) stay gated:**
```jsx
{category === 'TRUCKING' && (
  <>
    <div className="form-row">
      <div className="form-group">
        <label>Loai xe *</label>
        {/* ... vehicle_type select ... */}
      </div>
      <div className="form-group">
        <label>Loai hang</label>
        {/* ... rate_type select ... */}
      </div>
    </div>
    {formData.rate_type === 'REFRIGERATED' && (
      <div className="form-group">
        <label>Khoang nhiet do</label>
        {/* ... temperature_range input ... */}
      </div>
    )}
  </>
)}
```

### Step 6: Add min_charge fields (after pricing row, before date fields)

Insert after the pricing `form-row` (after line 522):

```jsx
{/* Min charge */}
<div className="form-row" style={{ alignItems: 'center' }}>
  <div className="form-group" style={{ flex: '0 0 auto' }}>
    <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
      <input
        type="checkbox"
        checked={formData.min_charge}
        onChange={(e) => setFormData({ ...formData, min_charge: e.target.checked })}
      />
      Co muc thu toi thieu (Min charge)
    </label>
  </div>
  {formData.min_charge && (
    <div className="form-group">
      <label>Muc toi thieu</label>
      <input
        type="number"
        value={formData.min_charge_amount}
        onChange={(e) => setFormData({ ...formData, min_charge_amount: e.target.value })}
        placeholder="VD: 500000"
      />
    </div>
  )}
</div>
```

### Step 7: Show Notes for ALL categories (line 545)

**Current**: `{category !== 'TRUCKING' && (`
**Change**: Remove the conditional entirely. Always show notes.

```jsx
{/* Notes - always visible */}
<div className="form-group">
  <label>Ghi chu</label>
  <textarea
    value={formData.notes}
    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
    placeholder="Ghi chu them..."
  />
</div>
```

### Step 8: Update handleSubmit payload (lines 164-200)

**A) Always include origin/destination (not just TRUCKING):**

Move origin_province and destination_province OUT of the `if (category === 'TRUCKING')` block into the common payload:

```javascript
const payload = {
  price: parseFloat(formData.price),
  currency: formData.currency,
  unit: formData.unit,
  effective_date: formData.effective_date || null,
  expiry_date: formData.expiry_date || null,
  notes: formData.sub_route || formData.notes,
  is_active: formData.is_active,
  service_type_code: formData.service_type_code || null,
  // Route fields - common to all categories
  origin_province: formData.origin_province || null,
  destination_province: formData.destination_province || null,
}
```

**B) Add min_charge to metadata for all categories:**

After building category-specific metadata, merge min_charge:

```javascript
// Add min_charge to metadata if enabled
if (formData.min_charge && formData.min_charge_amount) {
  payload.metadata = {
    ...(payload.metadata || {}),
    min_charge: true,
    min_charge_amount: parseFloat(formData.min_charge_amount),
  }
}
```

**C) Handle LOADING and INFRA categories (no special metadata needed):**

Add to the category switch:
```javascript
} else if (category === 'LOADING') {
  // No extra metadata needed
} else if (category === 'INFRA') {
  // No extra metadata needed
}
```

**D) Update TRUCKING block - remove origin/destination (already in common):**

```javascript
if (category === 'TRUCKING') {
  payload.vehicle_type = formData.vehicle_type
  payload.rate_type = formData.rate_type
  if (formData.rate_type === 'REFRIGERATED') {
    payload.temperature_range = formData.temperature_range
  }
}
```

## Todo List
- [ ] Add LOADING and INFRA to SERVICE_CATEGORIES
- [ ] Add KG/DAY and /LAN to WAREHOUSE units
- [ ] Add min_charge + min_charge_amount to formData state
- [ ] Update editData useEffect to read min_charge from metadata
- [ ] Rename labels: "Tinh di" -> "Diem di", "Tinh den" -> "Diem den"
- [ ] Move route fields (origin/dest/sub_route) outside TRUCKING conditional
- [ ] Add min_charge checkbox + amount input to form UI
- [ ] Remove `category !== 'TRUCKING'` gate on Notes field
- [ ] Update handleSubmit: origin/dest in common payload, min_charge in metadata
- [ ] Test: route fields visible for CUSTOMS, CONTAINER, PACKING, etc.
- [ ] Test: notes visible for TRUCKING
- [ ] Test: min_charge toggle and amount saved in metadata
- [ ] Test: new LOADING and INFRA categories appear and have correct units

## Success Criteria
- All labels use "Diem di/den" instead of "Tinh di/den"
- Route fields visible for every category
- Notes visible for every category
- Min charge checkbox works and saves to metadata
- LOADING and INFRA categories available with correct units
- WAREHOUSE has KG/DAY and /LAN units

## Risk Assessment
- **Low**: UI-only changes, no DB migration
- **Metadata JSONB**: Already used for customs_type, packing_type. Adding min_charge follows same pattern.
- **New categories**: Need corresponding `master_service_types` rows in DB with `category = 'LOADING'` or `'INFRA'`. If missing, the optgroup will be empty but won't break.

## Security Considerations
- N/A (frontend form changes only, backend already validates via RateCreate model)
