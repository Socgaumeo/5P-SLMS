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
// JOB DETAIL MODAL
// ========================================
function JobDetailModal({ job, onClose }) {
  const [services, setServices] = useState([])
  const [loading, setLoading] = useState(true)

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

  if (!job) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2 className="modal-title">📋 {job.job_no}</h2>
            <p className="modal-subtitle">{job.customer_name || job.customer_code}</p>
          </div>
          <StatusBadge status={job.status_code || 'PENDING'} />
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {/* Job Info */}
          <div className="detail-section">
            <h3>Thông tin Job</h3>
            <div className="detail-grid">
              <div className="detail-item">
                <span className="detail-label">Khách hàng:</span>
                <span className="detail-value">{job.customer_name || job.customer_code}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Ngày tạo:</span>
                <span className="detail-value">{job.created_at?.split('T')[0]}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">ETD:</span>
                <span className="detail-value">{job.etd || '-'}</span>
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
                    {/* Assignment info */}
                    <div className="service-assignment">
                      <strong>Người xử lý:</strong>
                      <span className={`assigned-badge ${svc.vendor_id ? 'vendor' : svc.employee_id ? 'employee' : 'unassigned'}`}>
                        {svc.vendor_id ? '🏢 ' : svc.employee_id ? '👤 ' : ''}
                        {svc.vendor_name || svc.employee_name || 'Chưa gán'}
                      </span>
                    </div>
                    <div className="service-details-grid">
                      {svc.cargo_type && <div><strong>Hàng:</strong> {svc.cargo_type}</div>}
                      {svc.weight_kg && <div><strong>Khối lượng:</strong> {svc.weight_kg}kg</div>}
                      {svc.package_quantity && <div><strong>Số kiện:</strong> {svc.package_quantity} {svc.package_unit || 'pcs'}</div>}
                      {svc.origin_address && <div><strong>Điểm đi:</strong> {svc.origin_address}</div>}
                      {svc.dest_address && <div><strong>Điểm đến:</strong> {svc.dest_address}</div>}
                      {svc.scheduled_date && <div><strong>Ngày:</strong> {svc.scheduled_date}</div>}
                      {svc.scheduled_time && <div><strong>Giờ:</strong> {svc.scheduled_time}</div>}
                      {svc.vehicle_id && <div><strong>Xe:</strong> ID {svc.vehicle_id}</div>}
                      {svc.driver_id && <div><strong>Tài xế:</strong> ID {svc.driver_id}</div>}
                      {/* Packing specific */}
                      {svc.before_length_cm && (
                        <div><strong>Kích thước trước:</strong> {svc.before_length_cm}x{svc.before_width_cm}x{svc.before_height_cm}cm</div>
                      )}
                      {svc.after_length_cm && (
                        <div><strong>Kích thước sau:</strong> {svc.after_length_cm}x{svc.after_width_cm}x{svc.after_height_cm}cm</div>
                      )}
                      {svc.vacuum_pack && <div>✅ Hút chân không</div>}
                      {svc.shrink_wrap && <div>✅ Màng co</div>}
                      {svc.lashing && <div>✅ Chằng buộc</div>}
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
// CHAT WINDOW (simplified)
// ========================================
function ChatWindow({ isOpen, onClose }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = { role: 'user', content: input, timestamp: new Date().toLocaleTimeString('vi-VN') }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch(`${API_URL}/api/chat/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: input, content_type: 'text' })
      })

      if (!response.ok) throw new Error('AI processing failed')
      const result = await response.json()

      const aiMessage = {
        role: 'assistant',
        intent: result.intent,
        confidence: result.confidence,
        entities: result.entities,
        enriched_data: result.enriched_data,
        summary: result.display_summary,
        timestamp: new Date().toLocaleTimeString('vi-VN'),
        status: 'pending'
      }
      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      setMessages(prev => [...prev, { role: 'error', content: error.message, timestamp: new Date().toLocaleTimeString('vi-VN') }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleConfirm = async (msgIndex) => {
    const msg = messages[msgIndex]
    setMessages(prev => prev.map((m, i) => i === msgIndex ? { ...m, status: 'confirming' } : m))

    try {
      if (msg.intent === 'CREATE_JOB') {
        const response = await fetch(`${API_URL}/api/jobs/create`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ entities: msg.entities, enriched_data: msg.enriched_data })
        })
        const result = await response.json()
        if (!result.success) throw new Error(result.message)
        setMessages(prev => prev.map((m, i) => i === msgIndex ? { ...m, status: 'confirmed', job_number: result.job_number } : m))
      } else {
        setMessages(prev => prev.map((m, i) => i === msgIndex ? { ...m, status: 'confirmed' } : m))
      }
    } catch (error) {
      setMessages(prev => prev.map((m, i) => i === msgIndex ? { ...m, status: 'error', error: error.message } : m))
    }
  }

  if (!isOpen) return null

  return (
    <div className="chat-window">
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
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-message ${msg.role}`}>
            {msg.role === 'user' && <div className="message-bubble user">{msg.content}</div>}
            {msg.role === 'assistant' && (
              <div className="message-bubble assistant">
                <div className="intent-badges">
                  <span className="intent-badge">{msg.intent}</span>
                  <span className="confidence-badge">{msg.confidence}%</span>
                </div>
                {msg.summary && <div className="message-summary">{msg.summary}</div>}
                {msg.status === 'pending' && (
                  <div className="message-actions">
                    <button className="btn-confirm" onClick={() => handleConfirm(idx)}>✓ Xác nhận</button>
                  </div>
                )}
                {msg.status === 'confirmed' && <div className="confirmed-message">✅ Đã xác nhận! {msg.job_number}</div>}
                {msg.status === 'error' && <div className="error-message">❌ {msg.error}</div>}
              </div>
            )}
            {msg.role === 'error' && <div className="message-bubble error">❌ {msg.content}</div>}
          </div>
        ))}
        {isLoading && <div className="chat-loading">AI đang xử lý...</div>}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <input
          type="text" value={input} onChange={e => setInput(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && handleSend()}
          placeholder="Paste tin nhắn hoặc nhập yêu cầu..." className="chat-input"
        />
        <button onClick={handleSend} disabled={isLoading} className="chat-send-btn">🚀 Gửi</button>
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
    setSelectedJob(job)
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
            <button className="notification-btn">🔔<span className="notification-dot" /></button>
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
                <button className="add-job-btn" onClick={() => setShowJobCreate(true)}>+ New Job</button>
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
