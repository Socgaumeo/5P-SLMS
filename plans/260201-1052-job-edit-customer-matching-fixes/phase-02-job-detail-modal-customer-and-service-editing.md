# Phase 2: Job Detail Modal Customer and Service Editing

## Context Links

- [App.jsx - JobDetailModal](/Users/bear1108/Documents/GitHub/5P-SLMS/frontend/src/App.jsx) - Line 78-538
- [Jobs API](/Users/bear1108/Documents/GitHub/5P-SLMS/backend/app/api/jobs.py)
- [Data Service](/Users/bear1108/Documents/GitHub/5P-SLMS/backend/app/services/data_service.py)

## Overview

**Priority:** P1
**Status:** pending
**Effort:** 3h

**Problem:** JobDetailModal currently allows editing vendor/driver assignment per service, but lacks:
1. Ability to change customer for the job
2. Ability to add new services to existing job

## Key Insights

- JobDetailModal already has edit mode toggle (line 81, 217-219)
- Customer display at line 257-258 is read-only
- Services list at line 281-524 allows vendor/employee assignment
- Backend `jobs.py` has `/update` endpoint but limited to status and notes
- Need new API endpoints for customer change and service addition

## Requirements

### Functional
1. Edit customer in JobDetailModal (with confirmation)
2. Add new service to existing job
3. Validate customer change doesn't break billing
4. Log all changes for audit

### Non-Functional
1. Keep modal responsive - lazy load customer list
2. Prevent accidental customer changes (require confirmation)
3. Support optimistic UI updates

## Architecture

```
JobDetailModal (Edit Mode)
       │
       ├─► Customer Section
       │   ├─ Current: [LKVMB - Loc Khi Viet Mien Bac]
       │   ├─ [Change Customer] button
       │   └─ CustomerSelector dropdown (lazy loaded)
       │
       └─► Services Section
           ├─ Existing services list
           ├─ [+ Add Service] button
           └─ AddServiceForm (service type, details)
```

## Related Code Files

### Files to Modify
- `frontend/src/App.jsx`
  - Add customer editing section in JobDetailModal
  - Add "Add Service" form/button
  - Handle customer change API call

- `backend/app/api/jobs.py`
  - Add `PUT /api/jobs/{job_id}/customer` endpoint
  - Add `POST /api/jobs/{job_id}/services` endpoint

### Files to Create
- None (extending existing components)

## Implementation Steps

### Step 1: Add Customer Edit Section to JobDetailModal

```jsx
// In App.jsx, inside JobDetailModal, after line 258

{/* Customer Edit Section */}
{editMode ? (
  <div className="form-group">
    <label>Khach hang:</label>
    <div className="customer-edit-row">
      <CustomerSelector
        currentCustomerId={job.customer_id}
        onSelect={handleCustomerChange}
        disabled={saving}
      />
      <span className="current-label">
        Hien tai: {job.customer_code} - {job.customer_name}
      </span>
    </div>
  </div>
) : (
  <div className="detail-item">
    <span className="detail-label">Khach hang:</span>
    <span className="detail-value">{job.customer || job.customer_name || job.customer_code}</span>
  </div>
)}
```

### Step 2: Create CustomerSelector Component

```jsx
// Add before JobDetailModal function

function CustomerSelector({ currentCustomerId, onSelect, disabled }) {
  const [customers, setCustomers] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)

  useEffect(() => {
    if (showDropdown && customers.length === 0) {
      setLoading(true)
      fetch(`${API_URL}/api/customers`)
        .then(r => r.json())
        .then(d => setCustomers(d.customers || []))
        .finally(() => setLoading(false))
    }
  }, [showDropdown])

  const filtered = customers.filter(c =>
    !search ||
    (c.customer_code || '').toLowerCase().includes(search.toLowerCase()) ||
    (c.short_name || '').toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="customer-selector">
      <input
        type="text"
        placeholder="Tim khach hang..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        onFocus={() => setShowDropdown(true)}
        disabled={disabled}
      />
      {showDropdown && (
        <div className="dropdown-list">
          {loading ? (
            <div className="loading">Dang tai...</div>
          ) : filtered.length > 0 ? (
            filtered.slice(0, 10).map(c => (
              <div
                key={c.customer_id}
                className={`dropdown-item ${c.customer_id === currentCustomerId ? 'selected' : ''}`}
                onClick={() => {
                  onSelect(c)
                  setShowDropdown(false)
                  setSearch('')
                }}
              >
                <strong>{c.customer_code}</strong> - {c.short_name}
              </div>
            ))
          ) : (
            <div className="no-results">Khong tim thay</div>
          )}
        </div>
      )}
    </div>
  )
}
```

### Step 3: Add Customer Change Handler

```jsx
// Inside JobDetailModal, add handler

const handleCustomerChange = async (newCustomer) => {
  if (!confirm(`Doi khach hang tu "${job.customer_code}" sang "${newCustomer.customer_code}"?`)) {
    return
  }

  setSaving(true)
  try {
    const res = await fetch(`${API_URL}/api/jobs/${job.job_id}/customer`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_id: newCustomer.customer_id,
        customer_code: newCustomer.customer_code
      })
    })
    const result = await res.json()
    if (result.success) {
      // Update local state
      job.customer_id = newCustomer.customer_id
      job.customer_code = newCustomer.customer_code
      job.customer_name = newCustomer.short_name
      onUpdate && onUpdate()
    } else {
      alert(result.message || 'Khong the doi khach hang')
    }
  } catch (e) {
    console.error('Change customer error:', e)
    alert('Loi khi doi khach hang')
  } finally {
    setSaving(false)
  }
}
```

### Step 4: Add Service Form

```jsx
// Inside JobDetailModal, after services list (around line 527)

{editMode && (
  <div className="add-service-section">
    <button
      className="btn-add-service"
      onClick={() => setShowAddService(!showAddService)}
    >
      + Them dich vu
    </button>

    {showAddService && (
      <div className="add-service-form">
        <div className="form-row">
          <label>Loai dich vu:</label>
          <select
            value={newService.service_type}
            onChange={e => setNewService({...newService, service_type: e.target.value})}
          >
            <option value="TRUCKING_SHORT">Trucking Noi vung</option>
            <option value="TRUCKING_LONG">Trucking Lien tinh</option>
            <option value="WHS_STORAGE">Luu kho</option>
            <option value="WHS_HANDLE">Boc xep</option>
            <option value="SVC_PACK">Dong goi</option>
          </select>
        </div>
        <div className="form-row">
          <label>Ngay thuc hien:</label>
          <input
            type="date"
            value={newService.scheduled_date}
            onChange={e => setNewService({...newService, scheduled_date: e.target.value})}
          />
        </div>
        <div className="form-row">
          <label>Diem di:</label>
          <input
            type="text"
            value={newService.origin_address}
            onChange={e => setNewService({...newService, origin_address: e.target.value})}
            placeholder="Dia chi lay hang"
          />
        </div>
        <div className="form-row">
          <label>Diem den:</label>
          <input
            type="text"
            value={newService.dest_address}
            onChange={e => setNewService({...newService, dest_address: e.target.value})}
            placeholder="Dia chi giao hang"
          />
        </div>
        <button
          className="btn-primary"
          onClick={handleAddService}
          disabled={saving}
        >
          {saving ? 'Dang them...' : 'Them dich vu'}
        </button>
      </div>
    )}
  </div>
)}
```

### Step 5: Backend - Add Customer Change Endpoint

```python
# In jobs.py, add new endpoint

class CustomerChangeRequest(BaseModel):
    customer_id: int
    customer_code: str
    reason: Optional[str] = None


@router.put("/{job_id}/customer")
async def change_job_customer(job_id: int, request: CustomerChangeRequest):
    """
    Change customer for a job
    Requires confirmation - logs change for audit
    """
    try:
        client = get_supabase()

        # Get current job
        job_result = client.table('jobs').select(
            'job_id, job_no, customer_id, status_code'
        ).eq('job_id', job_id).limit(1).execute()

        if not job_result.data:
            raise HTTPException(404, f"Job {job_id} not found")

        job = job_result.data[0]
        old_customer_id = job['customer_id']

        # Prevent change if job is completed/cancelled
        if job['status_code'] in ['COMPLETED', 'CANCELLED']:
            return {
                "success": False,
                "message": f"Khong the doi KH cho job da {job['status_code']}"
            }

        # Update job
        client.table('jobs').update({
            'customer_id': request.customer_id,
            'updated_at': datetime.now().isoformat()
        }).eq('job_id', job_id).execute()

        # Log change for audit
        logger.info(
            f"Job {job['job_no']} customer changed: "
            f"{old_customer_id} -> {request.customer_id} "
            f"(reason: {request.reason or 'not specified'})"
        )

        return {
            "success": True,
            "job_id": job_id,
            "message": f"Da doi khach hang thanh cong"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing customer: {e}")
        return {"success": False, "message": str(e)}
```

### Step 6: Backend - Add Service Endpoint

```python
# In jobs.py, add new endpoint

class AddServiceRequest(BaseModel):
    service_type_code: str
    scheduled_date: Optional[str] = None
    scheduled_time: Optional[str] = None
    origin_address: Optional[str] = None
    dest_address: Optional[str] = None
    cargo_type: Optional[str] = None
    package_quantity: Optional[int] = None
    package_unit: Optional[str] = None
    special_requirements: Optional[str] = None


@router.post("/{job_id}/services")
async def add_job_service(job_id: int, request: AddServiceRequest):
    """
    Add new service to existing job
    """
    try:
        client = get_supabase()

        # Verify job exists
        job_result = client.table('jobs').select(
            'job_id, job_no, status_code'
        ).eq('job_id', job_id).limit(1).execute()

        if not job_result.data:
            raise HTTPException(404, f"Job {job_id} not found")

        job = job_result.data[0]

        # Prevent adding to completed/cancelled jobs
        if job['status_code'] in ['COMPLETED', 'CANCELLED']:
            return {
                "success": False,
                "message": f"Khong the them dich vu cho job da {job['status_code']}"
            }

        # Parse dates
        scheduled_date = parse_date(request.scheduled_date) if request.scheduled_date else None
        scheduled_time = parse_time(request.scheduled_time) if request.scheduled_time else None

        # Insert new service
        service_result = client.table('job_services').insert({
            'job_id': job_id,
            'service_type_code': request.service_type_code,
            'scheduled_date': scheduled_date.isoformat() if scheduled_date else None,
            'scheduled_time': str(scheduled_time) if scheduled_time else None,
            'origin_address': request.origin_address,
            'dest_address': request.dest_address,
            'cargo_type': request.cargo_type,
            'package_quantity': request.package_quantity,
            'package_unit': request.package_unit,
            'special_requirements': request.special_requirements,
            'status_code': 'PENDING'
        }).execute()

        new_service = service_result.data[0]

        logger.info(f"Added service {new_service['svc_id']} to job {job['job_no']}")

        return {
            "success": True,
            "svc_id": new_service['svc_id'],
            "message": f"Da them dich vu {request.service_type_code}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding service: {e}")
        return {"success": False, "message": str(e)}
```

## Todo List

- [ ] Add CustomerSelector component to App.jsx
- [ ] Add customer edit section in JobDetailModal
- [ ] Add handleCustomerChange function
- [ ] Add state for showAddService, newService
- [ ] Add AddServiceForm in JobDetailModal
- [ ] Add handleAddService function
- [ ] Add PUT `/api/jobs/{job_id}/customer` endpoint
- [ ] Add POST `/api/jobs/{job_id}/services` endpoint
- [ ] Add CSS styles for new components
- [ ] Test customer change flow
- [ ] Test add service flow

## Success Criteria

- [ ] Can search and select new customer in edit mode
- [ ] Customer change requires confirmation dialog
- [ ] Can add new service with type, date, addresses
- [ ] New service appears in services list after adding
- [ ] Cannot edit completed/cancelled jobs
- [ ] Changes are logged for audit

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Billing impact from customer change | Add warning about billing implications |
| Orphaned cost records | Keep old customer_id in job_costs for reconciliation |
| UI state sync issues | Refresh full job data after changes |

## Security Considerations

- Customer change logged with timestamp and user
- API validates job ownership before changes
- Prevent SQL injection in search queries
