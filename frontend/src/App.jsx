import { useState, useEffect, useRef } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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
    PENDING: { bg: '#FEF3C7', color: '#D97706', label: 'Pending' },
    CONFIRMED: { bg: '#DBEAFE', color: '#2563EB', label: 'Confirmed' },
    DISPATCHED: { bg: '#E0E7FF', color: '#4F46E5', label: 'Dispatched' },
    IN_TRANSIT: { bg: '#DBEAFE', color: '#2563EB', label: 'In Transit' },
    DELIVERED: { bg: '#D1FAE5', color: '#059669', label: 'Delivered' },
    COMPLETED: { bg: '#D1FAE5', color: '#059669', label: 'Completed' },
    CANCELLED: { bg: '#FEE2E2', color: '#DC2626', label: 'Cancelled' },
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
// JOB DETAIL MODAL (with Edit Mode)
// ========================================
function JobDetailModal({ job, onClose, onUpdate }) {
  const [services, setServices] = useState([])
  const [loading, setLoading] = useState(true)
  const [editMode, setEditMode] = useState(false)
  const [vendors, setVendors] = useState([])
  const [employees, setEmployees] = useState([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const fetchJobDetails = async () => {
      if (!job?.job_id) return
      try {
        const res = await fetch(`${API_URL}/api/jobs/${job.job_id}/details`)
        if (res.ok) {
          const data = await res.json()
          setServices(data.services || [])
        }
      } catch (error) {
        console.error('Failed to fetch job details:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchJobDetails()
  }, [job])

  useEffect(() => {
    if (editMode) {
      // Fetch vendors and employees for dropdowns
      fetch(`${API_URL}/api/vendors`).then(r => r.json()).then(d => setVendors(d.vendors || []))
      fetch(`${API_URL}/api/employees`).then(r => r.json()).then(d => setEmployees(d.employees || []))
    }
  }, [editMode])

  const handleAssign = async (svc_id, vendor_id, employee_id) => {
    setSaving(true)
    try {
      const res = await fetch(`${API_URL}/api/services/${svc_id}/assign`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vendor_id, employee_id })
      })
      const result = await res.json()
      if (result.success) {
        // Update local state
        setServices(prev => prev.map(s =>
          s.svc_id === svc_id ? {
            ...s, vendor_id, employee_id,
            vendor_name: vendors.find(v => v.vendor_id === vendor_id)?.short_name,
            employee_name: employees.find(e => e.employee_id === employee_id)?.short_name
          } : s
        ))
      }
    } catch (error) {
      console.error('Failed to assign:', error)
    } finally {
      setSaving(false)
    }
  }

  if (!job) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content large" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2 className="modal-title">📋 {job.job_no}</h2>
            <p className="modal-subtitle">{job.customer || job.customer_name || job.customer_code}</p>
          </div>
          <StatusBadge status={job.status_code || 'PENDING'} />
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
            <div className="detail-grid">
              <div className="detail-item">
                <span className="detail-label">Khách hàng:</span>
                <span className="detail-value">{job.customer || job.customer_name || job.customer_code}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Ngày tạo:</span>
                <span className="detail-value">{job.created_at?.split('T')[0]}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Ngày thực hiện:</span>
                <span className="detail-value">{job.scheduled_date || job.etd || '-'}</span>
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
                      <span className="service-type-badge">{svc.service_type_code}</span>
                      <StatusBadge status={svc.status_code || 'PENDING'} />
                    </div>

                    {/* Assignment info - Editable */}
                    <div className="service-assignment">
                      <strong>Người xử lý:</strong>
                      {editMode ? (
                        <div className="assign-controls">
                          {/* Searchable Vendor Dropdown */}
                          <div className="vendor-search-wrapper" style={{ position: 'relative', display: 'inline-block' }}>
                            <input
                              type="text"
                              placeholder="🔍 Tìm vendor..."
                              value={svc.vendorSearch || ''}
                              onChange={(e) => {
                                const searchValue = e.target.value
                                setJobDetail(prev => ({
                                  ...prev,
                                  services: prev.services.map(s =>
                                    s.svc_id === svc.svc_id ? { ...s, vendorSearch: searchValue, showVendorDropdown: true } : s
                                  )
                                }))
                              }}
                              onFocus={() => {
                                setJobDetail(prev => ({
                                  ...prev,
                                  services: prev.services.map(s =>
                                    s.svc_id === svc.svc_id ? { ...s, showVendorDropdown: true } : s
                                  )
                                }))
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
                                  onClick={() => {
                                    handleAssign(svc.svc_id, null, null)
                                    setJobDetail(prev => ({
                                      ...prev,
                                      services: prev.services.map(s =>
                                        s.svc_id === svc.svc_id ? { ...s, showVendorDropdown: false, vendorSearch: '' } : s
                                      )
                                    }))
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
                                    onClick={() => {
                                      handleAssign(svc.svc_id, v.vendor_id, null)
                                      setJobDetail(prev => ({
                                        ...prev,
                                        services: prev.services.map(s =>
                                          s.svc_id === svc.svc_id ? { ...s, showVendorDropdown: false, vendorSearch: '', vendor_name: v.short_name || v.company_name } : s
                                        )
                                      }))
                                    }}
                                  >
                                    🏢 {v.short_name || v.company_name}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                          <span>hoặc</span>
                          <select
                            value={svc.employee_id || ''}
                            onChange={e => handleAssign(svc.svc_id, null, e.target.value ? parseInt(e.target.value) : null)}
                            disabled={saving}
                          >
                            <option value="">-- Nhân viên --</option>
                            {employees.map(e => (
                              <option key={e.employee_id} value={e.employee_id}>👤 {e.full_name}</option>
                            ))}
                          </select>
                        </div>
                      ) : (
                        <span className={`assigned-badge ${svc.vendor_id ? 'vendor' : svc.employee_id ? 'employee' : 'unassigned'}`}>
                          {svc.vendor_id ? '🏢 ' : svc.employee_id ? '👤 ' : ''}
                          {svc.vendor_name || svc.employee_name || 'Chưa gán'}
                        </span>
                      )}
                    </div>

                    <div className="service-details-grid">
                      {svc.cargo_type && <div><strong>Hàng:</strong> {svc.cargo_type}</div>}
                      {svc.weight_kg && <div><strong>Khối lượng:</strong> {svc.weight_kg}kg</div>}
                      {svc.package_quantity && <div><strong>Số kiện:</strong> {svc.package_quantity} {svc.package_unit || 'pcs'}</div>}
                      {svc.origin_address && <div><strong>Điểm đi:</strong> {svc.origin_address}</div>}
                      {svc.dest_address && <div><strong>Điểm đến:</strong> {svc.dest_address}</div>}
                      {svc.scheduled_date && <div><strong>Ngày:</strong> {svc.scheduled_date}</div>}
                      {svc.scheduled_time && <div><strong>Giờ:</strong> {svc.scheduled_time}</div>}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-data">Không có dịch vụ</div>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Đóng</button>
          {editMode && <button className="btn-primary" onClick={() => { setEditMode(false); onUpdate && onUpdate(); }}>✓ Lưu thay đổi</button>}
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
    service_type: 'TRUCKING_SHORT',
    cargo_type: '',
    package_quantity: '',
    package_unit: 'kiện',
    weight_kg: '',
    pickup_address: '',
    delivery_address: '',
    special_requirements: ''
  })
  const [services, setServices] = useState([
    { service_type: 'TRUCKING_SHORT', cargo_type: '', weight_kg: '', dimension_length_cm: '', dimension_width_cm: '', dimension_height_cm: '' }
  ])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    // Fetch customers
    const fetchCustomers = async () => {
      try {
        const res = await fetch(`${API_URL}/api/customers`)
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
    setServices(prev => [...prev, { service_type: 'TRUCKING_SHORT', cargo_type: '', weight_kg: '', dimension_length_cm: '', dimension_width_cm: '', dimension_height_cm: '' }])
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

      const res = await fetch(`${API_URL}/api/jobs/create`, {
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
                    <option value="kiện">Kiện</option>
                    <option value="thùng">Thùng</option>
                    <option value="pallet">Pallet</option>
                    <option value="container">Container</option>
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
                        <option value="TRUCKING_SHORT">🚚 Trucking Nội vùng</option>
                        <option value="TRUCKING_LONG">🚛 Trucking Liên tỉnh</option>
                        <option value="WHS_STORAGE">🏭 Lưu kho</option>
                        <option value="WHS_HANDLE">📦 Bốc xếp</option>
                        <option value="CUS_IMPORT">📥 Khai quan Nhập</option>
                        <option value="CUS_EXPORT">📤 Khai quan Xuất</option>
                        <option value="SVC_PACK">📦 Đóng gói</option>
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
const CHAT_STORAGE_KEY = 'slms_chat_history'
const CHAT_RETENTION_DAYS = 15

function ChatWindow({ isOpen, onClose }) {
  const [messages, setMessages] = useState(() => {
    // Load from localStorage on initial mount
    try {
      const saved = localStorage.getItem(CHAT_STORAGE_KEY)
      if (saved) {
        const { messages: savedMessages, timestamp } = JSON.parse(saved)
        // Check if within retention period
        const savedDate = new Date(timestamp)
        const now = new Date()
        const diffDays = (now - savedDate) / (1000 * 60 * 60 * 24)
        if (diffDays < CHAT_RETENTION_DAYS) {
          return savedMessages || []
        }
      }
    } catch (e) {
      console.error('Failed to load chat history:', e)
    }
    return []
  })
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [attachedFile, setAttachedFile] = useState(null)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const fileInputRef = useRef(null)

  // Edit mode state
  const [editingMsgIndex, setEditingMsgIndex] = useState(null)
  const [editFormData, setEditFormData] = useState({})
  const [customers, setCustomers] = useState([])
  const [customerSearch, setCustomerSearch] = useState('')
  const [showCustomerDropdown, setShowCustomerDropdown] = useState(false)

  // Fetch customers list
  useEffect(() => {
    fetch(`${API_URL}/api/chat/search-customers`)
      .then(res => res.json())
      .then(data => setCustomers(data.customers || []))
      .catch(err => console.error('Failed to load customers:', err))
  }, [])

  // Save to localStorage when messages change
  useEffect(() => {
    if (messages.length > 0) {
      try {
        localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify({
          messages,
          timestamp: new Date().toISOString()
        }))
      } catch (e) {
        console.error('Failed to save chat history:', e)
      }
    }
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])


  // ESC key to close, focus input when opened
  useEffect(() => {
    if (!isOpen) return

    // Scroll to bottom when chat window opens
    scrollToBottom()

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    // Focus input when chat opens
    setTimeout(() => inputRef.current?.focus(), 100)

    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  // Drag & Drop handlers
  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      handleFileSelect(files[0])
    }
  }

  // File selection handler
  const handleFileSelect = (file) => {
    const allowedTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // xlsx
      'application/vnd.ms-excel', // xls
      'application/pdf',
      'image/png',
      'image/jpeg',
      'image/jpg'
    ]

    if (!allowedTypes.includes(file.type)) {
      alert('Chỉ hỗ trợ file Excel, PDF hoặc ảnh (PNG/JPG)')
      return
    }

    setAttachedFile(file)
  }

  // File input change
  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelect(e.target.files[0])
    }
  }

  // Remove attached file
  const removeAttachedFile = () => {
    setAttachedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // Send message (with optional file)
  const handleSend = async () => {
    if ((!input.trim() && !attachedFile) || isLoading) return

    const userMessage = {
      role: 'user',
      content: input || (attachedFile ? `📎 ${attachedFile.name}` : ''),
      hasFile: !!attachedFile,
      fileName: attachedFile?.name,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])
    const currentInput = input
    const currentFile = attachedFile
    setInput('')
    setAttachedFile(null)
    setIsLoading(true)

    try {
      let result

      if (currentFile) {
        // Upload file
        const formData = new FormData()

        // Check if image or document
        if (currentFile.type.startsWith('image/')) {
          formData.append('image', currentFile)
          formData.append('context', JSON.stringify({ additional_text: currentInput }))

          const response = await fetch(`${API_URL}/api/chat/process-image`, {
            method: 'POST',
            body: formData
          })
          if (!response.ok) throw new Error('Image processing failed')
          result = await response.json()
        } else {
          formData.append('file', currentFile)
          formData.append('context', JSON.stringify({ additional_text: currentInput }))

          const response = await fetch(`${API_URL}/api/chat/process-file`, {
            method: 'POST',
            body: formData
          })
          if (!response.ok) throw new Error('File processing failed')
          result = await response.json()
        }
      } else {
        // Text only
        const response = await fetch(`${API_URL}/api/chat/process`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content: currentInput, content_type: 'text' })
        })
        if (!response.ok) throw new Error('AI processing failed')
        result = await response.json()
      }

      const aiMessage = {
        role: 'assistant',
        intent: result.intent,
        confidence: result.confidence,
        entities: result.entities,
        enriched_data: result.enriched_data,
        summary: result.display_summary,
        timestamp: new Date().toISOString(),
        status: 'pending'
      }
      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      setMessages(prev => [...prev, { role: 'error', content: error.message, timestamp: new Date().toISOString() }])
    } finally {
      setIsLoading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleConfirm = async (msgIndex) => {
    const msg = messages[msgIndex]

    // Use editFormData if available (when edit was done), else use original
    const finalEntities = editFormData.customer_id
      ? { ...msg.entities, ...editFormData }
      : msg.entities
    const finalEnriched = editFormData.customer_id
      ? { ...msg.enriched_data, ...editFormData }
      : msg.enriched_data

    setMessages(prev => prev.map((m, i) => i === msgIndex ? { ...m, status: 'confirming' } : m))

    try {
      if (msg.intent === 'CREATE_JOB') {
        const response = await fetch(`${API_URL}/api/jobs/create`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ entities: finalEntities, enriched_data: finalEnriched })
        })
        const result = await response.json()
        if (!result.success) throw new Error(result.message)
        setMessages(prev => prev.map((m, i) => i === msgIndex ? { ...m, status: 'confirmed', job_number: result.job_number } : m))

      } else if (msg.intent === 'ASSIGN_VEHICLE') {
        // Handle vehicle assignment
        const jobId = msg.entities?.job_id || msg.enriched_data?.job_id || (msg.entities?.linked_job_hint ? getJobIdFromHint(msg.entities.linked_job_hint) : null)

        // If we still don't have job_id but we have a job_number hint, try to find it?
        // Ideally backend should have found job_id during initial processing if context was clear.
        // For now, assume job_id is present or we can't assign.

        if (!jobId && msg.entities?.job_number) {
          // Try to use job_number if job_id missing (would need lookup, but let's assume entity has id or we fail)
          // Actually, let's rely on backend enriching job_id in previous step or prompt user?
          // Frontend simple fix: check if we have a job context?
        }

        if (!jobId) {
          throw new Error('Không tìm thấy Job ID. Vui lòng kiểm tra lại job number.')
        }

        const payload = {
          license_plate: finalEntities.license_plate,
          driver_name: finalEntities.driver_name,
          driver_phone: finalEntities.driver_phone,
          driver_id_card: finalEntities.driver_id_card,
          vendor_name: finalEntities.vendor_name,
          vehicle_type: finalEntities.vehicle_type
        }

        const response = await fetch(`${API_URL}/api/jobs/${jobId}/assign-vehicle`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
        const result = await response.json()
        if (!result.success) throw new Error(result.message)

        // Update message with enriched data for template
        setMessages(prev => prev.map((m, i) =>
          i === msgIndex ? {
            ...m,
            status: 'confirmed',
            job_number: result.job_number,
            enriched_data: { ...m.enriched_data, ...result.enriched_data } // Merge response data
          } : m
        ))

      } else {
        setMessages(prev => prev.map((m, i) => i === msgIndex ? { ...m, status: 'confirmed' } : m))
      }

      // Reset edit state
      setEditingMsgIndex(null)
      setEditFormData({})
    } catch (error) {
      // Keep status as 'pending' so user can continue editing after error
      setMessages(prev => prev.map((m, i) => i === msgIndex ? {
        ...m,
        status: 'pending',  // Allow continued editing
        lastError: error.message  // Store error separately
      } : m))
    }
  }

  // Edit handlers
  const handleEdit = (msgIndex) => {
    const msg = messages[msgIndex]
    setEditingMsgIndex(msgIndex)
    setEditFormData({
      customer_id: msg.enriched_data?.customer_id,
      customer_code: msg.enriched_data?.customer_code || msg.entities?.customer_code,
      customer_name: msg.enriched_data?.customer_name,
      booking_date: msg.entities?.booking_date,
      pickup_time: msg.entities?.pickup_time,
      cargo_type: msg.entities?.cargo_type,
      package_quantity: msg.entities?.package_quantity,
      package_unit: msg.entities?.package_unit || 'kiện',
      pickup_address: msg.entities?.pickup_address,
      delivery_address: msg.entities?.delivery_address,
      vehicle_type: msg.entities?.vehicle_type,
      // Vehicle Assignment Fields
      license_plate: msg.entities?.license_plate,
      driver_name: msg.entities?.driver_name,
      driver_phone: msg.entities?.driver_phone,
      driver_id_card: msg.entities?.driver_id_card || msg.entities?.driver_cccd,
      vendor_name: msg.entities?.vendor_name,
      job_number: msg.entities?.job_number || msg.enriched_data?.job_number,
      linked_job_hint: msg.entities?.linked_job_hint,
    })
    setCustomerSearch(msg.enriched_data?.customer_name || msg.entities?.customer_code || '')
  }

  const handleSaveEdit = (msgIndex) => {
    // Update message with edited data
    setMessages(prev => prev.map((m, i) => {
      if (i !== msgIndex) return m
      return {
        ...m,
        entities: { ...m.entities, ...editFormData },
        enriched_data: { ...m.enriched_data, ...editFormData }
      }
    }))
    setEditingMsgIndex(null)
  }

  const handleCancelEdit = () => {
    setEditingMsgIndex(null)
    setEditFormData({})
    setShowCustomerDropdown(false)
  }

  // Handle edit confirmed job (reset to pending status)
  const handleEditConfirmed = (msgIndex) => {
    const msg = messages[msgIndex]
    // Reset status to pending so user can edit and re-confirm
    setMessages(prev => prev.map((m, i) =>
      i === msgIndex ? { ...m, status: 'pending' } : m
    ))
    // Open edit form
    handleEdit(msgIndex)
  }

  // Handle cancel/delete job
  const handleCancelJob = async (msgIndex) => {
    const msg = messages[msgIndex]
    if (!confirm(`Bạn có chắc muốn huỷ job ${msg.job_number || ''}?`)) return

    try {
      // Call API to cancel job if it exists in DB
      if (msg.job_id || msg.job_number) {
        const response = await fetch(`${API_URL}/api/jobs/update`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            entities: {
              job_number: msg.job_number,
              new_status: 'CANCELLED'
            }
          })
        })
        const result = await response.json()
        if (!result.success) {
          console.warn('Failed to cancel job in DB:', result.message)
        }
      }

      // Mark message as cancelled
      setMessages(prev => prev.map((m, i) =>
        i === msgIndex ? { ...m, status: 'cancelled' } : m
      ))
    } catch (error) {
      console.error('Error cancelling job:', error)
      alert('Lỗi huỷ job: ' + error.message)
    }
  }

  const handleSelectCustomer = (customer) => {
    setEditFormData(prev => ({
      ...prev,
      customer_id: customer.id,
      customer_code: customer.code,
      customer_name: customer.name
    }))
    setCustomerSearch(customer.name || customer.code)
    setShowCustomerDropdown(false)
  }

  // Filter customers based on search
  const filteredCustomers = customers.filter(c =>
    (c.name?.toLowerCase() || '').includes(customerSearch.toLowerCase()) ||
    (c.code?.toLowerCase() || '').includes(customerSearch.toLowerCase())
  ).slice(0, 10)

  if (!isOpen) return null

  return (
    <div
      className={`chat-window ${isDragging ? 'dragging' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Drop zone overlay */}
      {isDragging && (
        <div className="chat-drop-overlay">
          <div className="drop-zone-content">
            <span className="drop-icon">📁</span>
            <span>Thả file vào đây</span>
            <span className="drop-hint">Excel, PDF hoặc ảnh</span>
          </div>
        </div>
      )}

      <div className="chat-header">
        <div className="chat-header-info">
          <div className="chat-avatar">🤖</div>
          <div>
            <div className="chat-title">5P AI Assistant</div>
            <div className="chat-subtitle">Paste tin nhắn từ Zalo → AI xử lý</div>
          </div>
        </div>
        <button className="chat-close" onClick={onClose}>✕</button>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-welcome">
            <span className="welcome-icon">💬</span>
            <p>Paste tin nhắn hoặc nhập yêu cầu...</p>
            <div className="welcome-shortcuts">
              <span>📎 Kéo thả file Excel/PDF/Ảnh</span>
              <span>⌨️ Ctrl+K mở/đóng chat</span>
            </div>
          </div>
        )}

        {messages.length > 0 && (
          <div className="chat-history-info">
            <span>💾 {messages.length} tin nhắn đã lưu (tự động xóa sau 15 ngày)</span>
            <button className="clear-history-btn" onClick={() => {
              if (confirm('Xóa toàn bộ lịch sử chat?')) {
                setMessages([])
                localStorage.removeItem(CHAT_STORAGE_KEY)
              }
            }}>🗑️ Xóa</button>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-message ${msg.role}`}>
            {msg.role === 'user' && (
              <>
                <div className="message-bubble user">
                  {msg.hasFile && <span className="file-indicator">📎 {msg.fileName}</span>}
                  {msg.content}
                </div>
                <div className="message-timestamp">
                  {(() => {
                    if (!msg.timestamp) return ''
                    const msgDate = new Date(msg.timestamp)
                    if (isNaN(msgDate.getTime())) return ''
                    const now = new Date()
                    const isToday = msgDate.toDateString() === now.toDateString()
                    const timeStr = msgDate.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
                    return isToday ? timeStr : `${msgDate.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })} ${timeStr}`
                  })()}
                </div>
              </>
            )}
            {msg.role === 'assistant' && (
              <div className="message-bubble assistant">
                <div className="intent-badges">
                  <span className="intent-badge">{msg.intent}</span>
                  <span className="confidence-badge">{(msg.confidence * 100).toFixed(0)}%</span>
                </div>

                {/* Extracted Info Table - VIEW MODE */}
                {msg.enriched_data && Object.keys(msg.enriched_data).length > 0 && editingMsgIndex !== idx && (
                  <div className="extracted-info">
                    <div className="extracted-header">📋 Thông tin trích xuất:</div>
                    <div className="entities-grid">
                      {Object.entries(msg.enriched_data).map(([key, value]) => {
                        if (key.startsWith('available_') || key === 'customer_matched' || key === 'customer_warning' || value === null || value === undefined) return null
                        return (
                          <div key={key} className="entity-item">
                            <span className="entity-key">{key}:</span>
                            <span className="entity-value">{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                {/* EDIT MODE FORM */}
                {editingMsgIndex === idx && (
                  <div className="edit-form">
                    <div className="edit-form-header">✏️ Chỉnh sửa thông tin:</div>

                    {/* Customer Dropdown with Search */}
                    <div className="edit-field customer-field">
                      <label>Khách hàng:</label>
                      <div className="customer-search-container">
                        {editFormData.customer_id && (
                          <div className="selected-customer">
                            ✓ Đã chọn: <strong>{editFormData.customer_code}</strong> - {editFormData.customer_name}
                            <button type="button" className="btn-change-customer" onClick={() => {
                              setEditFormData(prev => ({ ...prev, customer_id: null, customer_code: '', customer_name: '' }))
                              setCustomerSearch('')
                            }}>Đổi</button>
                          </div>
                        )}
                        {!editFormData.customer_id && (
                          <>
                            <input
                              type="text"
                              value={customerSearch}
                              onChange={(e) => {
                                setCustomerSearch(e.target.value)
                                setShowCustomerDropdown(true)
                              }}
                              onFocus={() => setShowCustomerDropdown(true)}
                              placeholder="Tìm khách hàng..."
                              className="customer-search-input"
                            />
                            {showCustomerDropdown && filteredCustomers.length > 0 && (
                              <div className="customer-dropdown">
                                {filteredCustomers.map(c => (
                                  <div
                                    key={c.id}
                                    className="customer-option"
                                    onClick={() => handleSelectCustomer(c)}
                                  >
                                    <span className="customer-code">{c.code}</span>
                                    <span className="customer-name">{c.name}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    </div>

                    {/* Other editable fields */}
                    <div className="edit-fields-grid">
                      <div className="edit-field">
                        <label>Ngày:</label>
                        <input
                          type="date"
                          value={editFormData.booking_date || ''}
                          onChange={e => setEditFormData({ ...editFormData, booking_date: e.target.value })}
                        />
                      </div>
                      <div className="edit-field">
                        <label>Giờ:</label>
                        <input
                          type="time"
                          value={editFormData.pickup_time || ''}
                          onChange={e => setEditFormData({ ...editFormData, pickup_time: e.target.value })}
                        />
                      </div>
                      <div className="edit-field">
                        <label>Loại hàng:</label>
                        <input
                          type="text"
                          value={editFormData.cargo_type || ''}
                          onChange={e => setEditFormData({ ...editFormData, cargo_type: e.target.value })}
                        />
                      </div>
                      <div className="edit-field">
                        <label>Số kiện:</label>
                        <input
                          type="number"
                          value={editFormData.package_quantity || ''}
                          onChange={e => setEditFormData({ ...editFormData, package_quantity: parseInt(e.target.value) || 0 })}
                        />
                      </div>
                      <div className="edit-field">
                        <label>Điểm lấy hàng:</label>
                        <input
                          type="text"
                          value={editFormData.pickup_address || ''}
                          onChange={e => setEditFormData({ ...editFormData, pickup_address: e.target.value })}
                        />
                      </div>
                      <div className="edit-field">
                        <label>Điểm giao:</label>
                        <input
                          type="text"
                          value={editFormData.delivery_address || ''}
                          onChange={e => setEditFormData({ ...editFormData, delivery_address: e.target.value })}
                        />
                      </div>

                      {/* ASSIGN_VEHICLE Specific Fields */}
                      {(messages[idx].intent === 'ASSIGN_VEHICLE' || editFormData.license_plate) && (
                        <>
                          <div className="edit-field">
                            <label>Biển số xe:</label>
                            <input
                              type="text"
                              value={editFormData.license_plate || ''}
                              onChange={e => setEditFormData({ ...editFormData, license_plate: e.target.value })}
                              placeholder="29H-..."
                            />
                          </div>
                          <div className="edit-field">
                            <label>Vendor:</label>
                            <input
                              type="text"
                              value={editFormData.vendor_name || ''}
                              onChange={e => setEditFormData({ ...editFormData, vendor_name: e.target.value })}
                              placeholder="Tên nhà xe"
                            />
                          </div>
                          <div className="edit-field">
                            <label>Tài xế:</label>
                            <input
                              type="text"
                              value={editFormData.driver_name || ''}
                              onChange={e => setEditFormData({ ...editFormData, driver_name: e.target.value })}
                              placeholder="Tên tài xế"
                            />
                          </div>
                          <div className="edit-field">
                            <label>SĐT Tài xế:</label>
                            <input
                              type="text"
                              value={editFormData.driver_phone || ''}
                              onChange={e => setEditFormData({ ...editFormData, driver_phone: e.target.value })}
                              placeholder="09..."
                            />
                          </div>
                          <div className="edit-field">
                            <label>CCCD:</label>
                            <input
                              type="text"
                              value={editFormData.driver_id_card || ''}
                              onChange={e => setEditFormData({ ...editFormData, driver_id_card: e.target.value })}
                            />
                          </div>
                        </>
                      )}
                    </div>

                    <div className="edit-actions">
                      <button className="btn-save-edit" onClick={() => handleSaveEdit(idx)}>💾 Lưu</button>
                      <button className="btn-cancel-edit" onClick={handleCancelEdit}>✕ Hủy</button>
                    </div>
                  </div>
                )}

                {/* Warning if customer not matched */}
                {msg.enriched_data?.customer_warning && editingMsgIndex !== idx && (
                  <div className="warning-message">⚠️ {msg.enriched_data.customer_warning}</div>
                )}

                {/* Show error from failed confirmation attempt */}
                {msg.lastError && (
                  <div className="error-message">❌ {msg.lastError}</div>
                )}

                {/* Action Buttons */}
                {msg.status === 'pending' && (
                  <div className="message-actions">
                    {editingMsgIndex !== idx && (
                      <button className="btn-edit" onClick={() => handleEdit(idx)}>✏️ Chỉnh sửa</button>
                    )}
                    <button className="btn-confirm" onClick={() => handleConfirm(idx)}>✓ Xác nhận</button>
                  </div>
                )}


                {/* Confirmed - Show Job Number and Vendor Message */}
                {msg.status === 'confirmed' && (
                  <div className="confirmed-section">
                    <div className="confirmed-message">✅ Đã xác nhận thành công! ({msg.job_number})</div>

                    {/* Vendor Message to Copy */}
                    <div className="vendor-message-section">
                      <div className="vendor-message-header">🚚 Tin nhắn gửi Vendor:</div>
                      <pre className="vendor-message-content" onClick={e => {
                        navigator.clipboard.writeText(e.target.innerText)
                        alert('Đã copy!')
                      }}>
                        {(() => {
                          // Build cargo info from cargo_items if available
                          const ent = msg.entities || {}
                          const enr = msg.enriched_data || {}
                          const cargoItems = ent.cargo_items || []

                          // Aggregate invoice numbers from cargo_items
                          let invoices = enr.invoice_numbers || ent.invoice_numbers || ent.invoices || []
                          if (!invoices.length && cargoItems.length) {
                            invoices = cargoItems.map(item => item.invoice_no).filter(Boolean)
                          }
                          const invoiceStr = Array.isArray(invoices) ? invoices.join(', ') : invoices

                          // Aggregate cargo info
                          let cargoDesc = ent.cargo_type || enr.cargo_type || ''
                          let totalPackages = ent.package_quantity || ent.total_packages || 0
                          let packageUnit = ent.package_unit || 'kiện'

                          if (cargoItems.length) {
                            // Build from cargo_items
                            const descriptions = [...new Set(cargoItems.map(i => i.description).filter(Boolean))]
                            cargoDesc = descriptions.join(', ') || 'PCB'
                            totalPackages = cargoItems.reduce((sum, item) => sum + (item.package_quantity || 1), 0)
                            packageUnit = cargoItems[0]?.package_unit || 'kiện'
                          }

                          // Dimensions
                          const dims = ent.dimension_length_cm
                            ? `${ent.dimension_length_cm}x${ent.dimension_width_cm}x${ent.dimension_height_cm}cm`
                            : (cargoItems.length ? 'Xem chi tiết' : '')

                          return `🚚 YÊU CẦU XE - ${enr.customer_code || ent.customer_code || ''}

📅 Ngày lấy hàng: ${enr.pickup_date || enr.scheduled_date || ent.pickup_date || ent.scheduled_date || ''}
⏰ Giờ: ${enr.pickup_time || ent.pickup_time || ''}
📋 Invoice: ${invoiceStr}
📦 Hàng: ${cargoDesc} - ${totalPackages} ${packageUnit}
📐 Kích thước: ${dims}
🚛 Loại xe: ${ent.vehicle_type || enr.vehicle_type || ''}
📍 Lấy tại: ${enr.pickup_address || ent.pickup_address || ''}
📍 Giao tại: ${enr.delivery_address || ent.delivery_address || ''}`
                        })()}
                      </pre>
                      <div className="copy-hint">👆 Click để copy</div>
                    </div>

                    {/* Reply button for CREATE_JOB to assign vehicle */}
                    {msg.intent === 'CREATE_JOB' && (
                      <div className="reply-section">
                        <button
                          className="btn-reply"
                          onClick={() => {
                            // Pre-populate input with job context for vehicle assignment
                            const replyText = `xe [BKS] / tài xế [Tên] / vendor [Tên vendor] cho job ${msg.job_number}`
                            setInput(replyText)
                            inputRef.current?.focus()
                            // Select the placeholder text for easy replacement
                            setTimeout(() => {
                              const inp = inputRef.current
                              if (inp) {
                                inp.setSelectionRange(3, 8) // Select [BKS]
                              }
                            }, 50)
                          }}
                        >
                          🚗 Gán xe vào job này
                        </button>
                      </div>
                    )}

                    {/* Edit/Cancel buttons for confirmed jobs */}
                    <div className="confirmed-actions">
                      <button className="btn-edit-confirmed" onClick={() => handleEditConfirmed(idx)}>
                        ✏️ Sửa
                      </button>
                      <button className="btn-cancel-job" onClick={() => handleCancelJob(idx)}>
                        ❌ Huỷ Job
                      </button>
                    </div>
                  </div>
                )}

                {/* Cancelled Status */}
                {msg.status === 'cancelled' && (
                  <div className="cancelled-section">
                    <div className="cancelled-message">🚫 Job đã bị huỷ ({msg.job_number})</div>
                  </div>
                )}

                {msg.status === 'confirming' && <div className="loading-message">⏳ Đang xử lý...</div>}
                {msg.status === 'error' && <div className="error-message">❌ {msg.error}</div>}

                {/* Timestamp */}
                <div className="message-timestamp">
                  {(() => {
                    if (!msg.timestamp) return ''
                    const msgDate = new Date(msg.timestamp)
                    if (isNaN(msgDate.getTime())) return ''
                    const now = new Date()
                    const isToday = msgDate.toDateString() === now.toDateString()
                    const timeStr = msgDate.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
                    return isToday ? timeStr : `${msgDate.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })} ${timeStr}`
                  })()}
                </div>
              </div>
            )}
            {msg.role === 'error' && <div className="message-bubble error">❌ {msg.content}</div>}
          </div>
        ))}
        {isLoading && <div className="chat-loading">AI đang xử lý...</div>}
        <div ref={messagesEndRef} />
      </div>

      {/* Attached file preview */}
      {attachedFile && (
        <div className="attached-file-preview">
          <span className="file-icon">
            {attachedFile.type.startsWith('image/') ? '🖼️' :
              attachedFile.type.includes('pdf') ? '📄' : '📊'}
          </span>
          <span className="file-name">{attachedFile.name}</span>
          <span className="file-size">({(attachedFile.size / 1024).toFixed(1)} KB)</span>
          <button className="remove-file" onClick={removeAttachedFile}>✕</button>
        </div>
      )}

      <div className="chat-input-area">
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls,.pdf,.png,.jpg,.jpeg"
          style={{ display: 'none' }}
          onChange={handleFileInputChange}
        />

        {/* Attachment button */}
        <button
          className="attach-btn"
          onClick={() => fileInputRef.current?.click()}
          title="Đính kèm file (Excel, PDF, Ảnh)"
        >
          📎
        </button>

        <textarea
          ref={inputRef}
          value={input}
          onChange={e => {
            setInput(e.target.value)
            e.target.style.height = 'auto'
            e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
          }}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
          onPaste={e => {
            // Handle paste images
            const items = e.clipboardData?.items
            if (items) {
              for (let i = 0; i < items.length; i++) {
                if (items[i].type.indexOf('image') !== -1) {
                  e.preventDefault()
                  const file = items[i].getAsFile()
                  if (file) handleFileSelect(file)
                  break
                }
              }
            }
          }}
          placeholder="Paste tin nhắn, kéo thả file, hoặc Ctrl+V ảnh..."
          className="chat-input"
          rows="1"
        />
        <button onClick={handleSend} disabled={isLoading} className="chat-send-btn">🚀</button>
      </div>
    </div>
  )
}

// ========================================
// MAIN DASHBOARD COMPONENT
// ========================================
function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [chatOpen, setChatOpen] = useState(false)
  const [activeNav, setActiveNav] = useState('dashboard')
  const [stats, setStats] = useState({ jobs_today: 0, trucking: 0, warehouse: 0, revenue: '0', status_counts: {} })
  const [recentJobs, setRecentJobs] = useState([])
  const [serviceData, setServiceData] = useState([])
  const [loading, setLoading] = useState(true)

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
      // Number keys 1-5: Quick navigation
      if (!e.ctrlKey && !e.metaKey && !e.altKey && !e.shiftKey) {
        const navMap = { '1': 'dashboard', '2': 'jobs', '3': 'trucking', '4': 'warehouse', '5': 'customs' }
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
        const statsRes = await fetch(`${API_URL}/api/dashboard/stats`)
        if (statsRes.ok) {
          const statsData = await statsRes.json()
          setStats(statsData)
        }

        const jobsRes = await fetch(`${API_URL}/api/jobs/recent?limit=10`)
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

  // Fetch service-specific data
  useEffect(() => {
    const fetchServiceData = async () => {
      if (['trucking', 'warehouse', 'customs', 'packing'].includes(activeNav)) {
        try {
          const res = await fetch(`${API_URL}/api/services/${activeNav}`)
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
      trucking: '🚚', TRUCKING_SHORT: '🚚', TRUCKING_LONG: '🚛',
      warehouse: '🏭', WHS_STORAGE: '🏭', WHS_HANDLE: '📦',
      customs: '📋', CUS_IMPORT: '📥', CUS_EXPORT: '📤',
      packing: '📦', SVC_PACK: '📦', SVC_VACUUM: '💨',
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
    fetch(`${API_URL}/api/jobs/recent?limit=10`)
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
          {sidebarOpen && (
            <div className="logo-text">
              <div className="logo-title">5P VIETNAM</div>
              <div className="logo-subtitle">SLMS</div>
            </div>
          )}
        </div>

        <nav className="sidebar-nav">
          <NavItem icon="📊" label="Dashboard" active={activeNav === 'dashboard'} onClick={() => setActiveNav('dashboard')} />
          <NavItem icon="📋" label="Jobs" active={activeNav === 'jobs'} onClick={() => setActiveNav('jobs')} badge={stats.jobs_today || null} />

          <div className="nav-divider" />
          <div className="nav-section-title">SERVICES</div>

          <NavItem icon="🚚" label="Trucking" active={activeNav === 'trucking'} onClick={() => setActiveNav('trucking')} />
          <NavItem icon="🏭" label="Warehouse" active={activeNav === 'warehouse'} onClick={() => setActiveNav('warehouse')} />
          <NavItem icon="📋" label="Customs" active={activeNav === 'customs'} onClick={() => setActiveNav('customs')} />
          <NavItem icon="📦" label="Packing" active={activeNav === 'packing'} onClick={() => setActiveNav('packing')} />

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
            <div className="search-box">
              <span className="search-icon">🔍</span>
              <input type="text" placeholder="Search jobs, customers..." className="search-input" />
            </div>
            <div className="user-avatar">KH</div>
          </div>
        </header>

        {/* Dashboard Content */}
        {activeNav === 'dashboard' && (
          <div className="dashboard-content">
            <div className="stats-grid">
              <StatsCard icon="📋" label="Jobs Today" value={stats.jobs_today || 0} color={theme.primary} />
              <StatsCard icon="🚚" label="Active Trucking" value={stats.trucking || 0} color={theme.accent} />
              <StatsCard icon="🏭" label="In Storage" value={stats.warehouse || 0} color="#8B5CF6" />
              <StatsCard icon="📈" label="Revenue MTD" value={stats.revenue || '0'} color={theme.success} />
            </div>

            <div className="dashboard-grid">
              {/* Jobs by Status - REAL DATA */}
              <div className="card jobs-status-card">
                <h3 className="card-title">Jobs by Status</h3>
                <div className="status-bars">
                  {Object.entries(stats.status_counts || {}).map(([status, count], i) => (
                    <div key={i} className="status-bar-row">
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
                        <td><StatusBadge status={job.status_code || 'PENDING'} /></td>
                      </tr>
                    )) : (
                      <tr><td colSpan="5" className="no-data">No recent jobs</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Service Views */}
        {['trucking', 'warehouse', 'customs', 'packing'].includes(activeNav) && (
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
                    <tr key={i}>
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
                        <button className="action-btn" onClick={() => handleViewJob(svc)}>View</button>
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
                <h3 className="card-title">📋 All Jobs</h3>
                <button className="add-job-btn" onClick={() => setShowJobCreate(true)}>+ New Job</button>
              </div>
              <table className="services-table">
                <thead>
                  <tr>
                    <th>Job No</th>
                    <th>Customer</th>
                    <th>Service Type</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {recentJobs.length > 0 ? recentJobs.map((job, i) => (
                    <tr key={i}>
                      <td className="job-number">{job.job_no}</td>
                      <td>{job.customer_code || job.customer_name}</td>
                      <td>{getServiceIcon(job.service_type)} {job.service_type}</td>
                      <td>{job.etd || job.created_at?.split('T')[0]}</td>
                      <td><StatusBadge status={job.status_code || 'PENDING'} /></td>
                      <td>
                        <button className="action-btn" onClick={() => handleViewJob(job)}>View</button>
                      </td>
                    </tr>
                  )) : (
                    <tr><td colSpan="6" className="no-data">No jobs found</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* Floating AI Button */}
      <FloatingAIButton onClick={() => setChatOpen(!chatOpen)} hasNotification={!chatOpen} />

      {/* Chat Window */}
      <ChatWindow isOpen={chatOpen} onClose={() => setChatOpen(false)} />

      {/* Job Detail Modal */}
      {showJobDetail && <JobDetailModal job={selectedJob} onClose={() => setShowJobDetail(false)} />}

      {/* Job Create Form */}
      {showJobCreate && <JobCreateForm onClose={() => setShowJobCreate(false)} onSuccess={handleJobCreated} />}
    </div>
  )
}

export default App
