// frontend/src/components/admin/RateFormModal.jsx
/**
 * Modal form for adding/editing buying and selling rates.
 * Supports multiple service types: trucking, customs, lift on/off, packing, etc.
 */

import { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Service type categories for different rate structures
const SERVICE_CATEGORIES = {
  TRUCKING: {
    label: 'Vận chuyển',
    fields: ['route', 'vehicle_type', 'rate_type', 'temperature_range'],
    units: ['TRIP', 'KG', 'CBM'],
  },
  CONTAINER: {
    label: 'Nâng hạ Container',
    fields: ['container_type', 'cargo_type'],
    units: ['CONT', 'UNIT'],
  },
  CUSTOMS: {
    label: 'Thủ tục Hải quan',
    fields: ['customs_type'],
    units: ['SHIPMENT', 'BILL', 'SET'],
  },
  PACKING: {
    label: 'Đóng gói / Chằng buộc',
    fields: ['packing_type'],
    units: ['PALLET', 'CBM', 'UNIT', 'CONT'],
  },
  WAREHOUSE: {
    label: 'Kho bãi',
    fields: ['warehouse_service'],
    units: ['CBM/DAY', 'PALLET/DAY', 'UNIT'],
  },
}

// Vehicle types for trucking
const VEHICLE_TYPES = ['1.25T', '1.5T', '2.5T', '3.5T', '5T', '7T', '8T', '10T', '13T', '15T', '20T']

// Container types
const CONTAINER_TYPES = ['20DC', '40DC', '40HC', '20RF', '40RF', '20OT', '40OT', '20FR', '40FR']

// Rate types
const RATE_TYPES = [
  { value: 'STANDARD', label: 'Thường' },
  { value: 'REFRIGERATED', label: 'Đông lạnh' },
]

export default function RateFormModal({
  isOpen,
  onClose,
  onSave,
  rateType = 'buying', // 'buying' or 'selling'
  editData = null,
}) {
  const [loading, setLoading] = useState(false)
  const [serviceTypes, setServiceTypes] = useState([])
  const [vendors, setVendors] = useState([])
  const [customers, setCustomers] = useState([])

  // Form state
  const [formData, setFormData] = useState({
    // Common fields
    service_type_code: '',
    price: '',
    currency: 'VND',
    unit: 'TRIP',
    effective_date: new Date().toISOString().split('T')[0],
    expiry_date: '',
    notes: '',
    is_active: true,

    // For buying rates
    vendor_id: '',

    // For selling rates
    customer_id: '',

    // Trucking specific
    origin_province: '',
    destination_province: '',
    sub_route: '', // stored in notes field
    vehicle_type: '',
    rate_type: 'STANDARD',
    temperature_range: '',

    // Container specific
    container_type: '',
    cargo_type: '', // 'CONTAINER' or 'CARGO'

    // Conditions
    conditions: '',

    // Customs specific
    customs_type: '',

    // Packing specific
    packing_type: '',

    // Warehouse specific
    warehouse_service: '',
  })

  // Fetch reference data
  useEffect(() => {
    if (isOpen) {
      fetchServiceTypes()
      if (rateType === 'buying') {
        fetchVendors()
      } else {
        fetchCustomers()
      }
    }
  }, [isOpen, rateType])

  // Populate form when editing
  useEffect(() => {
    if (editData) {
      setFormData({
        ...formData,
        ...editData,
        sub_route: editData.notes || '',
      })
    }
  }, [editData])

  const fetchServiceTypes = async () => {
    try {
      const res = await fetch(`${API_URL}/api/admin/service-types`)
      const json = await res.json()
      setServiceTypes(json.data || [])
    } catch (err) {
      console.error('Failed to fetch service types:', err)
    }
  }

  const fetchVendors = async () => {
    try {
      const res = await fetch(`${API_URL}/api/admin/vendors`)
      const json = await res.json()
      setVendors(json.data || [])
    } catch (err) {
      console.error('Failed to fetch vendors:', err)
    }
  }

  const fetchCustomers = async () => {
    try {
      const res = await fetch(`${API_URL}/api/admin/customers`)
      const json = await res.json()
      setCustomers(json.data || [])
    } catch (err) {
      console.error('Failed to fetch customers:', err)
    }
  }

  const getSelectedServiceCategory = () => {
    const service = serviceTypes.find(s => s.service_code === formData.service_type_code)
    return service?.category || ''
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      // Prepare payload
      const payload = {
        price: parseFloat(formData.price),
        currency: formData.currency,
        unit: formData.unit,
        effective_date: formData.effective_date || null,
        expiry_date: formData.expiry_date || null,
        notes: formData.sub_route || formData.notes,
        is_active: formData.is_active,
        service_type_code: formData.service_type_code || null,
      }

      // Add service-specific fields
      const category = getSelectedServiceCategory()
      if (category === 'TRUCKING') {
        payload.origin_province = formData.origin_province
        payload.destination_province = formData.destination_province
        payload.vehicle_type = formData.vehicle_type
        payload.rate_type = formData.rate_type
        if (formData.rate_type === 'REFRIGERATED') {
          payload.temperature_range = formData.temperature_range
        }
      } else if (category === 'CONTAINER') {
        payload.vehicle_type = formData.container_type
        payload.metadata = { container_type: formData.container_type, cargo_type: formData.cargo_type }
      } else if (category === 'CUSTOMS') {
        payload.metadata = { customs_type: formData.customs_type }
      } else if (category === 'PACKING') {
        payload.metadata = { packing_type: formData.packing_type }
      } else if (category === 'WAREHOUSE') {
        payload.metadata = { warehouse_service: formData.warehouse_service }
      }

      // Add vendor/customer
      if (rateType === 'buying') {
        payload.vendor_id = parseInt(formData.vendor_id)
      } else {
        payload.customer_id = parseInt(formData.customer_id)
      }

      // API call
      const endpoint = rateType === 'buying'
        ? `${API_URL}/api/admin/buying-rates`
        : `${API_URL}/api/admin/selling-rates`

      const method = editData ? 'PUT' : 'POST'
      const url = editData
        ? `${endpoint}/${editData.id || editData.rate_id}`
        : endpoint

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const error = await res.json()
        throw new Error(error.detail || 'Failed to save rate')
      }

      onSave && onSave()
      onClose()
    } catch (err) {
      console.error('Save failed:', err)
      alert('Lỗi: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  const category = getSelectedServiceCategory()

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content wide" onClick={(e) => e.stopPropagation()}>
        <h3>
          {editData ? 'Sửa' : 'Thêm'} báo giá {rateType === 'buying' ? 'mua vào' : 'bán ra'}
        </h3>

        <form onSubmit={handleSubmit}>
          {/* Vendor/Customer Selection */}
          <div className="form-row">
            {rateType === 'buying' ? (
              <div className="form-group">
                <label>Nhà cung cấp *</label>
                <select
                  value={formData.vendor_id}
                  onChange={(e) => setFormData({ ...formData, vendor_id: e.target.value })}
                  required
                >
                  <option value="">-- Chọn NCC --</option>
                  {vendors.map((v) => (
                    <option key={v.vendor_id} value={v.vendor_id}>
                      {v.short_name || v.vendor_name} ({v.vendor_code})
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div className="form-group">
                <label>Khách hàng *</label>
                <select
                  value={formData.customer_id}
                  onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                  required
                >
                  <option value="">-- Chọn KH --</option>
                  {customers.map((c) => (
                    <option key={c.customer_id} value={c.customer_id}>
                      {c.short_name || c.company_name} ({c.customer_code})
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="form-group">
              <label>Loại dịch vụ *</label>
              <select
                value={formData.service_type_code}
                onChange={(e) => setFormData({
                  ...formData,
                  service_type_code: e.target.value,
                  // Reset category-specific fields
                  vehicle_type: '',
                  container_type: '',
                })}
                required
              >
                <option value="">-- Chọn dịch vụ --</option>
                {Object.entries(
                  serviceTypes.reduce((acc, s) => {
                    const cat = s.category || 'OTHER'
                    if (!acc[cat]) acc[cat] = []
                    acc[cat].push(s)
                    return acc
                  }, {})
                ).map(([cat, services]) => (
                  <optgroup key={cat} label={SERVICE_CATEGORIES[cat]?.label || cat}>
                    {services.map((s) => (
                      <option key={s.service_code} value={s.service_code}>
                        {s.name_vi}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>
          </div>

          {/* Trucking specific fields */}
          {category === 'TRUCKING' && (
            <>
              <div className="form-row">
                <div className="form-group">
                  <label>Tỉnh đi *</label>
                  <input
                    type="text"
                    value={formData.origin_province}
                    onChange={(e) => setFormData({ ...formData, origin_province: e.target.value })}
                    placeholder="VD: Hà Nội"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Tỉnh đến *</label>
                  <input
                    type="text"
                    value={formData.destination_province}
                    onChange={(e) => setFormData({ ...formData, destination_province: e.target.value })}
                    placeholder="VD: Bắc Ninh"
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Chi tiết điểm giao (Sub-route)</label>
                <input
                  type="text"
                  value={formData.sub_route}
                  onChange={(e) => setFormData({ ...formData, sub_route: e.target.value })}
                  placeholder="VD: Nội Bài -> KCN Thăng Long"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Loại xe *</label>
                  <select
                    value={formData.vehicle_type}
                    onChange={(e) => setFormData({ ...formData, vehicle_type: e.target.value })}
                    required
                  >
                    <option value="">-- Chọn --</option>
                    {VEHICLE_TYPES.map((v) => (
                      <option key={v} value={v}>{v}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Loại hàng</label>
                  <select
                    value={formData.rate_type}
                    onChange={(e) => setFormData({ ...formData, rate_type: e.target.value })}
                  >
                    {RATE_TYPES.map((r) => (
                      <option key={r.value} value={r.value}>{r.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              {formData.rate_type === 'REFRIGERATED' && (
                <div className="form-group">
                  <label>Khoảng nhiệt độ</label>
                  <input
                    type="text"
                    value={formData.temperature_range}
                    onChange={(e) => setFormData({ ...formData, temperature_range: e.target.value })}
                    placeholder="VD: Từ Âm 10 đến 0 độ"
                  />
                </div>
              )}
            </>
          )}

          {/* Container specific fields */}
          {category === 'CONTAINER' && (
            <div className="form-row">
              <div className="form-group">
                <label>Loại container</label>
                <select
                  value={formData.container_type}
                  onChange={(e) => setFormData({ ...formData, container_type: e.target.value })}
                >
                  <option value="">-- Chọn --</option>
                  {CONTAINER_TYPES.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Loại hàng</label>
                <select
                  value={formData.cargo_type}
                  onChange={(e) => setFormData({ ...formData, cargo_type: e.target.value })}
                >
                  <option value="CONTAINER">Container</option>
                  <option value="CARGO">Kiện hàng (Cargo)</option>
                </select>
              </div>
            </div>
          )}

          {/* Customs specific fields */}
          {category === 'CUSTOMS' && (
            <div className="form-row">
              <div className="form-group">
                <label>Loại thủ tục *</label>
                <select
                  value={formData.customs_type}
                  onChange={(e) => setFormData({ ...formData, customs_type: e.target.value })}
                  required
                >
                  <option value="">-- Chọn --</option>
                  <option value="IMPORT">Nhập khẩu</option>
                  <option value="EXPORT">Xuất khẩu</option>
                  <option value="TRANSIT">Quá cảnh</option>
                  <option value="ONSPOT">Tại chỗ</option>
                </select>
              </div>
            </div>
          )}

          {/* Packing specific fields */}
          {category === 'PACKING' && (
            <div className="form-row">
              <div className="form-group">
                <label>Loại đóng gói</label>
                <select
                  value={formData.packing_type}
                  onChange={(e) => setFormData({ ...formData, packing_type: e.target.value })}
                >
                  <option value="">-- Chọn --</option>
                  <option value="WOODEN_CRATE">Đóng thùng gỗ</option>
                  <option value="SHRINK_WRAP">Quấn màng co</option>
                  <option value="VACUUM">Hút chân không</option>
                  <option value="FUMIGATION">Xông trùng</option>
                  <option value="LASHING">Chằng buộc</option>
                  <option value="PALLETIZE">Đóng pallet</option>
                </select>
              </div>
            </div>
          )}

          {/* Warehouse specific fields */}
          {category === 'WAREHOUSE' && (
            <div className="form-row">
              <div className="form-group">
                <label>Loại dịch vụ kho</label>
                <select
                  value={formData.warehouse_service}
                  onChange={(e) => setFormData({ ...formData, warehouse_service: e.target.value })}
                >
                  <option value="">-- Chọn --</option>
                  <option value="STORAGE">Lưu kho</option>
                  <option value="HANDLING">Xếp dỡ</option>
                  <option value="VAS">Dịch vụ gia tăng (VAS)</option>
                </select>
              </div>
            </div>
          )}

          {/* Pricing fields - common */}
          <div className="form-row">
            <div className="form-group">
              <label>Đơn giá *</label>
              <input
                type="number"
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                placeholder="1000000"
                required
              />
            </div>

            <div className="form-group">
              <label>Tiền tệ</label>
              <select
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
              >
                <option value="VND">VND</option>
                <option value="USD">USD</option>
              </select>
            </div>

            <div className="form-group">
              <label>Đơn vị tính</label>
              <select
                value={formData.unit}
                onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
              >
                {(SERVICE_CATEGORIES[category]?.units || ['TRIP', 'UNIT']).map((u) => (
                  <option key={u} value={u}>{u}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Date fields */}
          <div className="form-row">
            <div className="form-group">
              <label>Ngày hiệu lực</label>
              <input
                type="date"
                value={formData.effective_date}
                onChange={(e) => setFormData({ ...formData, effective_date: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Ngày hết hạn</label>
              <input
                type="date"
                value={formData.expiry_date}
                onChange={(e) => setFormData({ ...formData, expiry_date: e.target.value })}
              />
            </div>
          </div>

          {/* Notes */}
          {category !== 'TRUCKING' && (
            <div className="form-group">
              <label>Ghi chú</label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="Ghi chú thêm..."
              />
            </div>
          )}

          {/* Actions */}
          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={loading}>
              Hủy
            </button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Đang lưu...' : 'Lưu'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
