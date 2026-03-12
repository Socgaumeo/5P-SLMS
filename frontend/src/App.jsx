import { useState, useEffect } from 'react'
import './App.css'
import ChatWindow from './components/chat/ChatWindow'
import AdminPanel from './components/admin/AdminPanel'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import LoginPage from './pages/LoginPage'
import SearchBox from './components/SearchBox'
import { authFetch, API_URL } from './utils/auth-fetch'

// Theme colors from 5P Vietnam logo
const theme = {
  primary: '#2563EB',
  primaryDark: '#1E40AF',
  primaryLight: '#3B82F6',
  accent: '#F59E0B',
  accentRed: '#EF4444',
  success: '#10B981',
  warning: '#F59E0B',
  bgLight: '#F8FAFC',
  bgDark: '#1E293B',
  text: '#1E293B',
  textSecondary: '#64748B',
  border: '#E2E8F0',
}

// Status Badge Component
const StatusBadge = ({ status }) => {
  const styles = {
    // Common
    PENDING: { bg: '#FEF3C7', color: '#D97706', label: 'Chờ xử lý' },
    CONFIRMED: { bg: '#DBEAFE', color: '#2563EB', label: 'Đã xác nhận' },
    CANCELLED: { bg: '#FEE2E2', color: '#DC2626', label: 'Đã hủy' },
    // Transport-specific
    DISPATCHED: { bg: '#E0E7FF', color: '#4F46E5', label: 'Đã điều xe' },
    IN_TRANSIT: { bg: '#DBEAFE', color: '#2563EB', label: 'Đang vận chuyển' },
    // General
    ASSIGNED: { bg: '#E0E7FF', color: '#4F46E5', label: 'Đã phân công' },
    IN_PROGRESS: { bg: '#FEF3C7', color: '#D97706', label: 'Đang thực hiện' },
    COMPLETED: { bg: '#D1FAE5', color: '#059669', label: 'Hoàn thành' },
    // Warehouse-specific
    WHS_RECEIVED: { bg: '#DBEAFE', color: '#2563EB', label: 'Đã nhập kho' },
    WHS_PROCESSING: { bg: '#FEF3C7', color: '#D97706', label: 'Đang xử lý' },
    WHS_RELEASED: { bg: '#D1FAE5', color: '#059669', label: 'Đã xuất kho' },
    // Customs-specific
    CUS_SUBMITTED: { bg: '#E0E7FF', color: '#4F46E5', label: 'Đã nộp hồ sơ' },
    CUS_PROCESSING: { bg: '#FEF3C7', color: '#D97706', label: 'Đang xử lý' },
    CUS_APPROVED: { bg: '#D1FAE5', color: '#059669', label: 'Đã thông quan' },
  }
  const style = styles[status] || styles.PENDING

  return (
    <span className="status-badge" style={{ backgroundColor: style.bg, color: style.color }}>
      {style.label}
    </span>
  )
}

// Stats Card Component
const StatsCard = ({ icon, label, value, color }) => (
  <div className="stats-card">
    <div className="stats-card-header">
      <div className="stats-icon" style={{ backgroundColor: `${color}15` }}>
        <span style={{ color }}>{icon}</span>
      </div>
    </div>
    <div className="stats-value">{value}</div>
    <div className="stats-label">{label}</div>
  </div>
)

// Nav Item Component
const NavItem = ({ icon, label, active, onClick, badge }) => (
  <button className={`nav-item ${active ? 'active' : ''}`} onClick={onClick}>
    <span className="nav-icon">{icon}</span>
    <span className="nav-label">{label}</span>
    {badge && <span className="nav-badge">{badge}</span>}
  </button>
)

// Floating AI Button
const FloatingAIButton = ({ onClick, hasNotification }) => (
  <button className="floating-ai-btn" onClick={onClick}>
    <span className="ai-icon">🤖</span>
    <span className="ai-label">5P AI</span>
    {hasNotification && <span className="notification-badge">●</span>}
  </button>
)

// ========================================
// QUOTATION SELECTOR COMPONENT
// ========================================
// Remove Vietnamese diacritics for search matching
const removeDiacritics = (str) => str?.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D') || ''

function QuotationSelector({ type, rates, standardRates = [], selectedRateId, selectedPrice, quantity = 1, onQuantityChange, onSelect, disabled, vendorId }) {
  const [manualMode, setManualMode] = useState(false)
  const [manualUnitPrice, setManualUnitPrice] = useState('')
  const [manualUnit, setManualUnit] = useState('TRIP')
  const [costSource, setCostSource] = useState('vendor') // 'vendor' or 'standard'
  const [rateSearch, setRateSearch] = useState('')

  const label = type === 'buying' ? 'Chi phí' : 'Doanh Thu'
  const icon = type === 'buying' ? '📥' : '📤'
  const color = type === 'buying' ? '#EF4444' : '#10B981'

  const UNITS = ['TRIP', 'CONT', 'KG', 'CBM', 'PALLET', 'SHIPMENT', 'SET', 'UNIT', 'TỜ KHAI', 'BỘ']

  const formatPriceDisplay = (price) => {
    if (!price) return '0 VND'
    return new Intl.NumberFormat('vi-VN').format(price) + ' VND'
  }

  const handleManualSubmit = () => {
    const unitPrice = parseFloat(manualUnitPrice) || 0
    const totalPrice = unitPrice * quantity
    onSelect(null, totalPrice, { unitPrice, unit: manualUnit })
    setManualMode(false)
  }

  // Client-side search filter (diacritic-insensitive)
  const searchFilter = (items) => {
    if (!rateSearch.trim()) return items
    const terms = removeDiacritics(rateSearch.toLowerCase()).split(/[\s,]+/).filter(Boolean)
    return items.filter(r => {
      const haystack = removeDiacritics(`${r.notes || ''} ${r.origin || ''} ${r.destination || ''} ${r.vehicle_type || ''} ${r.vendor_name || ''} ${r.customer_name || ''}`).toLowerCase()
      return terms.every(term => haystack.includes(term))
    })
  }
  // Filter vendor rates by selected vendor + search text
  const filteredVendorRates = searchFilter(vendorId ? rates.filter(r => r.vendor_id === vendorId) : rates)
  const filteredSellingRates = searchFilter(rates)

  // For buying type, show cost source options
  const showCostSourceToggle = type === 'buying' && standardRates.length > 0

  // Quantity input component (reusable)
  const QuantityInput = () => (
    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
      <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>SL:</span>
      <input
        type="number"
        min="1"
        value={quantity}
        onChange={e => onQuantityChange && onQuantityChange(parseInt(e.target.value) || 1)}
        disabled={disabled}
        style={{ padding: '4px 6px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '11px', width: '50px', textAlign: 'center' }}
      />
    </div>
  )

  return (
    <div style={{ marginBottom: '10px' }}>
      <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
        {icon} {label}:
      </label>

      {/* Cost source toggle for buying type */}
      {showCostSourceToggle && !manualMode && (
        <div style={{ display: 'flex', gap: '4px', marginBottom: '6px' }}>
          <button
            type="button"
            onClick={() => setCostSource('standard')}
            style={{
              padding: '4px 8px',
              fontSize: '10px',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              background: costSource === 'standard' ? 'var(--primary)' : 'var(--border)',
              color: costSource === 'standard' ? 'white' : 'var(--text-primary)'
            }}
          >
            📋 Định mức
          </button>
          <button
            type="button"
            onClick={() => setCostSource('vendor')}
            style={{
              padding: '4px 8px',
              fontSize: '10px',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              background: costSource === 'vendor' ? 'var(--primary)' : 'var(--border)',
              color: costSource === 'vendor' ? 'white' : 'var(--text-primary)'
            }}
          >
            🏢 Nhà cung cấp
          </button>
        </div>
      )}

      {manualMode ? (
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            type="number"
            value={manualUnitPrice}
            onChange={e => setManualUnitPrice(e.target.value)}
            placeholder="Đơn giá"
            disabled={disabled}
            style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--border)', fontSize: '12px', width: '100px' }}
          />
          <select
            value={manualUnit}
            onChange={e => setManualUnit(e.target.value)}
            disabled={disabled}
            style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--border)', fontSize: '12px', width: '80px' }}
          >
            {UNITS.map(u => <option key={u} value={u}>{u}</option>)}
          </select>
          <QuantityInput />
          {manualUnitPrice && quantity > 0 && (
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
              = {formatPriceDisplay(parseFloat(manualUnitPrice) * quantity)}
            </span>
          )}
          <button
            onClick={handleManualSubmit}
            disabled={disabled}
            style={{ padding: '6px 10px', background: 'var(--success)', color: 'white', border: 'none', borderRadius: '4px', fontSize: '11px', cursor: 'pointer' }}
          >
            OK
          </button>
          <button
            onClick={() => setManualMode(false)}
            style={{ padding: '6px 10px', background: 'var(--border)', border: 'none', borderRadius: '4px', fontSize: '11px', cursor: 'pointer' }}
          >
            Hủy
          </button>
        </div>
      ) : (
        <div>
          {/* Search input for filtering rates (client-side with diacritic support) */}
          {costSource !== 'standard' && (
            <div style={{ marginBottom: '4px' }}>
              <input
                type="text"
                placeholder={`🔍 Tìm tuyến, xe... (VD: Binh Duong, 5T)`}
                value={rateSearch}
                onChange={(e) => setRateSearch(e.target.value)}
                style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--border)', fontSize: '12px', width: '100%' }}
              />
            </div>
          )}
          {/* Row 1: Select dropdown - full width */}
          <div style={{ marginBottom: '6px' }}>
            {type === 'buying' && costSource === 'standard' && standardRates.length > 0 ? (
              <select
                value={selectedRateId || ''}
                onChange={e => {
                  const itemId = e.target.value
                  const item = standardRates.find(r => r.cost_item_id == itemId)
                  const totalPrice = (item?.default_price || 0) * quantity
                  onSelect(itemId ? parseInt(itemId) : null, totalPrice, { source: 'standard', unitPrice: item?.default_price, unit: item?.unit })
                }}
                disabled={disabled}
                style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--border)', fontSize: '12px', width: '100%' }}
              >
                <option value="">-- Chọn định mức --</option>
              {standardRates.map(r => (
                <option key={r.cost_item_id} value={r.cost_item_id}>
                  {r.name_vi} - {formatPriceDisplay(r.default_price)}/{r.unit}
                </option>
              ))}
              </select>
            ) : (
              <select
                value={selectedRateId || ''}
                onChange={e => {
                  const rateId = e.target.value
                  const rate = (type === 'buying' ? filteredVendorRates : filteredSellingRates).find(r => r.rate_id == rateId)
                  const totalPrice = (rate?.price || 0) * quantity
                  onSelect(rateId ? parseInt(rateId) : null, totalPrice, { source: 'vendor', unitPrice: rate?.price })
                }}
                disabled={disabled}
                style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--border)', fontSize: '12px', width: '100%' }}
              >
                <option value="">-- Chọn báo giá --</option>
                {type === 'buying' ? (
                  filteredVendorRates.map(r => {
                    const route = r.notes || (r.origin && r.destination ? `${r.origin}→${r.destination}` : r.vendor_name || 'N/A')
                    return (
                      <option key={r.rate_id} value={r.rate_id}>
                        {route} | {r.vehicle_type || r.unit || 'N/A'} | {formatPriceDisplay(r.price)}
                      </option>
                    )
                  })
                ) : (
                  Object.entries(
                    filteredSellingRates.reduce((groups, r) => {
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
              </select>
            )}
          </div>
          {/* Row 2: Quantity, pencil button, price */}
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <QuantityInput />
            <button
              onClick={() => setManualMode(true)}
              disabled={disabled}
              title="Nhập tay"
              style={{ padding: '6px 10px', background: 'var(--border)', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
            >
              ✏️
            </button>
            {selectedPrice > 0 && (
              <span style={{ fontSize: '12px', fontWeight: 'bold', color }}>{formatPriceDisplay(selectedPrice)}</span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ========================================
// JOB DETAIL MODAL (with Edit Mode)
// ========================================
function JobDetailModal({ job, onClose, onUpdate }) {
  const [services, setServices] = useState([])
  const [loading, setLoading] = useState(true)
  const [editMode, setEditMode] = useState(false)
  const [vendors, setVendors] = useState([])
  const [employees, setEmployees] = useState([])
  const [customers, setCustomers] = useState([])
  const [saving, setSaving] = useState(false)
  const [jobStatus, setJobStatus] = useState(job?.status_code || 'PENDING')
  const [jobCustomer, setJobCustomer] = useState({
    id: job?.customer_id,
    code: job?.customer_code,
    name: job?.customer || job?.customer_name
  })
  const [showCustomerSelector, setShowCustomerSelector] = useState(false)
  const [customerSearch, setCustomerSearch] = useState('')
  const [showAddService, setShowAddService] = useState(false)
  const [newService, setNewService] = useState({
    service_type_code: 'TRUCKING_DOM',
    scheduled_date: '',
    origin_address: '',
    dest_address: '',
    vendor_id: '',
    license_plate: '',
    driver_name: '',
    driver_phone: '',
    notes: ''
  })
  // Quotation state for per-service pricing
  const [quotations, setQuotations] = useState({}) // {svc_id: {buying: [], selling: []}}
  const [standardRates, setStandardRates] = useState([]) // Standard cost items from master_cost_items
  const [savedField, setSavedField] = useState(null) // Flash "Saved" indicator: 'vendor-{svc_id}', 'vehicle-{svc_id}'

  // Service type labels for display
  const SERVICE_TYPE_LABELS = {
    // Road Transport
    TRUCKING_DOM: 'Vận tải nội địa',
    BORDER_IMP: 'Nhập khẩu đường bộ',
    // Air Freight
    AIR_IMP: 'Hàng không - Nhập',
    AIR_EXP: 'Hàng không - Xuất',
    // Sea Freight
    SEA_IMP: 'Đường biển - Nhập',
    SEA_EXP: 'Đường biển - Xuất',
    // Warehouse
    WHS_STORAGE: 'Lưu kho',
    WHS_HANDLE: 'Bốc xếp',
    WHS_VAS: 'Dịch vụ gia tăng (VAS)',
    WHS_CSHT: 'Phí cơ sở hạ tầng (CSHT)',
    WHS_THC: 'Phí THC',
    // Customs
    CUS_IMPORT: 'Khai quan Nhập',
    CUS_EXPORT: 'Khai quan Xuất',
    CUS_TRANSIT: 'Quá cảnh',
    CUS_CO: 'Chứng nhận xuất xứ (C/O)',
    CUS_SUPERVISE: 'Giám sát hải quan',
    CUS_INSPECT: 'Kiểm hoá',
    CUS_TRANSFER: 'Chuyển khẩu',
    // Packing
    SVC_PACK: 'Đóng gói',
    SVC_FUMI: 'Hun trùng',
    SVC_VACUUM: 'Hút chân không',
    SVC_SHRINK: 'Màng co',
    SVC_LASHING: 'Chằng buộc',
    SVC_LASHING_TRUCK: 'Chằng buộc (xe tải)',
    SVC_LASHING_CONT: 'Chằng buộc (container)',
    SVC_LASHING_FR: 'Chằng buộc (flat rack)',
    // Container
    LIFT_ON: 'Nâng cont/hàng',
    LIFT_OFF: 'Hạ cont/hàng',
    // Fees/Surcharges
    SVC_WAITING: 'Phí chờ giờ',
    SVC_CANCEL_FEE: 'Phí huỷ chuyến',
    SVC_SURCHARGE: 'Phí phát sinh',
    // Other
    SVC_OTHER: 'Dịch vụ khác',
  }

  // Service type category helpers
  const isTransportService = (serviceType) => {
    return ['TRUCKING_DOM', 'BORDER_IMP', 'AIR_IMP', 'AIR_EXP', 'SEA_IMP', 'SEA_EXP'].includes(serviceType)
  }

  const isWarehouseService = (serviceType) => {
    // WHS_HANDLE (Bốc xếp) uses general statuses - not all are warehouse-related
    return ['WHS_STORAGE', 'WHS_VAS'].includes(serviceType)
  }

  const isCustomsService = (serviceType) => {
    return ['CUS_IMPORT', 'CUS_EXPORT', 'CUS_TRANSIT', 'CUS_CO'].includes(serviceType)
  }

  // Status options based on service type category
  const getStatusOptions = (serviceType) => {
    if (isTransportService(serviceType)) {
      return [
        { value: 'PENDING', label: 'Chờ xử lý' },
        { value: 'DISPATCHED', label: 'Đã điều xe' },
        { value: 'IN_TRANSIT', label: 'Đang vận chuyển' },
        { value: 'COMPLETED', label: 'Hoàn thành' },
      ]
    } else if (isWarehouseService(serviceType)) {
      return [
        { value: 'PENDING', label: 'Chờ xử lý' },
        { value: 'WHS_RECEIVED', label: 'Đã nhập kho' },
        { value: 'WHS_PROCESSING', label: 'Đang xử lý' },
        { value: 'WHS_RELEASED', label: 'Đã xuất kho' },
        { value: 'COMPLETED', label: 'Hoàn thành' },
      ]
    } else if (isCustomsService(serviceType)) {
      return [
        { value: 'PENDING', label: 'Chờ xử lý' },
        { value: 'CUS_SUBMITTED', label: 'Đã nộp hồ sơ' },
        { value: 'CUS_PROCESSING', label: 'Đang xử lý' },
        { value: 'CUS_APPROVED', label: 'Đã thông quan' },
        { value: 'COMPLETED', label: 'Hoàn thành' },
      ]
    } else {
      // Default for packing, lifting, other services
      return [
        { value: 'PENDING', label: 'Chờ xử lý' },
        { value: 'ASSIGNED', label: 'Đã phân công' },
        { value: 'IN_PROGRESS', label: 'Đang thực hiện' },
        { value: 'COMPLETED', label: 'Hoàn thành' },
      ]
    }
  }

  // Default status options for backward compatibility
  const statusOptions = [
    { value: 'PENDING', label: 'Chờ xử lý' },
    { value: 'DISPATCHED', label: 'Đã điều xe' },
    { value: 'IN_TRANSIT', label: 'Đang vận chuyển' },
    { value: 'COMPLETED', label: 'Hoàn thành' },
  ]

  const fetchJobDetails = async () => {
    if (!job?.job_id) return
    try {
      const res = await authFetch(`${API_URL}/api/jobs/${job.job_id}/details`)
      if (res.ok) {
        const data = await res.json()
        // Update jobCustomer from API response (ensures customer_id is always available)
        if (data.job?.customer_id) {
          setJobCustomer({
            id: data.job.customer_id,
            code: data.job.customer_code || jobCustomer.code,
            name: data.job.customer_name || jobCustomer.name
          })
        }
        // Parse vendor_text_input to extract vehicle info, with fallback to drivers table
        const processedServices = (data.services || []).map(svc => {
          // If license_plate is already set but driver_name missing, apply db fallback
          if (svc.license_plate && !svc.driver_name && svc.db_driver_name) {
            return {
              ...svc,
              driver_name: svc.db_driver_name,
              driver_phone: svc.db_driver_phone || svc.driver_phone,
              driver_id_card: svc.db_driver_id_card || svc.driver_id_card,
            }
          }
          if (svc.license_plate) return svc

          // Otherwise, try to parse vendor_text_input
          if (svc.vendor_text_input) {
            try {
              const parsed = JSON.parse(svc.vendor_text_input)
              if (Array.isArray(parsed) && parsed.length > 0) {
                const firstVehicle = parsed[0]
                return {
                  ...svc,
                  license_plate: firstVehicle.license_plate,
                  driver_name: firstVehicle.driver_name || svc.db_driver_name,
                  driver_phone: firstVehicle.driver_phone || svc.db_driver_phone,
                  driver_id_card: firstVehicle.driver_id_card || svc.db_driver_id_card,
                  vehicles: parsed
                }
              } else if (parsed.license_plate) {
                return {
                  ...svc,
                  license_plate: parsed.license_plate,
                  driver_name: parsed.driver_name || svc.db_driver_name,
                  driver_phone: parsed.driver_phone || svc.db_driver_phone,
                  driver_id_card: parsed.driver_id_card || svc.db_driver_id_card,
                  vehicles: [parsed]
                }
              }
            } catch (e) {
              console.log('Could not parse vendor_text_input:', e)
            }
          }
          // Fallback: use driver info from drivers table (linked via driver_id)
          if (svc.db_driver_name || svc.db_driver_license_plate) {
            return {
              ...svc,
              license_plate: svc.db_driver_license_plate || svc.license_plate,
              driver_name: svc.db_driver_name,
              driver_phone: svc.db_driver_phone,
              driver_id_card: svc.db_driver_id_card,
            }
          }
          return svc
        })
        setServices(processedServices)
      }
    } catch (error) {
      console.error('Failed to fetch job details:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchJobDetails()
  }, [job])

  useEffect(() => {
    if (editMode) {
      // Fetch vendors, employees, and customers for dropdowns
      authFetch(`${API_URL}/api/jobs/lookup/vendors`)
        .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
        .then(d => setVendors(d.data || []))
        .catch(err => console.error('Vendor fetch failed:', err))
      authFetch(`${API_URL}/api/jobs/lookup/customers`)
        .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
        .then(d => setCustomers(d.data || []))
        .catch(err => console.error('Customer fetch failed:', err))
      // Fetch standard cost rates
      authFetch(`${API_URL}/api/admin/cost-items`).then(r => r.json()).then(d => setStandardRates(d.data || []))

      // Fetch quotations for each service
      if (services.length > 0) {
        services.forEach(svc => fetchQuotationsForService(svc))
      }
    }
  }, [editMode, services.length, jobCustomer?.id])

  // Fetch matching quotations for a service (filtered by vendor/customer)
  const fetchQuotationsForService = async (svc) => {
    try {
      const svcType = svc.service_type_code || ''

      // Buying rates: filter by vendor
      let buyingUrl = `${API_URL}/api/jobs/quotations/search?type=buying&service_type=${encodeURIComponent(svcType)}`
      if (svc.vendor_id) buyingUrl += `&vendor_id=${svc.vendor_id}`
      const buyingRes = await authFetch(buyingUrl)
      const buyingData = await buyingRes.json()

      // Selling rates: filter by job's customer
      let sellingUrl = `${API_URL}/api/jobs/quotations/search?type=selling&service_type=${encodeURIComponent(svcType)}`
      const custId = jobCustomer?.id || job?.customer_id
      if (custId) sellingUrl += `&customer_id=${custId}`
      const sellingRes = await authFetch(sellingUrl)
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

  // Format price for display
  const formatPrice = (price) => {
    if (!price) return '0 VND'
    return new Intl.NumberFormat('vi-VN').format(price) + ' VND'
  }

  // Save quotations for a service (including extra costs/revenues)
  const handleSaveQuotations = async (svc) => {
    setSaving(true)
    try {
      const res = await authFetch(`${API_URL}/api/jobs/services/${svc.svc_id}/quotations`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          buying_rate_id: svc.buying_rate_id,
          buying_price: svc.buying_price,
          selling_rate_id: svc.selling_rate_id,
          selling_price: svc.selling_price,
          extra_costs: svc.extra_costs || [],
          extra_revenues: svc.extra_revenues || []
        })
      })
      const result = await res.json()
      if (result.success) {
        alert('Đã lưu báo giá thành công!')
        // Re-fetch to ensure UI reflects saved data
        await fetchJobDetails()
      } else {
        alert(result.message || 'Không thể lưu báo giá')
      }
    } catch (e) {
      console.error('Save quotations error:', e)
      alert('Lỗi khi lưu báo giá')
    } finally {
      setSaving(false)
    }
  }

  // Save all quotation changes for all services at once
  const handleSaveAllChanges = async () => {
    setSaving(true)
    try {
      // Save quotations for services that have any pricing data
      const svcsWithPricing = services.filter(svc =>
        svc.buying_price || svc.selling_price ||
        svc.buying_rate_id || svc.selling_rate_id ||
        (svc.extra_costs && svc.extra_costs.length > 0) ||
        (svc.extra_revenues && svc.extra_revenues.length > 0)
      )
      if (svcsWithPricing.length === 0) {
        alert('Chưa có báo giá nào để lưu. Hãy chọn báo giá từ dropdown hoặc nhập tay.')
        return false
      }
      const results = await Promise.all(svcsWithPricing.map(svc =>
        authFetch(`${API_URL}/api/jobs/services/${svc.svc_id}/quotations`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            buying_rate_id: svc.buying_rate_id,
            buying_price: svc.buying_price,
            selling_rate_id: svc.selling_rate_id,
            selling_price: svc.selling_price,
            extra_costs: svc.extra_costs || [],
            extra_revenues: svc.extra_revenues || []
          })
        }).then(r => r.json())
      ))
      const failed = results.filter(r => !r.success)
      if (failed.length > 0) {
        alert(`Lưu thất bại ${failed.length}/${results.length} dịch vụ`)
        return false
      } else {
        alert(`Đã lưu báo giá cho ${results.length} dịch vụ thành công!`)
        // Re-fetch to ensure UI reflects saved data
        await fetchJobDetails()
        return true
      }
    } catch (e) {
      console.error('Save all changes error:', e)
      alert('Lỗi khi lưu: ' + e.message)
      return false
    } finally {
      setSaving(false)
    }
  }

  const handleAssign = async (svc_id, vendor_id, employee_id, vehicleInfo = {}) => {
    setSaving(true)
    try {
      const res = await authFetch(`${API_URL}/api/jobs/services/${svc_id}/assign`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vendor_id, employee_id, ...vehicleInfo })
      })
      const result = await res.json()
      if (result.success) {
        // Update local state and refresh quotations with new vendor
        const updatedSvc = services.find(s => s.svc_id === svc_id)
        const newSvc = {
          ...updatedSvc, vendor_id, employee_id,
          vendor_name: vendors.find(v => v.vendor_id === vendor_id)?.short_name || vendors.find(v => v.vendor_id === vendor_id)?.company_name,
          employee_name: employees.find(e => e.employee_id === employee_id)?.short_name,
          ...vehicleInfo
        }
        setServices(prev => prev.map(s => s.svc_id === svc_id ? newSvc : s))
        // Auto-refresh quotations with updated vendor_id
        fetchQuotationsForService(newSvc)
        // Flash saved indicator
        setSavedField(`vendor-${svc_id}`)
        setTimeout(() => setSavedField(null), 2000)
      } else {
        alert(result.message || 'Không thể cập nhật')
      }
    } catch (error) {
      console.error('Failed to assign:', error)
      alert('Lỗi khi cập nhật')
    } finally {
      setSaving(false)
    }
  }

  const handleUpdateStatus = async (newStatus) => {
    setSaving(true)
    try {
      const res = await authFetch(`${API_URL}/api/jobs/${job.job_id}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status_code: newStatus })
      })
      const result = await res.json()
      if (result.success) {
        setJobStatus(newStatus)
        setServices(prev => prev.map(s => ({ ...s, status_code: newStatus })))
        onUpdate && onUpdate()
      } else {
        alert(result.message || 'Không thể cập nhật trạng thái')
      }
    } catch (e) {
      console.error('Update status error:', e)
      alert('Lỗi khi cập nhật trạng thái')
    } finally {
      setSaving(false)
    }
  }

  const handleCancelJob = async () => {
    if (!confirm(`Bạn có chắc muốn hủy job ${job.job_no}?`)) return

    setSaving(true)
    try {
      const res = await authFetch(`${API_URL}/api/jobs/${job.job_id}/cancel`, { method: 'DELETE' })
      const result = await res.json()
      if (result.success) {
        setJobStatus('CANCELLED')
        setServices(prev => prev.map(s => ({ ...s, status_code: 'CANCELLED' })))
        onUpdate && onUpdate()
        onClose()
      } else {
        alert(result.message || 'Không thể hủy job')
      }
    } catch (e) {
      console.error('Cancel job error:', e)
      alert('Lỗi khi hủy job')
    } finally {
      setSaving(false)
    }
  }

  // Update individual service status
  const handleUpdateServiceStatus = async (svc_id, newStatus) => {
    setSaving(true)
    try {
      const res = await authFetch(`${API_URL}/api/services/${svc_id}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status_code: newStatus })
      })
      const result = await res.json()
      if (result.success) {
        setServices(prev => prev.map(s =>
          s.svc_id === svc_id ? { ...s, status_code: newStatus } : s
        ))
      } else {
        alert(result.message || 'Không thể cập nhật trạng thái')
      }
    } catch (e) {
      console.error('Update service status error:', e)
      alert('Lỗi khi cập nhật trạng thái')
    } finally {
      setSaving(false)
    }
  }

  // Delete service from job
  const handleDeleteService = async (svc_id) => {
    if (!confirm('Bạn có chắc muốn xóa dịch vụ này?')) return

    setSaving(true)
    try {
      const res = await authFetch(`${API_URL}/api/services/${svc_id}`, { method: 'DELETE' })
      const result = await res.json()
      if (result.success) {
        setServices(prev => prev.filter(s => s.svc_id !== svc_id))
      } else {
        alert(result.message || 'Không thể xóa dịch vụ')
      }
    } catch (e) {
      console.error('Delete service error:', e)
      alert('Lỗi khi xóa dịch vụ')
    } finally {
      setSaving(false)
    }
  }

  // Update service notes
  const handleUpdateServiceNotes = async (svc_id, notes) => {
    setSaving(true)
    try {
      const res = await authFetch(`${API_URL}/api/jobs/services/${svc_id}/notes`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: notes || '' })
      })
      const result = await res.json()
      if (result.success) {
        // Already updated in local state via onChange
      } else {
        alert(result.message || 'Không thể lưu ghi chú')
      }
    } catch (e) {
      console.error('Update notes error:', e)
      alert('Lỗi khi lưu ghi chú')
    } finally {
      setSaving(false)
    }
  }

  const handleCustomerChange = async (newCustomer) => {
    if (!confirm(`Đổi khách hàng từ "${jobCustomer.code || jobCustomer.name}" sang "${newCustomer.customer_code}"?`)) {
      return
    }

    setSaving(true)
    try {
      const res = await authFetch(`${API_URL}/api/jobs/${job.job_id}/customer`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_id: newCustomer.customer_id,
          customer_code: newCustomer.customer_code
        })
      })
      const result = await res.json()
      if (result.success) {
        setJobCustomer({
          id: newCustomer.customer_id,
          code: newCustomer.customer_code,
          name: newCustomer.short_name || newCustomer.company_name
        })
        setShowCustomerSelector(false)
        setCustomerSearch('')
        onUpdate && onUpdate()
      } else {
        alert(result.message || 'Không thể đổi khách hàng')
      }
    } catch (e) {
      console.error('Change customer error:', e)
      alert('Lỗi khi đổi khách hàng')
    } finally {
      setSaving(false)
    }
  }

  const handleAddService = async () => {
    if (!newService.service_type_code) {
      alert('Vui lòng chọn loại dịch vụ')
      return
    }

    setSaving(true)
    try {
      const res = await authFetch(`${API_URL}/api/jobs/${job.job_id}/services`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newService)
      })
      const result = await res.json()
      if (result.success) {
        // Find vendor name if vendor_id is set
        const vendor = vendors.find(v => v.vendor_id == newService.vendor_id)
        // Add new service to list
        setServices(prev => [...prev, {
          svc_id: result.svc_id,
          service_type_code: newService.service_type_code,
          scheduled_date: newService.scheduled_date,
          origin_address: newService.origin_address,
          dest_address: newService.dest_address,
          vendor_id: newService.vendor_id ? parseInt(newService.vendor_id) : null,
          vendor_name: vendor?.vendor_name || vendor?.short_name || null,
          license_plate: newService.license_plate || null,
          driver_name: newService.driver_name || null,
          driver_phone: newService.driver_phone || null,
          notes: newService.notes || null,
          status_code: 'PENDING'
        }])
        setShowAddService(false)
        setNewService({
          service_type_code: 'TRUCKING_DOM',
          scheduled_date: '',
          origin_address: '',
          dest_address: '',
          vendor_id: '',
          license_plate: '',
          driver_name: '',
          driver_phone: '',
          notes: ''
        })
        onUpdate && onUpdate()
      } else {
        alert(result.message || 'Không thể thêm dịch vụ')
      }
    } catch (e) {
      console.error('Add service error:', e)
      alert('Lỗi khi thêm dịch vụ')
    } finally {
      setSaving(false)
    }
  }

  const filteredCustomers = customers.filter(c =>
    !customerSearch ||
    (c.customer_code || '').toLowerCase().includes(customerSearch.toLowerCase()) ||
    (c.short_name || '').toLowerCase().includes(customerSearch.toLowerCase()) ||
    (c.company_name || '').toLowerCase().includes(customerSearch.toLowerCase())
  )

  if (!job) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content large" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2 className="modal-title">📋 {job.job_no}</h2>
            <p className="modal-subtitle">{job.customer || job.customer_name || job.customer_code}</p>
          </div>
          <StatusBadge status={jobStatus} />
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {/* Job Info */}
          <div className="detail-section">
            <div className="section-header">
              <h3>Thông tin Job</h3>
              <button className={`btn-edit ${editMode ? 'active' : ''}`} onClick={() => setEditMode(!editMode)}>
                {editMode ? '🔒 Xong' : '✏️ Sửa'}
              </button>
            </div>

            {/* Edit mode actions: Update Status & Cancel */}
            {editMode && jobStatus !== 'CANCELLED' && (
              <div className="edit-actions" style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Cập nhật trạng thái:</label>
                  <select
                    value={jobStatus}
                    onChange={(e) => handleUpdateStatus(e.target.value)}
                    disabled={saving}
                    style={{ padding: '8px 12px', borderRadius: '6px', border: '1px solid var(--border)' }}
                  >
                    {getStatusOptions(services[0]?.service_type_code || job?.service_type || 'TRUCKING_DOM').map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
                <button
                  onClick={handleCancelJob}
                  disabled={saving}
                  style={{
                    padding: '8px 16px',
                    background: '#EF4444',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '13px'
                  }}
                >
                  ❌ Hủy Job
                </button>
              </div>
            )}
            <div className="detail-grid">
              <div className="detail-item">
                <span className="detail-label">Khách hàng:</span>
                {editMode && jobStatus !== 'COMPLETED' && jobStatus !== 'CANCELLED' ? (
                  <div className="customer-edit-section" style={{ position: 'relative' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="detail-value">{jobCustomer.code || jobCustomer.name}</span>
                      <button
                        onClick={() => setShowCustomerSelector(!showCustomerSelector)}
                        style={{
                          padding: '4px 8px',
                          background: showCustomerSelector ? '#6B7280' : 'var(--primary)',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        {showCustomerSelector ? '✕ Đóng' : 'Thay đổi khách hàng'}
                      </button>
                    </div>
                    {showCustomerSelector && (
                      <>
                        {/* Overlay to close dropdown on outside click */}
                        <div
                          onClick={() => { setShowCustomerSelector(false); setCustomerSearch(''); }}
                          style={{
                            position: 'fixed',
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            zIndex: 99
                          }}
                        />
                        <div style={{
                          position: 'absolute',
                          top: '100%',
                          left: 0,
                          zIndex: 100,
                          background: 'white',
                          border: '1px solid var(--border)',
                          borderRadius: '6px',
                          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                          width: '300px',
                          maxHeight: '250px',
                          overflow: 'hidden'
                        }}>
                        <input
                          type="text"
                          placeholder="🔍 Tìm khách hàng..."
                          value={customerSearch}
                          onChange={e => setCustomerSearch(e.target.value)}
                          autoFocus
                          style={{
                            width: '100%',
                            padding: '10px',
                            border: 'none',
                            borderBottom: '1px solid var(--border)',
                            fontSize: '13px'
                          }}
                        />
                        <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                          {filteredCustomers.slice(0, 10).map(c => (
                            <div
                              key={c.customer_id}
                              onClick={() => handleCustomerChange(c)}
                              style={{
                                padding: '10px',
                                cursor: 'pointer',
                                borderBottom: '1px solid #f0f0f0',
                                fontSize: '13px',
                                background: c.customer_id === jobCustomer.id ? '#e3f2fd' : 'white'
                              }}
                              onMouseEnter={e => e.currentTarget.style.background = '#f5f5f5'}
                              onMouseLeave={e => e.currentTarget.style.background = c.customer_id === jobCustomer.id ? '#e3f2fd' : 'white'}
                            >
                              <strong>{c.customer_code}</strong> - {c.short_name || c.company_name}
                            </div>
                          ))}
                          {filteredCustomers.length === 0 && (
                            <div style={{ padding: '10px', color: '#999', textAlign: 'center' }}>Không tìm thấy</div>
                          )}
                        </div>
                      </div>
                      </>
                    )}
                  </div>
                ) : (
                  <span className="detail-value">{jobCustomer.code || jobCustomer.name || job.customer || job.customer_name}</span>
                )}
              </div>
              <div className="detail-item">
                <span className="detail-label">Ngày tạo:</span>
                <span className="detail-value">{job.created_at?.split('T')[0]}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Người tạo:</span>
                <span className="detail-value">{job.creator_name || job.created_by || '-'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Cập nhật bởi:</span>
                <span className="detail-value">{job.updater_name || job.updated_by || '-'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Ngày thực hiện:</span>
                <span className="detail-value">{job.scheduled_date || job.etd || '-'}{job.scheduled_time ? ` • ${job.scheduled_time.slice(0,5)}` : ''}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Status:</span>
                <StatusBadge status={job.status_code || 'PENDING'} />
              </div>
            </div>
          </div>

          {/* Services */}
          <div className="detail-section">
            <h3>Dịch vụ ({services.length})</h3>
            {loading ? (
              <div className="loading-text">Đang tải...</div>
            ) : services.length > 0 ? (
              <div className="services-list">
                {services.map((svc, idx) => (
                  <div key={idx} className="service-card">
                    <div className="service-card-header">
                      <span className="service-type-badge">{SERVICE_TYPE_LABELS[svc.service_type_code] || svc.service_type_code}</span>
                      {editMode ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <select
                            value={svc.status_code || 'PENDING'}
                            onChange={(e) => handleUpdateServiceStatus(svc.svc_id, e.target.value)}
                            disabled={saving}
                            style={{
                              padding: '4px 8px',
                              borderRadius: '4px',
                              border: '1px solid var(--border)',
                              fontSize: '12px',
                              background: 'var(--bg-card)'
                            }}
                          >
                            {getStatusOptions(svc.service_type_code).map(opt => (
                              <option key={opt.value} value={opt.value}>{opt.label}</option>
                            ))}
                          </select>
                          <button
                            onClick={() => handleDeleteService(svc.svc_id)}
                            disabled={saving}
                            title="Xóa dịch vụ"
                            style={{
                              padding: '4px 8px',
                              background: '#FEE2E2',
                              color: '#DC2626',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '12px'
                            }}
                          >
                            🗑️
                          </button>
                        </div>
                      ) : (
                        <StatusBadge status={svc.status_code || 'PENDING'} />
                      )}
                    </div>

                    {/* Assignment info - Editable (auto-saves on selection) */}
                    <div className="service-assignment">
                      <strong>Vendor/NV:</strong>
                      {editMode ? (
                        <div className="assign-controls">
                          {/* Searchable Vendor Dropdown */}
                          <div className="vendor-search-wrapper" style={{ position: 'relative', display: 'inline-block' }}>
                            <input
                              type="text"
                              placeholder="🔍 Tìm vendor..."
                              value={svc.vendorSearch !== undefined ? svc.vendorSearch : (svc.vendor_name || '')}
                              onChange={(e) => {
                                const searchValue = e.target.value
                                setServices(prev => prev.map(s =>
                                  s.svc_id === svc.svc_id ? { ...s, vendorSearch: searchValue, showVendorDropdown: true } : s
                                ))
                              }}
                              onFocus={() => {
                                setServices(prev => prev.map(s =>
                                  s.svc_id === svc.svc_id ? { ...s, showVendorDropdown: true } : s
                                ))
                              }}
                              onBlur={() => {
                                // Delay to allow click on dropdown items
                                setTimeout(() => {
                                  setServices(prev => prev.map(s =>
                                    s.svc_id === svc.svc_id ? { ...s, showVendorDropdown: false } : s
                                  ))
                                }, 200)
                              }}
                              onKeyDown={(e) => e.stopPropagation()}
                              onMouseDown={(e) => e.stopPropagation()}
                              onClick={(e) => e.stopPropagation()}
                              style={{
                                padding: '6px 10px',
                                borderRadius: '6px',
                                border: '1px solid var(--border)',
                                minWidth: '200px',
                                fontSize: '12px'
                              }}
                            />
                            {svc.showVendorDropdown && (
                              <div style={{
                                position: 'absolute',
                                top: '100%',
                                left: 0,
                                right: 0,
                                maxHeight: '200px',
                                overflowY: 'auto',
                                background: 'var(--bg-card)',
                                border: '1px solid var(--border)',
                                borderRadius: '6px',
                                marginTop: '4px',
                                zIndex: 1000,
                                boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
                              }}>
                                <div
                                  style={{ padding: '8px 10px', cursor: 'pointer', borderBottom: '1px solid var(--border)' }}
                                  onMouseDown={(e) => {
                                    e.preventDefault()
                                    handleAssign(svc.svc_id, null, svc.employee_id || null)
                                    setServices(prev => prev.map(s =>
                                      s.svc_id === svc.svc_id ? { ...s, showVendorDropdown: false, vendorSearch: '', vendor_id: null, vendor_name: null } : s
                                    ))
                                  }}
                                >
                                  -- Bỏ chọn --
                                </div>
                                {vendors.filter(v =>
                                  !svc.vendorSearch ||
                                  (v.short_name || v.company_name || '').toLowerCase().includes((svc.vendorSearch || '').toLowerCase())
                                ).map(v => (
                                  <div
                                    key={v.vendor_id}
                                    style={{
                                      padding: '8px 10px',
                                      cursor: 'pointer',
                                      background: svc.vendor_id === v.vendor_id ? 'rgba(37, 99, 235, 0.2)' : 'transparent'
                                    }}
                                    onMouseEnter={(e) => e.target.style.background = 'rgba(37, 99, 235, 0.1)'}
                                    onMouseLeave={(e) => e.target.style.background = svc.vendor_id === v.vendor_id ? 'rgba(37, 99, 235, 0.2)' : 'transparent'}
                                    onMouseDown={(e) => {
                                      e.preventDefault()
                                      handleAssign(svc.svc_id, v.vendor_id, svc.employee_id || null)
                                      setServices(prev => prev.map(s =>
                                        s.svc_id === svc.svc_id ? { ...s, showVendorDropdown: false, vendorSearch: '', vendor_id: v.vendor_id, vendor_name: v.short_name || v.company_name } : s
                                      ))
                                    }}
                                  >
                                    🏢 {v.short_name || v.company_name}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                          {savedField === `vendor-${svc.svc_id}` && (
                            <span style={{ color: '#10B981', fontSize: '12px', fontWeight: 'bold', animation: 'fadeIn 0.3s' }}>Da luu</span>
                          )}
                          <span>hoặc</span>
                          <select
                            value={svc.employee_id || ''}
                            onChange={e => handleAssign(svc.svc_id, svc.vendor_id || null, e.target.value ? parseInt(e.target.value) : null)}
                            disabled={saving}
                          >
                            <option value="">-- Nhân viên --</option>
                            {employees.map(e => (
                              <option key={e.employee_id} value={e.employee_id}>👤 {e.full_name}</option>
                            ))}
                          </select>
                        </div>
                      ) : (
                        <span className={`assigned-badge ${svc.vendor_id ? 'vendor' : svc.employee_id ? 'employee' : svc.license_plate ? 'vendor' : 'unassigned'}`}>
                          {svc.vendor_id ? '🏢 ' : svc.employee_id ? '👤 ' : svc.license_plate ? '🚚 ' : ''}
                          {svc.vendor_name || svc.employee_name || (svc.license_plate ? `${svc.vehicles?.length || 1} xe đã gán` : 'Chưa gán')}
                        </span>
                      )}
                    </div>

                    <div className="service-details-grid">
                      {editMode ? (
                        /* Editable service details */
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', width: '100%' }}>
                          <div>
                            <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Hàng</label>
                            <input type="text" value={svc.cargo_type || ''} onChange={e => setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, cargo_type: e.target.value } : s))} placeholder="VD: loc khi, linh kien..." style={{ width: '100%', padding: '5px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '12px' }} />
                          </div>
                          <div>
                            <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Số kiện</label>
                            <div style={{ display: 'flex', gap: '4px' }}>
                              <input type="text" value={svc.package_quantity || ''} onChange={e => setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, package_quantity: e.target.value } : s))} placeholder="38" style={{ width: '60px', padding: '5px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '12px' }} />
                              <select value={svc.package_unit || 'Package (Kiện, gói)'} onChange={e => setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, package_unit: e.target.value } : s))} style={{ flex: 1, padding: '5px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '12px', background: 'var(--bg-primary)' }}>
                                <optgroup label="Phổ biến">
                                  <option value="Carton (Thùng carton)">Carton (Thùng carton)</option>
                                  <option value="Pallet & Package">Pallet & Package</option>
                                  <option value="Box (Hộp)">Box (Hộp)</option>
                                  <option value="Package (Kiện, gói)">Package (Kiện, gói)</option>
                                  <option value="Case (Thùng)">Case (Thùng)</option>
                                  <option value="Bundle (Gói)">Bundle (Gói)</option>
                                  <option value="Roll(Cuộn)">Roll (Cuộn)</option>
                                  <option value="Container">Container</option>
                                  <option value="Piece">Piece</option>
                                </optgroup>
                                <optgroup label="Tất cả">
                                  <option value="Bag (Túi)">Bag (Túi)</option>
                                  <option value="Bale,compressed (Gói dạng nén)">Bale, compressed (Gói dạng nén)</option>
                                  <option value="Bale,non-compressed (Gói không nén)">Bale, non-compressed (Gói không nén)</option>
                                  <option value="Bar (Thanh)">Bar (Thanh)</option>
                                  <option value="Barrel (Thùng)">Barrel (Thùng)</option>
                                  <option value="Basket (Giỏ)">Basket (Giỏ)</option>
                                  <option value="Cage (Lồng)">Cage (Lồng)</option>
                                  <option value="Can, cylindrical (Hộp hình trụ)">Can, cylindrical (Hộp hình trụ)</option>
                                  <option value="Can, rectangular (Thùng, hình hộp chữ nhật)">Can, rectangular (Thùng HCN)</option>
                                  <option value="Carboy, non-protected (Chai, không được bảo vệ)">Carboy, non-protected</option>
                                  <option value="Carboy, protected (Chai đựng axit)">Carboy, protected</option>
                                  <option value="Cask (Thùng tô nô)">Cask (Thùng tô nô)</option>
                                  <option value="Coil (Cuốn)">Coil (Cuốn)</option>
                                  <option value="Crate (Giỏ)">Crate (Giỏ)</option>
                                  <option value="Cylinder (Xylanh)">Cylinder (Xylanh)</option>
                                  <option value="Drum (Thùng)">Drum (Thùng)</option>
                                  <option value="Keg (Thùng đựng cá mòi muối)">Keg</option>
                                  <option value="Log (Khúc gỗ)">Log (Khúc gỗ)</option>
                                  <option value="Logs, in bundle/bunch/truss">Logs, in bundle/bunch/truss</option>
                                  <option value="MST">MST</option>
                                  <option value="Mat (Thảm)">Mat (Thảm)</option>
                                  <option value="Net (Cuộn)">Net (Cuộn)</option>
                                  <option value="Packet (Gói)">Packet (Gói)</option>
                                  <option value="Pail (Thùng đựng nước)">Pail (Thùng đựng nước)</option>
                                  <option value="Parcel (Lô, bưu kiện, gói hàng)">Parcel (Bưu kiện)</option>
                                  <option value="Pen (Lồng)">Pen (Lồng)</option>
                                  <option value="Pipe (ống)">Pipe (Ống)</option>
                                  <option value="Plate (Đĩa)">Plate (Đĩa)</option>
                                  <option value="Tank (Thùng, két, bể chứa hình trụ)">Tank (Bể chứa)</option>
                                  <option value="Tray (Khay)">Tray (Khay)</option>
                                  <option value="Unpacked or unpackaged (Hàng rời, không đóng gói)">Unpacked (Hàng rời)</option>
                                  <option value="Other (Loại khác)">Other (Loại khác)</option>
                                </optgroup>
                              </select>
                            </div>
                          </div>
                          <div>
                            <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Điểm đi</label>
                            <input type="text" value={svc.origin_address || ''} onChange={e => setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, origin_address: e.target.value } : s))} placeholder="VD: Binh Duong" style={{ width: '100%', padding: '5px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '12px' }} />
                          </div>
                          <div>
                            <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Điểm đến</label>
                            <input type="text" value={svc.dest_address || ''} onChange={e => setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, dest_address: e.target.value } : s))} placeholder="VD: KCN Song Cong" style={{ width: '100%', padding: '5px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '12px' }} />
                          </div>
                          <div>
                            <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Ngày</label>
                            <input type="date" value={svc.scheduled_date || ''} onChange={e => setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, scheduled_date: e.target.value } : s))} style={{ width: '100%', padding: '5px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '12px' }} />
                          </div>
                          <div>
                            <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Giờ</label>
                            <input type="time" value={(svc.scheduled_time || '').slice(0, 5)} onChange={e => setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, scheduled_time: e.target.value } : s))} style={{ width: '100%', padding: '5px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '12px' }} />
                          </div>
                          <div style={{ gridColumn: '1 / -1' }}>
                            <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Invoice</label>
                            <input type="text" value={svc.invoice_numbers || ''} onChange={e => setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, invoice_numbers: e.target.value } : s))} placeholder="VD: INV-001, INV-002" style={{ width: '100%', padding: '5px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '12px' }} />
                          </div>
                          {/* Dynamic extra info fields */}
                          {(svc.extra_info || []).map((info, idx) => (
                            <div key={`info-${idx}`} style={{ gridColumn: '1 / -1', display: 'flex', gap: '4px', alignItems: 'center' }}>
                              <input type="text" value={info.label || ''} onChange={e => {
                                const updated = [...(svc.extra_info || [])]
                                updated[idx] = { ...updated[idx], label: e.target.value }
                                setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, extra_info: updated } : s))
                              }} placeholder="Tên (VD: Điểm giao 2)" style={{ width: '140px', padding: '5px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '12px' }} />
                              <input type="text" value={info.value || ''} onChange={e => {
                                const updated = [...(svc.extra_info || [])]
                                updated[idx] = { ...updated[idx], value: e.target.value }
                                setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, extra_info: updated } : s))
                              }} placeholder="Giá trị" style={{ flex: 1, padding: '5px 8px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '12px' }} />
                              <button type="button" onClick={() => {
                                const updated = (svc.extra_info || []).filter((_, i) => i !== idx)
                                setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, extra_info: updated } : s))
                              }} style={{ padding: '4px 8px', background: '#FEE2E2', color: '#DC2626', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '11px' }}>✕</button>
                            </div>
                          ))}
                          <div style={{ gridColumn: '1 / -1', display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <button type="button" onClick={() => {
                              const updated = [...(svc.extra_info || []), { label: '', value: '' }]
                              setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, extra_info: updated } : s))
                            }} style={{ padding: '4px 10px', background: 'rgba(59, 130, 246, 0.1)', color: 'var(--primary)', border: '1px dashed var(--primary)', borderRadius: '4px', fontSize: '11px', cursor: 'pointer' }}>
                              + Thêm thông tin
                            </button>
                            <button type="button" onClick={async () => {
                              setSaving(true)
                              try {
                                const res = await authFetch(`${API_URL}/api/jobs/services/${svc.svc_id}/details`, {
                                  method: 'PUT',
                                  headers: { 'Content-Type': 'application/json' },
                                  body: JSON.stringify({
                                    cargo_type: svc.cargo_type || null,
                                    package_quantity: svc.package_quantity || null,
                                    package_unit: svc.package_unit || null,
                                    origin_address: svc.origin_address || null,
                                    dest_address: svc.dest_address || null,
                                    scheduled_date: svc.scheduled_date || null,
                                    scheduled_time: svc.scheduled_time || null,
                                    invoice_numbers: svc.invoice_numbers || null,
                                    extra_info: (svc.extra_info || []).filter(i => i.label || i.value),
                                  })
                                })
                                const result = await res.json()
                                if (result.success) {
                                  setSavedField(`details-${svc.svc_id}`)
                                  setTimeout(() => setSavedField(null), 2000)
                                } else { alert(result.message || 'Lỗi khi lưu') }
                              } catch (e) { alert('Lỗi khi lưu chi tiết') }
                              finally { setSaving(false) }
                            }} disabled={saving} style={{ padding: '6px 12px', background: 'var(--primary)', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' }}>
                              {saving ? '...' : '✓'} Lưu chi tiết
                            </button>
                            {savedField === `details-${svc.svc_id}` && (
                              <span style={{ color: '#10B981', fontSize: '12px', fontWeight: 'bold' }}>Da luu</span>
                            )}
                          </div>
                        </div>
                      ) : (
                        /* Read-only service details */
                        <>
                          {svc.cargo_type && <div><strong>Hàng:</strong> {svc.cargo_type}</div>}
                          {svc.package_quantity && <div><strong>Số kiện:</strong> {svc.package_quantity} {svc.package_unit || 'pallet'}</div>}
                          {svc.origin_address && <div><strong>Điểm đi:</strong> {svc.origin_address}</div>}
                          {svc.dest_address && <div><strong>Điểm đến:</strong> {svc.dest_address}</div>}
                          {svc.scheduled_date && <div><strong>Ngày:</strong> {svc.scheduled_date}</div>}
                          {svc.scheduled_time && <div><strong>Giờ:</strong> {svc.scheduled_time}</div>}
                          {svc.invoice_numbers && <div><strong>Invoice:</strong> {svc.invoice_numbers}</div>}
                          {(svc.extra_info || []).map((info, idx) => (
                            info.label && info.value ? <div key={idx}><strong>{info.label}:</strong> {info.value}</div> : null
                          ))}
                        </>
                      )}

                      {/* Ghi chú / Yêu cầu đặc biệt - Editable */}
                      {editMode ? (
                        <div className="notes-edit-section" style={{
                          marginTop: '10px',
                          padding: '10px',
                          background: 'rgba(59, 130, 246, 0.05)',
                          borderRadius: '8px',
                          border: '1px dashed var(--border)'
                        }}>
                          <strong style={{ display: 'block', marginBottom: '6px' }}>📝 Ghi chú dịch vụ:</strong>
                          <textarea
                            value={svc.special_requirements || ''}
                            onChange={(e) => setServices(prev => prev.map(s =>
                              s.svc_id === svc.svc_id ? { ...s, special_requirements: e.target.value } : s
                            ))}
                            placeholder="VD: Khách yêu cầu không xếp chồng, chờ hàng từ 8h-12h, phí chờ giờ..."
                            style={{
                              width: '100%',
                              minHeight: '60px',
                              padding: '8px',
                              borderRadius: '6px',
                              border: '1px solid var(--border)',
                              fontSize: '13px',
                              resize: 'vertical'
                            }}
                          />
                          <button
                            type="button"
                            onClick={() => handleUpdateServiceNotes(svc.svc_id, svc.special_requirements)}
                            disabled={saving}
                            style={{
                              marginTop: '6px',
                              padding: '6px 12px',
                              background: 'var(--primary)',
                              color: 'white',
                              border: 'none',
                              borderRadius: '6px',
                              cursor: 'pointer',
                              fontSize: '12px'
                            }}
                          >
                            {saving ? '⏳' : '✓'} Lưu ghi chú
                          </button>
                        </div>
                      ) : svc.special_requirements && (
                        <div className="special-requirements-section" style={{
                          marginTop: '10px',
                          padding: '10px',
                          background: 'rgba(59, 130, 246, 0.1)',
                          borderRadius: '6px',
                          borderLeft: '3px solid var(--primary)'
                        }}>
                          <strong>📝 Ghi chú:</strong>
                          <div style={{ marginTop: '4px', whiteSpace: 'pre-wrap' }}>{svc.special_requirements}</div>
                        </div>
                      )}

                      {/* Vehicle info - editable in edit mode */}
                      {editMode ? (
                        <div className="vehicle-edit-section" style={{
                          marginTop: '12px',
                          padding: '12px',
                          background: 'rgba(59, 130, 246, 0.05)',
                          borderRadius: '8px',
                          border: '1px dashed var(--border)'
                        }}>
                          <strong style={{ display: 'block', marginBottom: '8px' }}>🚚 Thông tin xe:</strong>
                          {/* Warning if no vendor selected */}
                          {!svc.vendor_id && (
                            <div style={{
                              padding: '8px 12px',
                              background: 'rgba(245, 158, 11, 0.1)',
                              border: '1px solid #F59E0B',
                              borderRadius: '6px',
                              marginBottom: '8px',
                              fontSize: '12px',
                              color: '#D97706'
                            }}>
                              ⚠️ Vui lòng chọn Vendor trước khi gán xe để đối chiếu thanh toán
                            </div>
                          )}
                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                            <input
                              type="text"
                              placeholder="Biển số xe"
                              value={svc.license_plate || ''}
                              onChange={(e) => setServices(prev => prev.map(s =>
                                s.svc_id === svc.svc_id ? { ...s, license_plate: e.target.value } : s
                              ))}
                              style={{ padding: '8px', borderRadius: '6px', border: '1px solid var(--border)', fontSize: '13px' }}
                            />
                            <input
                              type="text"
                              placeholder="Tên tài xế"
                              value={svc.driver_name || ''}
                              onChange={(e) => setServices(prev => prev.map(s =>
                                s.svc_id === svc.svc_id ? { ...s, driver_name: e.target.value } : s
                              ))}
                              style={{ padding: '8px', borderRadius: '6px', border: '1px solid var(--border)', fontSize: '13px' }}
                            />
                            <input
                              type="text"
                              placeholder="SĐT tài xế"
                              value={svc.driver_phone || ''}
                              onChange={(e) => setServices(prev => prev.map(s =>
                                s.svc_id === svc.svc_id ? { ...s, driver_phone: e.target.value } : s
                              ))}
                              style={{ padding: '8px', borderRadius: '6px', border: '1px solid var(--border)', fontSize: '13px' }}
                            />
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              // Require vendor selection before saving vehicle info
                              if (!svc.vendor_id && svc.license_plate) {
                                alert('Vui lòng chọn Vendor trước khi lưu thông tin xe để đối chiếu thanh toán')
                                return
                              }
                              handleAssign(svc.svc_id, svc.vendor_id, svc.employee_id, {
                                license_plate: svc.license_plate,
                                driver_name: svc.driver_name,
                                driver_phone: svc.driver_phone
                              })
                            }}
                            disabled={saving}
                            style={{
                              marginTop: '8px',
                              padding: '6px 12px',
                              background: !svc.vendor_id && svc.license_plate ? '#9CA3AF' : 'var(--primary)',
                              color: 'white',
                              border: 'none',
                              borderRadius: '6px',
                              cursor: !svc.vendor_id && svc.license_plate ? 'not-allowed' : 'pointer',
                              fontSize: '12px'
                            }}
                          >
                            {saving ? '⏳' : '✓'} Lưu thông tin xe
                          </button>
                        </div>
                      ) : svc.license_plate && (
                        <div className="vehicle-info-section" style={{
                          marginTop: '10px',
                          padding: '10px',
                          background: 'rgba(16, 185, 129, 0.1)',
                          borderRadius: '6px'
                        }}>
                          {svc.vendor_name && <div><strong>🏢 Vendor:</strong> {svc.vendor_name}</div>}
                          {/* Display all vehicles if multiple */}
                          {svc.vehicles && svc.vehicles.length > 1 ? (
                            <div>
                              <strong>🚚 Xe đã gán ({svc.vehicles.length} xe):</strong>
                              {svc.vehicles.map((v, idx) => (
                                <div key={idx} style={{
                                  marginTop: '8px',
                                  padding: '8px',
                                  background: 'rgba(255, 255, 255, 0.5)',
                                  borderRadius: '4px',
                                  borderLeft: '3px solid #10B981'
                                }}>
                                  <div><strong>🚗 Xe {idx + 1}:</strong> {v.license_plate}</div>
                                  {v.driver_name && <div><strong>👤 Tài xế:</strong> {v.driver_name}</div>}
                                  {v.driver_phone && <div><strong>📞 SĐT:</strong> {v.driver_phone}</div>}
                                  {v.driver_id_card && <div><strong>🆔 CCCD:</strong> {v.driver_id_card}</div>}
                                </div>
                              ))}
                            </div>
                          ) : (
                            <>
                              <div><strong>🚗 Biển số:</strong> {svc.license_plate}</div>
                              {svc.driver_name && <div><strong>👤 Tài xế:</strong> {svc.driver_name}</div>}
                              {svc.driver_phone && <div><strong>📞 SĐT:</strong> {svc.driver_phone}</div>}
                              {svc.driver_id_card && <div><strong>🆔 CCCD:</strong> {svc.driver_id_card}</div>}
                            </>
                          )}
                        </div>
                      )}

                      {/* Cost/Revenue Summary - Always visible when data exists */}
                      {!editMode && (() => {
                        const totalCost = (svc.buying_price || 0) + (svc.extra_costs || []).reduce((sum, c) => sum + (c.amount || 0), 0)
                        const totalRevenue = (svc.selling_price || 0) + (svc.extra_revenues || []).reduce((sum, r) => sum + (r.amount || 0), 0)
                        const profit = totalRevenue - totalCost
                        if (totalCost === 0 && totalRevenue === 0) return null
                        return (
                          <div style={{
                            marginTop: '12px',
                            padding: '10px 12px',
                            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.08), rgba(59, 130, 246, 0.08))',
                            borderRadius: '8px',
                            border: '1px solid rgba(16, 185, 129, 0.2)'
                          }}>
                            <div style={{
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              flexWrap: 'wrap',
                              gap: '10px',
                              fontSize: '13px'
                            }}>
                              <span style={{ color: '#10B981' }}>
                                📤 Doanh thu: <b>{formatPrice(totalRevenue)}</b>
                              </span>
                              <span style={{ color: '#EF4444' }}>
                                📥 Chi phí: <b>{formatPrice(totalCost)}</b>
                              </span>
                              <span style={{
                                fontWeight: 'bold',
                                color: profit >= 0 ? '#10B981' : '#EF4444',
                                padding: '4px 8px',
                                background: profit >= 0 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                                borderRadius: '4px'
                              }}>
                                💵 Lợi nhuận: {formatPrice(profit)}
                                {totalCost > 0 && ` (${(profit / totalCost * 100).toFixed(1)}%)`}
                              </span>
                            </div>
                            {/* Breakdown: base prices + extras */}
                            <div style={{
                              marginTop: '8px',
                              paddingTop: '8px',
                              borderTop: '1px dashed rgba(0,0,0,0.1)',
                              fontSize: '11px',
                              color: 'var(--text-secondary)'
                            }}>
                              {/* Base cost (buying_price) */}
                              {svc.buying_price > 0 && (
                                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '2px 0' }}>
                                  <span>📥 Chi phí vận chuyển</span>
                                  <span style={{ color: '#EF4444' }}><b>{formatPrice(svc.buying_price)}</b></span>
                                </div>
                              )}
                              {(svc.extra_costs || []).map((cost, idx) => (
                                <div key={`vc-${idx}`} style={{ display: 'flex', justifyContent: 'space-between', padding: '2px 0' }}>
                                  <span>📥 {cost.name || cost.description || 'Phụ phí'}{cost.vendor && <span style={{ color: '#6B7280' }}> ({cost.vendor})</span>}</span>
                                  <span style={{ color: '#EF4444' }}>
                                    {cost.unit_price ? `${cost.qty || 1} ${cost.unit || 'ca'} × ${formatPrice(cost.unit_price)} = ` : ''}
                                    <b>{formatPrice(cost.amount || ((cost.qty || 1) * (cost.unit_price || 0)))}</b>
                                  </span>
                                </div>
                              ))}
                              {/* Base revenue (selling_price) */}
                              {svc.selling_price > 0 && (
                                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '2px 0' }}>
                                  <span>📤 Doanh thu vận chuyển</span>
                                  <span style={{ color: '#10B981' }}><b>{formatPrice(svc.selling_price)}</b></span>
                                </div>
                              )}
                              {(svc.extra_revenues || []).map((rev, idx) => (
                                <div key={`vr-${idx}`} style={{ display: 'flex', justifyContent: 'space-between', padding: '2px 0' }}>
                                  <span>📤 {rev.name || rev.description || 'Phụ thu'}</span>
                                  <span style={{ color: '#10B981' }}>
                                    {rev.unit_price ? `${rev.qty || 1} ${rev.unit || 'chuyến'} × ${formatPrice(rev.unit_price)} = ` : ''}
                                    <b>{formatPrice(rev.amount || ((rev.qty || 1) * (rev.unit_price || 0)))}</b>
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )
                      })()}

                      {/* Quotation Section - Only in edit mode */}
                      {editMode && (
                        <div className="quotation-section" style={{
                          marginTop: '12px',
                          padding: '12px',
                          background: 'rgba(16, 185, 129, 0.05)',
                          borderRadius: '8px',
                          border: '1px dashed rgba(16, 185, 129, 0.3)'
                        }}>
                          <strong style={{ display: 'block', marginBottom: '10px' }}>
                            💰 Báo giá dịch vụ:
                          </strong>

                          {/* Buying Rate (Cost) */}
                          <QuotationSelector
                            type="buying"
                            rates={quotations[svc.svc_id]?.buying || []}
                            standardRates={standardRates}
                            selectedRateId={svc.buying_rate_id}
                            selectedPrice={svc.buying_price}
                            quantity={svc.buying_qty || 1}
                            vendorId={svc.vendor_id}
                            onQuantityChange={(qty) => {
                              setServices(prev => prev.map(s =>
                                s.svc_id === svc.svc_id
                                  ? { ...s, buying_qty: qty, buying_price: (s.buying_unit_price || 0) * qty }
                                  : s
                              ))
                            }}
                            onSelect={(rateId, price, details) => {
                              setServices(prev => prev.map(s =>
                                s.svc_id === svc.svc_id
                                  ? { ...s, buying_rate_id: rateId, buying_price: price, buying_unit_price: details?.unitPrice || price }
                                  : s
                              ))
                            }}
                            disabled={saving}
                          />

                          {/* Extra Costs - with qty, unit_price, unit, vendor */}
                          {(svc.extra_costs || []).map((cost, idx) => (
                            <div key={`cost-${idx}`} style={{
                              display: 'grid',
                              gridTemplateColumns: '1fr 80px 50px 80px 60px 80px 30px',
                              gap: '4px',
                              alignItems: 'center',
                              marginBottom: '6px',
                              padding: '6px',
                              background: 'rgba(239, 68, 68, 0.05)',
                              borderRadius: '4px'
                            }}>
                              <input
                                type="text"
                                value={cost.name}
                                onChange={e => {
                                  const newCosts = [...(svc.extra_costs || [])]
                                  newCosts[idx] = { ...newCosts[idx], name: e.target.value }
                                  setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, extra_costs: newCosts } : s))
                                }}
                                placeholder="Tên chi phí"
                                style={{ padding: '4px 6px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '11px' }}
                              />
                              <input
                                type="text"
                                value={cost.vendor || ''}
                                onChange={e => {
                                  const newCosts = [...(svc.extra_costs || [])]
                                  newCosts[idx] = { ...newCosts[idx], vendor: e.target.value }
                                  setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, extra_costs: newCosts } : s))
                                }}
                                placeholder="Vendor"
                                title="Nhà cung cấp"
                                style={{ padding: '4px 4px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '11px' }}
                              />
                              <input
                                type="number"
                                value={cost.qty ?? ''}
                                min="1"
                                onChange={e => {
                                  const newCosts = [...(svc.extra_costs || [])]
                                  const qty = e.target.value === '' ? null : (parseFloat(e.target.value) || 1)
                                  const unitPrice = newCosts[idx].unit_price || newCosts[idx].amount || 0
                                  newCosts[idx] = { ...newCosts[idx], qty, amount: (qty || 1) * unitPrice }
                                  setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, extra_costs: newCosts } : s))
                                }}
                                placeholder="KL"
                                title="Khối lượng"
                                style={{ padding: '4px 4px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '11px', textAlign: 'center' }}
                              />
                              <input
                                type="number"
                                value={cost.unit_price ?? cost.amount ?? ''}
                                onChange={e => {
                                  const newCosts = [...(svc.extra_costs || [])]
                                  const unitPrice = e.target.value === '' ? null : (parseFloat(e.target.value) || 0)
                                  const qty = newCosts[idx].qty || 1
                                  newCosts[idx] = { ...newCosts[idx], unit_price: unitPrice, amount: qty * (unitPrice || 0) }
                                  setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, extra_costs: newCosts } : s))
                                }}
                                placeholder="Đơn giá"
                                title="Đơn giá"
                                style={{ padding: '4px 4px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '11px' }}
                              />
                              <select
                                value={cost.unit || 'ca'}
                                onChange={e => {
                                  const newCosts = [...(svc.extra_costs || [])]
                                  newCosts[idx] = { ...newCosts[idx], unit: e.target.value }
                                  setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, extra_costs: newCosts } : s))
                                }}
                                style={{ padding: '4px 2px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '11px' }}
                              >
                                <option value="ca">ca</option>
                                <option value="chuyến">chuyến</option>
                                <option value="lần">lần</option>
                                <option value="giờ">giờ</option>
                                <option value="ngày">ngày</option>
                                <option value="kg">kg</option>
                                <option value="cbm">cbm</option>
                                <option value="kiện">kiện</option>
                                <option value="tờ khai">tờ khai</option>
                                <option value="bill">bill</option>
                              </select>
                              <span style={{ fontSize: '11px', fontWeight: 'bold', color: '#EF4444', textAlign: 'right' }}>
                                {formatPrice(cost.amount || 0)}
                              </span>
                              <button
                                onClick={() => {
                                  const newCosts = (svc.extra_costs || []).filter((_, i) => i !== idx)
                                  setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, extra_costs: newCosts } : s))
                                }}
                                style={{ padding: '4px 6px', background: '#EF4444', color: 'white', border: 'none', borderRadius: '4px', fontSize: '10px', cursor: 'pointer' }}
                              >✕</button>
                            </div>
                          ))}
                          <button
                            onClick={() => {
                              const newCosts = [...(svc.extra_costs || []), { name: '', vendor: '', qty: null, unit_price: null, unit: 'ca', amount: 0 }]
                              setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, extra_costs: newCosts } : s))
                            }}
                            style={{ marginBottom: '10px', padding: '4px 10px', background: 'rgba(239, 68, 68, 0.1)', color: '#EF4444', border: '1px dashed #EF4444', borderRadius: '4px', fontSize: '11px', cursor: 'pointer' }}
                          >+ Thêm chi phí</button>

                          {/* Selling Rate (Revenue) */}
                          <QuotationSelector
                            type="selling"
                            rates={quotations[svc.svc_id]?.selling || []}
                            selectedRateId={svc.selling_rate_id}
                            selectedPrice={svc.selling_price}
                            quantity={svc.selling_qty || 1}
                            onQuantityChange={(qty) => {
                              setServices(prev => prev.map(s =>
                                s.svc_id === svc.svc_id
                                  ? { ...s, selling_qty: qty, selling_price: (s.selling_unit_price || 0) * qty }
                                  : s
                              ))
                            }}
                            onSelect={(rateId, price, details) => {
                              setServices(prev => prev.map(s =>
                                s.svc_id === svc.svc_id
                                  ? { ...s, selling_rate_id: rateId, selling_price: price, selling_unit_price: details?.unitPrice || price }
                                  : s
                              ))
                            }}
                            disabled={saving}
                          />

                          {/* Extra Revenues - with qty, unit_price, unit */}
                          {(svc.extra_revenues || []).map((rev, idx) => (
                            <div key={`rev-${idx}`} style={{
                              display: 'grid',
                              gridTemplateColumns: '1fr 60px 90px 70px 90px 30px',
                              gap: '4px',
                              alignItems: 'center',
                              marginBottom: '6px',
                              padding: '6px',
                              background: 'rgba(16, 185, 129, 0.05)',
                              borderRadius: '4px'
                            }}>
                              <input
                                type="text"
                                value={rev.name}
                                onChange={e => {
                                  const newRevs = [...(svc.extra_revenues || [])]
                                  newRevs[idx] = { ...newRevs[idx], name: e.target.value }
                                  setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, extra_revenues: newRevs } : s))
                                }}
                                placeholder="Tên doanh thu"
                                style={{ padding: '4px 6px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '11px' }}
                              />
                              <input
                                type="number"
                                value={rev.qty || 1}
                                min="1"
                                onChange={e => {
                                  const newRevs = [...(svc.extra_revenues || [])]
                                  const qty = parseFloat(e.target.value) || 1
                                  const unitPrice = newRevs[idx].unit_price || newRevs[idx].amount || 0
                                  newRevs[idx] = { ...newRevs[idx], qty, amount: qty * unitPrice }
                                  setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, extra_revenues: newRevs } : s))
                                }}
                                placeholder="SL"
                                title="Số lượng"
                                style={{ padding: '4px 4px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '11px', textAlign: 'center' }}
                              />
                              <input
                                type="number"
                                value={rev.unit_price || rev.amount || 0}
                                onChange={e => {
                                  const newRevs = [...(svc.extra_revenues || [])]
                                  const unitPrice = parseFloat(e.target.value) || 0
                                  const qty = newRevs[idx].qty || 1
                                  newRevs[idx] = { ...newRevs[idx], unit_price: unitPrice, amount: qty * unitPrice }
                                  setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, extra_revenues: newRevs } : s))
                                }}
                                placeholder="Đơn giá"
                                title="Đơn giá"
                                style={{ padding: '4px 4px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '11px' }}
                              />
                              <select
                                value={rev.unit || 'chuyến'}
                                onChange={e => {
                                  const newRevs = [...(svc.extra_revenues || [])]
                                  newRevs[idx] = { ...newRevs[idx], unit: e.target.value }
                                  setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, extra_revenues: newRevs } : s))
                                }}
                                style={{ padding: '4px 2px', borderRadius: '4px', border: '1px solid var(--border)', fontSize: '11px' }}
                              >
                                <option value="chuyến">chuyến</option>
                                <option value="ca">ca</option>
                                <option value="lần">lần</option>
                                <option value="giờ">giờ</option>
                                <option value="ngày">ngày</option>
                                <option value="kg">kg</option>
                                <option value="cbm">cbm</option>
                              </select>
                              <span style={{ fontSize: '11px', fontWeight: 'bold', color: '#10B981', textAlign: 'right' }}>
                                {formatPrice(rev.amount || 0)}
                              </span>
                              <button
                                onClick={() => {
                                  const newRevs = (svc.extra_revenues || []).filter((_, i) => i !== idx)
                                  setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, extra_revenues: newRevs } : s))
                                }}
                                style={{ padding: '4px 6px', background: '#EF4444', color: 'white', border: 'none', borderRadius: '4px', fontSize: '10px', cursor: 'pointer' }}
                              >✕</button>
                            </div>
                          ))}
                          <button
                            onClick={() => {
                              const newRevs = [...(svc.extra_revenues || []), { name: '', qty: 1, unit_price: 0, unit: 'chuyến', amount: 0 }]
                              setServices(prev => prev.map(s => s.svc_id === svc.svc_id ? { ...s, extra_revenues: newRevs } : s))
                            }}
                            style={{ marginBottom: '10px', padding: '4px 10px', background: 'rgba(16, 185, 129, 0.1)', color: '#10B981', border: '1px dashed #10B981', borderRadius: '4px', fontSize: '11px', cursor: 'pointer' }}
                          >+ Thêm doanh thu</button>

                          {/* Profit Display */}
                          {(() => {
                            const totalCost = (svc.buying_price || 0) + (svc.extra_costs || []).reduce((sum, c) => sum + (c.amount || 0), 0)
                            const totalRevenue = (svc.selling_price || 0) + (svc.extra_revenues || []).reduce((sum, r) => sum + (r.amount || 0), 0)
                            const profit = totalRevenue - totalCost
                            if (totalCost === 0 && totalRevenue === 0) return null
                            return (
                              <div style={{
                                marginTop: '10px',
                                padding: '8px',
                                background: 'rgba(16, 185, 129, 0.1)',
                                borderRadius: '6px',
                                display: 'flex',
                                justifyContent: 'space-between',
                                fontSize: '12px',
                                flexWrap: 'wrap',
                                gap: '8px'
                              }}>
                                <span>📤 Doanh thu: <b>{formatPrice(totalRevenue)}</b></span>
                                <span>📥 Chi phí: <b>{formatPrice(totalCost)}</b></span>
                                <span style={{
                                  fontWeight: 'bold',
                                  color: profit >= 0 ? '#10B981' : '#EF4444'
                                }}>
                                  💵 Lợi nhuận: {formatPrice(profit)}
                                  {totalCost > 0 && ` (${(profit / totalCost * 100).toFixed(1)}%)`}
                                </span>
                              </div>
                            )
                          })()}

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
                              cursor: 'pointer',
                              fontSize: '12px'
                            }}
                          >
                            {saving ? '⏳' : '✓'} Lưu báo giá
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-data">Không có dịch vụ</div>
            )}

            {/* Add Service Section - only in edit mode */}
            {editMode && jobStatus !== 'COMPLETED' && jobStatus !== 'CANCELLED' && (
              <div className="add-service-section" style={{ marginTop: '16px' }}>
                <button
                  onClick={() => setShowAddService(!showAddService)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '10px 16px',
                    background: showAddService ? 'var(--border)' : 'var(--success)',
                    color: showAddService ? 'var(--text)' : 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: '500'
                  }}
                >
                  {showAddService ? '✕ Đóng' : '+ Thêm dịch vụ'}
                </button>

                {showAddService && (
                  <div style={{
                    marginTop: '12px',
                    padding: '16px',
                    background: 'rgba(16, 185, 129, 0.05)',
                    borderRadius: '8px',
                    border: '1px solid rgba(16, 185, 129, 0.2)'
                  }}>
                    <h4 style={{ margin: '0 0 12px 0', fontSize: '14px' }}>Thêm dịch vụ mới</h4>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                      <div>
                        <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px', color: 'var(--text-secondary)' }}>
                          Loại dịch vụ:
                        </label>
                        <select
                          value={newService.service_type_code}
                          onChange={e => setNewService({...newService, service_type_code: e.target.value})}
                          style={{
                            width: '100%',
                            padding: '8px',
                            borderRadius: '6px',
                            border: '1px solid var(--border)',
                            fontSize: '13px'
                          }}
                        >
                          <optgroup label="🚚 Vận tải Đường bộ">
                            <option value="TRUCKING_DOM">Vận tải nội địa</option>
                            <option value="BORDER_IMP">Nhập khẩu đường bộ</option>
                          </optgroup>
                          <optgroup label="✈️ Hàng không">
                            <option value="AIR_IMP">Hàng không - Nhập</option>
                            <option value="AIR_EXP">Hàng không - Xuất</option>
                          </optgroup>
                          <optgroup label="🚢 Đường biển">
                            <option value="SEA_IMP">Đường biển - Nhập</option>
                            <option value="SEA_EXP">Đường biển - Xuất</option>
                          </optgroup>
                          <optgroup label="🏭 Kho bãi">
                            <option value="WHS_STORAGE">Lưu kho</option>
                            <option value="WHS_HANDLE">Bốc xếp</option>
                            <option value="WHS_VAS">Dịch vụ gia tăng (VAS)</option>
                            <option value="WHS_CSHT">Phí cơ sở hạ tầng (CSHT)</option>
                            <option value="WHS_THC">Phí THC</option>
                          </optgroup>
                          <optgroup label="📋 Khai quan">
                            <option value="CUS_IMPORT">Khai quan Nhập</option>
                            <option value="CUS_EXPORT">Khai quan Xuất</option>
                            <option value="CUS_TRANSIT">Quá cảnh</option>
                            <option value="CUS_CO">Chứng nhận xuất xứ (C/O)</option>
                            <option value="CUS_SUPERVISE">Giám sát hải quan</option>
                            <option value="CUS_INSPECT">Kiểm hoá</option>
                            <option value="CUS_TRANSFER">Chuyển khẩu</option>
                          </optgroup>
                          <optgroup label="📦 Đóng gói">
                            <option value="SVC_PACK">Đóng gói</option>
                            <option value="SVC_FUMI">Hun trùng</option>
                            <option value="SVC_VACUUM">Hút chân không</option>
                            <option value="SVC_SHRINK">Màng co</option>
                            <option value="SVC_LASHING">Chằng buộc</option>
                          </optgroup>
                          <optgroup label="🏗️ Nâng hạ">
                            <option value="LIFT_ON">Nâng cont/hàng</option>
                            <option value="LIFT_OFF">Hạ cont/hàng</option>
                          </optgroup>
                          <optgroup label="💰 Phí phát sinh">
                            <option value="SVC_WAITING">Phí chờ giờ</option>
                            <option value="SVC_CANCEL_FEE">Phí huỷ chuyến</option>
                            <option value="SVC_SURCHARGE">Phí phát sinh khác</option>
                          </optgroup>
                          <optgroup label="📌 Khác">
                            <option value="SVC_OTHER">Dịch vụ khác</option>
                          </optgroup>
                        </select>
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px', color: 'var(--text-secondary)' }}>
                          Ngày thực hiện:
                        </label>
                        <input
                          type="date"
                          value={newService.scheduled_date}
                          onChange={e => setNewService({...newService, scheduled_date: e.target.value})}
                          style={{
                            width: '100%',
                            padding: '8px',
                            borderRadius: '6px',
                            border: '1px solid var(--border)',
                            fontSize: '13px'
                          }}
                        />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px', color: 'var(--text-secondary)' }}>
                          Điểm đi:
                        </label>
                        <input
                          type="text"
                          value={newService.origin_address}
                          onChange={e => setNewService({...newService, origin_address: e.target.value})}
                          placeholder="Địa chỉ lấy hàng"
                          style={{
                            width: '100%',
                            padding: '8px',
                            borderRadius: '6px',
                            border: '1px solid var(--border)',
                            fontSize: '13px'
                          }}
                        />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px', color: 'var(--text-secondary)' }}>
                          Điểm đến:
                        </label>
                        <input
                          type="text"
                          value={newService.dest_address}
                          onChange={e => setNewService({...newService, dest_address: e.target.value})}
                          placeholder="Địa chỉ giao hàng"
                          style={{
                            width: '100%',
                            padding: '8px',
                            borderRadius: '6px',
                            border: '1px solid var(--border)',
                            fontSize: '13px'
                          }}
                        />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px', color: 'var(--text-secondary)' }}>
                          🏢 Nhà cung cấp:
                        </label>
                        <select
                          value={newService.vendor_id}
                          onChange={e => setNewService({...newService, vendor_id: e.target.value})}
                          style={{
                            width: '100%',
                            padding: '8px',
                            borderRadius: '6px',
                            border: '1px solid var(--border)',
                            fontSize: '13px'
                          }}
                        >
                          <option value="">-- Chọn vendor --</option>
                          {vendors.map(v => (
                            <option key={v.vendor_id} value={v.vendor_id}>
                              {v.short_name || v.vendor_name}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px', color: 'var(--text-secondary)' }}>
                          🚗 Biển số xe:
                        </label>
                        <input
                          type="text"
                          value={newService.license_plate}
                          onChange={e => setNewService({...newService, license_plate: e.target.value.toUpperCase()})}
                          placeholder="51C-12345"
                          style={{
                            width: '100%',
                            padding: '8px',
                            borderRadius: '6px',
                            border: '1px solid var(--border)',
                            fontSize: '13px'
                          }}
                        />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px', color: 'var(--text-secondary)' }}>
                          👤 Tên tài xế:
                        </label>
                        <input
                          type="text"
                          value={newService.driver_name}
                          onChange={e => setNewService({...newService, driver_name: e.target.value})}
                          placeholder="Nguyễn Văn A"
                          style={{
                            width: '100%',
                            padding: '8px',
                            borderRadius: '6px',
                            border: '1px solid var(--border)',
                            fontSize: '13px'
                          }}
                        />
                      </div>
                      <div>
                        <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px', color: 'var(--text-secondary)' }}>
                          📞 SĐT tài xế:
                        </label>
                        <input
                          type="text"
                          value={newService.driver_phone}
                          onChange={e => setNewService({...newService, driver_phone: e.target.value})}
                          placeholder="0901234567"
                          style={{
                            width: '100%',
                            padding: '8px',
                            borderRadius: '6px',
                            border: '1px solid var(--border)',
                            fontSize: '13px'
                          }}
                        />
                      </div>
                      <div style={{ gridColumn: '1 / -1' }}>
                        <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px', color: 'var(--text-secondary)' }}>
                          📝 Ghi chú:
                        </label>
                        <input
                          type="text"
                          value={newService.notes}
                          onChange={e => setNewService({...newService, notes: e.target.value})}
                          placeholder="Ghi chú thêm..."
                          style={{
                            width: '100%',
                            padding: '8px',
                            borderRadius: '6px',
                            border: '1px solid var(--border)',
                            fontSize: '13px'
                          }}
                        />
                      </div>
                    </div>
                    <button
                      onClick={handleAddService}
                      disabled={saving}
                      style={{
                        marginTop: '12px',
                        padding: '10px 20px',
                        background: saving ? '#9CA3AF' : 'var(--primary)',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: saving ? 'not-allowed' : 'pointer',
                        fontSize: '13px',
                        fontWeight: '500'
                      }}
                    >
                      {saving ? '⏳ Đang thêm...' : '✓ Thêm dịch vụ'}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Đóng</button>
          {editMode && <button className="btn-primary" disabled={saving} onClick={async () => { const ok = await handleSaveAllChanges(); if (ok !== false) { setEditMode(false); onUpdate && onUpdate(); } }}>{saving ? '⏳ Đang lưu...' : '✓ Lưu thay đổi'}</button>}
        </div>
      </div>
    </div>
  )
}

// ========================================
// JOB CREATE FORM
// ========================================
function JobCreateForm({ onClose, onSuccess }) {
  const [customers, setCustomers] = useState([])
  const [formData, setFormData] = useState({
    customer_id: '',
    booking_date: new Date().toISOString().split('T')[0],
    pickup_time: '',
    service_type: 'TRUCKING_DOM',
    cargo_type: '',
    package_quantity: '',
    package_unit: 'Package (Kiện, gói)',
    weight_kg: '',
    pickup_address: '',
    delivery_address: '',
    special_requirements: ''
  })
  const [services, setServices] = useState([
    { service_type: 'TRUCKING_DOM', cargo_type: '', weight_kg: '', dimension_length_cm: '', dimension_width_cm: '', dimension_height_cm: '' }
  ])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    // Fetch customers
    const fetchCustomers = async () => {
      try {
        const res = await authFetch(`${API_URL}/api/customers`)
        if (res.ok) {
          const data = await res.json()
          setCustomers(data.customers || [])
        }
      } catch (error) {
        console.error('Failed to fetch customers:', error)
      }
    }
    fetchCustomers()
  }, [])

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleServiceChange = (idx, field, value) => {
    setServices(prev => prev.map((svc, i) => i === idx ? { ...svc, [field]: value } : svc))
  }

  const addService = () => {
    setServices(prev => [...prev, { service_type: 'TRUCKING_DOM', cargo_type: '', weight_kg: '', dimension_length_cm: '', dimension_width_cm: '', dimension_height_cm: '' }])
  }

  const removeService = (idx) => {
    if (services.length > 1) {
      setServices(prev => prev.filter((_, i) => i !== idx))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')

    try {
      const payload = {
        entities: {
          customer_id: parseInt(formData.customer_id),
          booking_date: formData.booking_date,
          pickup_time: formData.pickup_time,
          service_type: services[0]?.service_type,
          services: services.map(s => s.service_type),
          cargo_type: formData.cargo_type || services[0]?.cargo_type,
          package_quantity: parseInt(formData.package_quantity) || null,
          package_unit: formData.package_unit,
          weight_kg: parseFloat(formData.weight_kg) || null,
          pickup_address: formData.pickup_address,
          delivery_address: formData.delivery_address,
          special_requirements: formData.special_requirements
        },
        enriched_data: {
          customer_id: parseInt(formData.customer_id),
          customer_matched: true
        }
      }

      const res = await authFetch(`${API_URL}/api/jobs/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      const result = await res.json()
      if (!result.success) {
        throw new Error(result.message || 'Failed to create job')
      }

      onSuccess && onSuccess(result)
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content large" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">📋 Tạo Job Mới</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && <div className="error-alert">{error}</div>}

            {/* Customer & Date */}
            <div className="form-section">
              <h3>Thông tin cơ bản</h3>
              <div className="form-grid">
                <div className="form-group">
                  <label>Khách hàng *</label>
                  <select name="customer_id" value={formData.customer_id} onChange={handleInputChange} required>
                    <option value="">-- Chọn khách hàng --</option>
                    {customers.map(c => (
                      <option key={c.customer_id} value={c.customer_id}>
                        {c.customer_code} - {c.short_name || c.full_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Ngày booking *</label>
                  <input type="date" name="booking_date" value={formData.booking_date} onChange={handleInputChange} required />
                </div>
                <div className="form-group">
                  <label>Giờ lấy hàng</label>
                  <input type="time" name="pickup_time" value={formData.pickup_time} onChange={handleInputChange} />
                </div>
              </div>
            </div>

            {/* Cargo Info */}
            <div className="form-section">
              <h3>Thông tin hàng hóa</h3>
              <div className="form-grid">
                <div className="form-group">
                  <label>Loại hàng</label>
                  <input type="text" name="cargo_type" value={formData.cargo_type} onChange={handleInputChange} placeholder="VD: PCB, FPC, Electronics" />
                </div>
                <div className="form-group">
                  <label>Số kiện</label>
                  <input type="number" name="package_quantity" value={formData.package_quantity} onChange={handleInputChange} placeholder="VD: 10" />
                </div>
                <div className="form-group">
                  <label>Đơn vị</label>
                  <select name="package_unit" value={formData.package_unit} onChange={handleInputChange}>
                    <optgroup label="Phổ biến">
                      <option value="Carton (Thùng carton)">Carton (Thùng carton)</option>
                      <option value="Pallet & Package">Pallet & Package</option>
                      <option value="Box (Hộp)">Box (Hộp)</option>
                      <option value="Package (Kiện, gói)">Package (Kiện, gói)</option>
                      <option value="Case (Thùng)">Case (Thùng)</option>
                      <option value="Bundle (Gói)">Bundle (Gói)</option>
                      <option value="Roll(Cuộn)">Roll (Cuộn)</option>
                      <option value="Container">Container</option>
                      <option value="Piece">Piece</option>
                    </optgroup>
                    <optgroup label="Tất cả">
                      <option value="Bag (Túi)">Bag (Túi)</option>
                      <option value="Bale,compressed (Gói dạng nén)">Bale, compressed</option>
                      <option value="Bale,non-compressed (Gói không nén)">Bale, non-compressed</option>
                      <option value="Bar (Thanh)">Bar (Thanh)</option>
                      <option value="Barrel (Thùng)">Barrel (Thùng)</option>
                      <option value="Basket (Giỏ)">Basket (Giỏ)</option>
                      <option value="Cage (Lồng)">Cage (Lồng)</option>
                      <option value="Can, cylindrical (Hộp hình trụ)">Can, cylindrical</option>
                      <option value="Can, rectangular (Thùng, hình hộp chữ nhật)">Can, rectangular</option>
                      <option value="Carboy, non-protected (Chai, không được bảo vệ)">Carboy, non-protected</option>
                      <option value="Carboy, protected (Chai đựng axit)">Carboy, protected</option>
                      <option value="Cask (Thùng tô nô)">Cask (Thùng tô nô)</option>
                      <option value="Coil (Cuốn)">Coil (Cuốn)</option>
                      <option value="Crate (Giỏ)">Crate (Giỏ)</option>
                      <option value="Cylinder (Xylanh)">Cylinder (Xylanh)</option>
                      <option value="Drum (Thùng)">Drum (Thùng)</option>
                      <option value="Keg (Thùng đựng cá mòi muối)">Keg</option>
                      <option value="Log (Khúc gỗ)">Log (Khúc gỗ)</option>
                      <option value="Logs, in bundle/bunch/truss">Logs, in bundle</option>
                      <option value="MST">MST</option>
                      <option value="Mat (Thảm)">Mat (Thảm)</option>
                      <option value="Net (Cuộn)">Net (Cuộn)</option>
                      <option value="Packet (Gói)">Packet (Gói)</option>
                      <option value="Pail (Thùng đựng nước)">Pail</option>
                      <option value="Parcel (Lô, bưu kiện, gói hàng)">Parcel (Bưu kiện)</option>
                      <option value="Pen (Lồng)">Pen (Lồng)</option>
                      <option value="Pipe (ống)">Pipe (Ống)</option>
                      <option value="Plate (Đĩa)">Plate (Đĩa)</option>
                      <option value="Tank (Thùng, két, bể chứa hình trụ)">Tank (Bể chứa)</option>
                      <option value="Tray (Khay)">Tray (Khay)</option>
                      <option value="Unpacked or unpackaged (Hàng rời, không đóng gói)">Unpacked (Hàng rời)</option>
                      <option value="Other (Loại khác)">Other (Loại khác)</option>
                    </optgroup>
                  </select>
                </div>
                <div className="form-group">
                  <label>Khối lượng (kg)</label>
                  <input type="number" name="weight_kg" value={formData.weight_kg} onChange={handleInputChange} placeholder="VD: 500" />
                </div>
              </div>
            </div>

            {/* Addresses */}
            <div className="form-section">
              <h3>Địa chỉ</h3>
              <div className="form-grid cols-2">
                <div className="form-group">
                  <label>Điểm lấy hàng</label>
                  <input type="text" name="pickup_address" value={formData.pickup_address} onChange={handleInputChange} placeholder="VD: KCN Quang Minh" />
                </div>
                <div className="form-group">
                  <label>Điểm giao hàng</label>
                  <input type="text" name="delivery_address" value={formData.delivery_address} onChange={handleInputChange} placeholder="VD: Sân bay Nội Bài" />
                </div>
              </div>
            </div>

            {/* Services */}
            <div className="form-section">
              <div className="section-header">
                <h3>Dịch vụ ({services.length})</h3>
                <button type="button" className="btn-add" onClick={addService}>+ Thêm dịch vụ</button>
              </div>
              {services.map((svc, idx) => (
                <div key={idx} className="service-form-card">
                  <div className="service-form-header">
                    <span>Dịch vụ #{idx + 1}</span>
                    {services.length > 1 && (
                      <button type="button" className="btn-remove" onClick={() => removeService(idx)}>✕</button>
                    )}
                  </div>
                  <div className="form-grid">
                    <div className="form-group">
                      <label>Loại dịch vụ</label>
                      <select value={svc.service_type} onChange={e => handleServiceChange(idx, 'service_type', e.target.value)}>
                        <optgroup label="🚚 Vận tải Đường bộ">
                          <option value="TRUCKING_DOM">Vận tải nội địa</option>
                          <option value="BORDER_IMP">Nhập khẩu đường bộ</option>
                        </optgroup>
                        <optgroup label="✈️ Hàng không">
                          <option value="AIR_IMP">Hàng không - Nhập</option>
                          <option value="AIR_EXP">Hàng không - Xuất</option>
                        </optgroup>
                        <optgroup label="🚢 Đường biển">
                          <option value="SEA_IMP">Đường biển - Nhập</option>
                          <option value="SEA_EXP">Đường biển - Xuất</option>
                        </optgroup>
                        <optgroup label="🏭 Kho bãi">
                          <option value="WHS_STORAGE">Lưu kho</option>
                          <option value="WHS_HANDLE">Bốc xếp</option>
                          <option value="WHS_VAS">Dịch vụ gia tăng (VAS)</option>
                        </optgroup>
                        <optgroup label="📋 Khai quan">
                          <option value="CUS_IMPORT">Khai quan Nhập</option>
                          <option value="CUS_EXPORT">Khai quan Xuất</option>
                          <option value="CUS_TRANSIT">Quá cảnh</option>
                          <option value="CUS_CO">Chứng nhận xuất xứ (C/O)</option>
                        </optgroup>
                        <optgroup label="📦 Đóng gói">
                          <option value="SVC_PACK">Đóng gói</option>
                          <option value="SVC_FUMI">Hun trùng</option>
                          <option value="SVC_VACUUM">Hút chân không</option>
                          <option value="SVC_SHRINK">Màng co</option>
                          <option value="SVC_LASHING">Chằng buộc</option>
                        </optgroup>
                        <optgroup label="🏗️ Nâng hạ">
                          <option value="LIFT_ON">Nâng cont/hàng</option>
                          <option value="LIFT_OFF">Hạ cont/hàng</option>
                        </optgroup>
                        <optgroup label="💰 Phí phát sinh">
                          <option value="SVC_WAITING">Phí chờ giờ</option>
                          <option value="SVC_CANCEL_FEE">Phí huỷ chuyến</option>
                          <option value="SVC_SURCHARGE">Phí phát sinh khác</option>
                        </optgroup>
                        <optgroup label="📌 Khác">
                          <option value="SVC_OTHER">Dịch vụ khác</option>
                        </optgroup>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Mô tả hàng</label>
                      <input type="text" value={svc.cargo_type} onChange={e => handleServiceChange(idx, 'cargo_type', e.target.value)} placeholder="VD: CNC Main Unit" />
                    </div>
                    <div className="form-group">
                      <label>Khối lượng (kg)</label>
                      <input type="number" value={svc.weight_kg} onChange={e => handleServiceChange(idx, 'weight_kg', e.target.value)} />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Notes */}
            <div className="form-section">
              <h3>Ghi chú</h3>
              <textarea name="special_requirements" value={formData.special_requirements} onChange={handleInputChange} placeholder="Yêu cầu đặc biệt..." rows={3} />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn-secondary" onClick={onClose}>Hủy</button>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? 'Đang tạo...' : '✓ Tạo Job'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ========================================
// CHAT WINDOW (with Drag-Drop & File Upload)
// ========================================

// ========================================
// USER MENU COMPONENT
// ========================================
function UserMenu() {
  const { user, logout, isAdmin } = useAuth()
  const [showMenu, setShowMenu] = useState(false)

  if (!user) return null

  const initials = user.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : user.user_code?.slice(0, 2) || 'U'

  return (
    <div className="user-menu-container">
      <div className="user-avatar" onClick={() => setShowMenu(!showMenu)}>
        {initials}
      </div>
      {showMenu && (
        <div className="user-dropdown">
          <div className="user-dropdown-header">
            <div className="user-name">{user.full_name}</div>
            <div className="user-role">{user.role}</div>
          </div>
          <div className="user-dropdown-divider" />
          <button className="user-dropdown-item" onClick={logout}>
            Đăng xuất
          </button>
        </div>
      )}
    </div>
  )
}

// ========================================
// MAIN DASHBOARD COMPONENT
// ========================================
function App() {
  const { isAuthenticated, loading: authLoading } = useAuth()

  // Show login page if not authenticated
  if (authLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Đang tải...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <LoginPage />
  }

  return <MainDashboard />
}

function MainDashboard() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [chatOpen, setChatOpen] = useState(false)
  const [activeNav, setActiveNav] = useState('dashboard')
  const [stats, setStats] = useState({ jobs_today: 0, trucking: 0, warehouse: 0, revenue: '0', status_counts: {} })
  const [recentJobs, setRecentJobs] = useState([])
  const [serviceData, setServiceData] = useState([])
  const [loading, setLoading] = useState(true)

  // Filter states
  const [statusFilter, setStatusFilter] = useState('')

  // Modal states
  const [selectedJob, setSelectedJob] = useState(null)
  const [showJobDetail, setShowJobDetail] = useState(false)
  const [showJobCreate, setShowJobCreate] = useState(false)

  // ========================================
  // KEYBOARD SHORTCUTS
  // ========================================
  useEffect(() => {
    const handleGlobalKeyDown = (e) => {
      // Skip if user is typing in an input/textarea
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
        // Only handle Escape in inputs
        if (e.key === 'Escape') {
          e.target.blur()
          setChatOpen(false)
          setShowJobDetail(false)
          setShowJobCreate(false)
        }
        return
      }

      // Ctrl/Cmd + K: Toggle AI Chat
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        setChatOpen(prev => !prev)
      }
      // Ctrl/Cmd + N: New Job
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault()
        setShowJobCreate(true)
      }
      // Ctrl/Cmd + F: Focus Search
      if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault()
        document.querySelector('.search-input')?.focus()
      }
      // Escape: Close modals
      if (e.key === 'Escape') {
        setChatOpen(false)
        setShowJobDetail(false)
        setShowJobCreate(false)
      }
      // Number keys 1-9: Quick navigation
      if (!e.ctrlKey && !e.metaKey && !e.altKey && !e.shiftKey) {
        const navMap = {
          '1': 'dashboard',
          '2': 'jobs',
          '3': 'trucking',
          '4': 'container',
          '5': 'warehouse',
          '6': 'customs',
          '7': 'packing',
          '8': 'master',
          '9': 'financial'
        }
        if (navMap[e.key]) {
          setActiveNav(navMap[e.key])
        }
      }
    }

    document.addEventListener('keydown', handleGlobalKeyDown)
    return () => document.removeEventListener('keydown', handleGlobalKeyDown)
  }, [])

  // Fetch dashboard data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const statsRes = await authFetch(`${API_URL}/api/dashboard/stats`)
        if (statsRes.ok) {
          const statsData = await statsRes.json()
          setStats(statsData)
        }

        const jobsRes = await authFetch(`${API_URL}/api/jobs/recent?limit=10`)
        if (jobsRes.ok) {
          const jobsData = await jobsRes.json()
          setRecentJobs(jobsData.jobs || [])
        }
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  // Fetch filtered jobs when status filter changes
  useEffect(() => {
    if (activeNav === 'jobs' && statusFilter) {
      authFetch(`${API_URL}/api/jobs/recent?limit=100&status=${statusFilter}`)
        .then(r => r.json())
        .then(data => setRecentJobs(data.jobs || []))
        .catch(err => console.error('Failed to fetch filtered jobs:', err))
    }
  }, [activeNav, statusFilter])

  // Fetch service-specific data
  useEffect(() => {
    const fetchServiceData = async () => {
      const serviceNavs = ['trucking', 'container', 'air', 'sea', 'warehouse', 'handling', 'customs', 'co', 'packing', 'special']
      if (serviceNavs.includes(activeNav)) {
        try {
          const res = await authFetch(`${API_URL}/api/services/${activeNav}`)
          if (res.ok) {
            const data = await res.json()
            setServiceData(data.services || [])
          }
        } catch (error) {
          console.error(`Failed to fetch ${activeNav} data:`, error)
        }
      }
    }
    fetchServiceData()
  }, [activeNav])

  const getServiceIcon = (type) => {
    const icons = {
      // Road Transport
      trucking: '🚚', TRUCKING_DOM: '🚚', BORDER_IMP: '🛣️',
      container: '🏗️', LIFT_ON: '⬆️', LIFT_OFF: '⬇️',
      // Air Freight
      air: '✈️', AIR_IMP: '✈️', AIR_EXP: '✈️',
      // Sea Freight
      sea: '🚢', SEA_IMP: '🚢', SEA_EXP: '🚢',
      // Warehouse
      warehouse: '🏭', WHS_STORAGE: '🏭', WHS_VAS: '✨',
      handling: '📥', WHS_HANDLE: '📥',
      // Customs
      customs: '🛃', CUS_IMPORT: '📥', CUS_EXPORT: '📤', CUS_TRANSIT: '🔄',
      co: '📜', CUS_CO: '📜',
      // Value-Added
      packing: '📦', SVC_PACK: '📦',
      special: '🔧', SVC_FUMI: '🧪', SVC_VACUUM: '💨', SVC_SHRINK: '🎁', SVC_LASHING: '🔗',
    }
    return icons[type] || '📋'
  }

  const handleViewJob = (job) => {
    // Ensure we have job_id - it might be named differently in different views
    const jobId = job.job_id || job.svc_job_id || job.id
    if (!jobId) {
      console.error('Missing job_id in job data:', job)
      alert('Không tìm thấy job ID')
      return
    }
    setSelectedJob({ ...job, job_id: jobId })
    setShowJobDetail(true)
  }

  const handleJobCreated = (result) => {
    // Refresh data
    authFetch(`${API_URL}/api/jobs/recent?limit=10`)
      .then(res => res.json())
      .then(data => setRecentJobs(data.jobs || []))
  }

  // Status colors for chart
  const statusColors = {
    PENDING: theme.warning,
    CONFIRMED: theme.primary,
    DISPATCHED: '#8B5CF6',
    IN_TRANSIT: '#8B5CF6',
    COMPLETED: theme.success,
    CANCELLED: theme.accentRed
  }

  return (
    <div className="dashboard-app">
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'collapsed'}`}>
        <div className="sidebar-logo">
          <img src="/logo.png" alt="5P Vietnam" className="logo-img" />
        </div>

        <nav className="sidebar-nav">
          <NavItem icon="📊" label="Dashboard" active={activeNav === 'dashboard'} onClick={() => setActiveNav('dashboard')} />
          <NavItem icon="📋" label="All Jobs" active={activeNav === 'jobs'} onClick={() => setActiveNav('jobs')} badge={stats.jobs_today || null} />

          <div className="nav-divider" />
          <div className="nav-section-title">LOGISTICS</div>
          <NavItem icon="🚚" label="Trucking" active={activeNav === 'trucking'} onClick={() => setActiveNav('trucking')} />
          <NavItem icon="✈️" label="Air Freight" active={activeNav === 'air'} onClick={() => setActiveNav('air')} />
          <NavItem icon="🚢" label="Sea Freight" active={activeNav === 'sea'} onClick={() => setActiveNav('sea')} />
          <NavItem icon="🏗️" label="Container" active={activeNav === 'container'} onClick={() => setActiveNav('container')} />

          <div className="nav-divider" />
          <div className="nav-section-title">WAREHOUSE</div>
          <NavItem icon="🏭" label="Storage" active={activeNav === 'warehouse'} onClick={() => setActiveNav('warehouse')} />
          <NavItem icon="📥" label="Handling" active={activeNav === 'handling'} onClick={() => setActiveNav('handling')} />

          <div className="nav-divider" />
          <div className="nav-section-title">CUSTOMS</div>
          <NavItem icon="🛃" label="Clearance" active={activeNav === 'customs'} onClick={() => setActiveNav('customs')} />
          <NavItem icon="📜" label="C/O" active={activeNav === 'co'} onClick={() => setActiveNav('co')} />

          <div className="nav-divider" />
          <div className="nav-section-title">VALUE-ADDED</div>
          <NavItem icon="📦" label="Packing" active={activeNav === 'packing'} onClick={() => setActiveNav('packing')} />
          <NavItem icon="🔧" label="Special" active={activeNav === 'special'} onClick={() => setActiveNav('special')} />

          <div className="nav-divider" />
          <div className="nav-section-title">MANAGEMENT</div>
          <NavItem icon="👥" label="Master Data" active={activeNav === 'master'} onClick={() => setActiveNav('master')} />
          <NavItem icon="💰" label="Financial" active={activeNav === 'financial'} onClick={() => setActiveNav('financial')} />
          <NavItem icon="📈" label="Reports" active={activeNav === 'reports'} onClick={() => setActiveNav('reports')} />
        </nav>

        <div className="sidebar-footer">
          <NavItem icon="⚙️" label="Settings" active={activeNav === 'settings'} onClick={() => setActiveNav('settings')} />
        </div>
      </aside>

      {/* Main Content */}
      <main className={`main-content ${sidebarOpen ? '' : 'expanded'}`}>
        <header className="main-header">
          <div className="header-left">
            <button className="menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>☰</button>
            <div>
              <h1 className="page-title">{activeNav.charAt(0).toUpperCase() + activeNav.slice(1)}</h1>
              <p className="page-subtitle">Welcome back! Here's your logistics overview.</p>
            </div>
          </div>
          <div className="header-right">
            <SearchBox onJobSelect={(job) => {
              setSelectedJob(job)
              setShowJobDetail(true)
            }} />
            <UserMenu />
          </div>
        </header>

        {/* Dashboard Content */}
        {activeNav === 'dashboard' && (
          <div className="dashboard-content">
            <div className="stats-grid">
              <StatsCard icon="📋" label="Jobs Today" value={stats.jobs_today || 0} color={theme.primary} />
              <StatsCard icon="🚚" label="Active Trucking" value={stats.trucking || 0} color={theme.accent} />
              <StatsCard icon="🏭" label="In Storage" value={stats.warehouse || 0} color="#8B5CF6" />
              <StatsCard icon="📈" label="Doanh thu" value={stats.revenue || '0'} color={theme.success} />
            </div>

            <div className="dashboard-grid">
              {/* Jobs by Status - REAL DATA */}
              <div className="card jobs-status-card">
                <h3 className="card-title">Jobs by Status</h3>
                <div className="status-bars">
                  {Object.entries(stats.status_counts || {}).map(([status, count], i) => (
                    <div key={i} className="status-bar-row" style={{ cursor: 'pointer' }}
                      onClick={() => { setStatusFilter(status); setActiveNav('jobs') }}
                      title={`Click để xem jobs ${status}`}>
                      <div className="status-indicator" style={{ backgroundColor: statusColors[status] || theme.primary }} />
                      <span className="status-label">{status.replace(/_/g, ' ')}</span>
                      <span className="status-value">{count}</span>
                      <div className="status-bar-bg">
                        <div className="status-bar-fill" style={{ width: `${Math.min(count * 10, 100)}%`, backgroundColor: statusColors[status] || theme.primary }} />
                      </div>
                    </div>
                  ))}
                  {Object.keys(stats.status_counts || {}).length === 0 && (
                    <div className="no-data">Không có dữ liệu</div>
                  )}
                </div>
              </div>

              {/* Recent Jobs */}
              <div className="card recent-jobs-card">
                <div className="card-header">
                  <h3 className="card-title">Recent Jobs</h3>
                  <button className="view-all-btn" onClick={() => setActiveNav('jobs')}>View All →</button>
                </div>
                <table className="jobs-table">
                  <thead>
                    <tr>
                      <th>Job No</th>
                      <th>Customer</th>
                      <th>Type</th>
                      <th>Date</th>
                      <th>Người tạo</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentJobs.length > 0 ? recentJobs.slice(0, 5).map((job, i) => (
                      <tr key={i} onClick={() => handleViewJob(job)} style={{ cursor: 'pointer' }}>
                        <td className="job-number">{job.job_no}</td>
                        <td>{job.customer_code || job.customer_name}</td>
                        <td><span className="job-type">{getServiceIcon(job.service_type)} {job.service_type?.replace(/_/g, ' ')}</span></td>
                        <td>{job.etd || job.created_at?.split('T')[0]}</td>
                        <td>{job.creator_name || '-'}</td>
                        <td><StatusBadge status={job.status_code || 'PENDING'} /></td>
                      </tr>
                    )) : (
                      <tr><td colSpan="6" className="no-data">No recent jobs</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Service Views */}
        {['trucking', 'container', 'air', 'sea', 'warehouse', 'handling', 'customs', 'co', 'packing', 'special'].includes(activeNav) && (
          <div className="service-content">
            <div className="card full-width">
              <div className="card-header">
                <h3 className="card-title">{getServiceIcon(activeNav)} {activeNav.charAt(0).toUpperCase() + activeNav.slice(1)} Services</h3>
                <div className="header-actions">
                  {/* Export Button with Month Filter */}
                  <div className="export-section">
                    <input
                      type="month"
                      className="export-month-input"
                      onChange={(e) => {
                        const month = e.target.value
                        if (month) {
                          window.open(`${API_URL}/api/jobs/export/${activeNav}?month=${month}`, '_blank')
                        }
                      }}
                      title="Chọn tháng để xuất Excel"
                    />
                    <button
                      className="export-btn"
                      onClick={() => window.open(`${API_URL}/api/jobs/export/${activeNav}`, '_blank')}
                      title="Xuất tất cả ra Excel"
                    >
                      📥 Xuất Excel
                    </button>
                  </div>
                  <button className="add-job-btn" onClick={() => setShowJobCreate(true)}>+ New Job</button>
                </div>
              </div>

              <table className="services-table">
                <thead>
                  <tr>
                    <th>Job No</th>
                    <th>Customer</th>
                    <th>Assigned To</th>
                    <th>Date</th>
                    <th>Details</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {serviceData.length > 0 ? serviceData.map((svc, i) => (
                    <tr key={i} onClick={() => handleViewJob(svc)} style={{ cursor: 'pointer' }} className="job-row-clickable">
                      <td className="job-number">{svc.job_no}</td>
                      <td>{svc.customer || svc.customer_code}</td>
                      <td>
                        <span className={`assigned-badge ${svc.assignment_type === 'UNASSIGNED' ? 'unassigned' : svc.assignment_type?.toLowerCase()}`}>
                          {svc.assignment_type === 'VENDOR' && '🏢 '}
                          {svc.assignment_type === 'EMPLOYEE' && '👤 '}
                          {svc.assigned_to || 'Chưa gán'}
                        </span>
                      </td>
                      <td>{svc.scheduled_date || svc.etd}</td>
                      <td className="service-details">
                        {svc.cargo_type && <span>{svc.cargo_type}</span>}
                        {svc.weight_kg && <span> • {svc.weight_kg}kg</span>}
                        {svc.package_quantity && <span> • {svc.package_quantity} {svc.package_unit || 'pcs'}</span>}
                      </td>
                      <td><StatusBadge status={svc.status_code || 'PENDING'} /></td>
                      <td>
                        <button className="action-btn" onClick={(e) => { e.stopPropagation(); handleViewJob(svc); }}>View</button>
                      </td>
                    </tr>
                  )) : (
                    <tr><td colSpan="7" className="no-data">No {activeNav} services found</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Jobs List View */}
        {activeNav === 'jobs' && (
          <div className="service-content">
            <div className="card full-width">
              <div className="card-header">
                <h3 className="card-title">
                  📋 All Jobs
                  {statusFilter && (
                    <span style={{ fontSize: '0.75em', marginLeft: '8px', padding: '2px 8px', borderRadius: '12px', backgroundColor: statusColors[statusFilter] || theme.primary, color: '#fff' }}>
                      {statusFilter.replace(/_/g, ' ')}
                      <span style={{ marginLeft: '6px', cursor: 'pointer' }} onClick={() => {
                        setStatusFilter('')
                        authFetch(`${API_URL}/api/jobs/recent?limit=10`).then(r => r.json()).then(d => setRecentJobs(d.jobs || []))
                      }}>✕</span>
                    </span>
                  )}
                </h3>
                <button className="add-job-btn" onClick={() => setShowJobCreate(true)}>+ New Job</button>
              </div>
              <table className="services-table">
                <thead>
                  <tr>
                    <th>Job No</th>
                    <th>Customer</th>
                    <th>Service Type</th>
                    <th>Date</th>
                    <th>Người tạo</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {recentJobs.length > 0 ? recentJobs.map((job, i) => (
                    <tr key={i} onClick={() => handleViewJob(job)} style={{ cursor: 'pointer' }} className="job-row-clickable">
                      <td className="job-number">{job.job_no}</td>
                      <td>{job.customer_code || job.customer_name}</td>
                      <td>{getServiceIcon(job.service_type)} {job.service_type}</td>
                      <td>{job.etd || job.created_at?.split('T')[0]}</td>
                      <td>{job.creator_name || '-'}</td>
                      <td><StatusBadge status={job.status_code || 'PENDING'} /></td>
                      <td>
                        <button className="action-btn" onClick={(e) => { e.stopPropagation(); handleViewJob(job); }}>View</button>
                      </td>
                    </tr>
                  )) : (
                    <tr><td colSpan="7" className="no-data">No jobs found</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Master Data / Admin Panel */}
        {activeNav === 'master' && <AdminPanel />}
      </main>

      {/* Floating AI Button */}
      <FloatingAIButton onClick={() => setChatOpen(!chatOpen)} hasNotification={!chatOpen} />

      {/* Chat Window */}
      <ChatWindow isOpen={chatOpen} onClose={() => setChatOpen(false)} />

      {/* Job Detail Modal */}
      {showJobDetail && <JobDetailModal job={selectedJob} onClose={() => setShowJobDetail(false)} onUpdate={() => {
        // Refresh recent jobs list after quotation save
        authFetch(`${API_URL}/api/jobs/recent?limit=10`).then(r => r.json()).then(d => setRecentJobs(d.jobs || []))
      }} />}

      {/* Job Create Form */}
      {showJobCreate && <JobCreateForm onClose={() => setShowJobCreate(false)} onSuccess={handleJobCreated} />}
    </div>
  )
}

// Wrap App with AuthProvider
function AppWithAuth() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  )
}

export default AppWithAuth
