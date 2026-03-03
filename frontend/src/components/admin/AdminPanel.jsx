// frontend/src/components/admin/AdminPanel.jsx
/**
 * Admin Panel for managing master data:
 * - Service Types
 * - Vendors
 * - Customers
 * - Buying/Selling Rates
 */

import { useState, useEffect } from 'react'
import './AdminPanel.css'
import RateFormModal from './RateFormModal'
import RateUploadModal from './RateUploadModal'
import { authFetch, API_URL } from '../../utils/auth-fetch'

// Helper to format currency
const formatCurrency = (value) => {
  if (!value && value !== 0) return '-'
  return new Intl.NumberFormat('vi-VN').format(value)
}

// Tab definitions
const TABS = [
  { id: 'users', label: 'Users', icon: '👤', adminOnly: true },
  { id: 'audit-logs', label: 'Audit Logs', icon: '📜', adminOnly: true },
  { id: 'service-types', label: 'Service Types', icon: '📋' },
  { id: 'cost-items', label: 'Định mức', icon: '📋' },
  { id: 'vendors', label: 'Vendors', icon: '🏢' },
  { id: 'customers', label: 'Customers', icon: '👥' },
  { id: 'selling-rates', label: 'Doanh Thu', icon: '💰' },
  { id: 'buying-rates', label: 'Chi phí NCC', icon: '💸' },
]

// Generic DataTable component
function DataTable({ columns, data, onEdit, onDelete, loading }) {
  if (loading) {
    return <div className="loading-state">Loading...</div>
  }

  if (!data || data.length === 0) {
    return <div className="empty-state">No data found</div>
  }

  return (
    <table className="admin-table">
      <thead>
        <tr>
          {columns.map((col) => (
            <th key={col.key}>{col.label}</th>
          ))}
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {data.map((row, idx) => (
          <tr key={row.id || row.service_code || idx}>
            {columns.map((col) => (
              <td key={col.key}>
                {col.render ? col.render(row[col.key], row) : row[col.key]}
              </td>
            ))}
            <td className="action-cell">
              <button className="btn-edit" onClick={() => onEdit(row)}>Edit</button>
              <button className="btn-delete" onClick={() => onDelete(row)}>Delete</button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

// Users Management Tab
function UsersTab() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [formData, setFormData] = useState({
    user_code: '',
    full_name: '',
    email: '',
    password: '',
    role: 'STAFF',
  })
  const [resetPasswordResult, setResetPasswordResult] = useState(null)

  // Fetch users
  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('token')
      const res = await authFetch(`${API_URL}/api/users?include_inactive=true`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await res.json()
      if (data.success) {
        setUsers(data.users || [])
      }
    } catch (error) {
      console.error('Error fetching users:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (user) => {
    if (!confirm(`Vô hiệu hóa user "${user.user_code}"?`)) return
    try {
      const token = localStorage.getItem('token')
      await authFetch(`${API_URL}/api/users/${user.user_id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      })
      fetchUsers()
    } catch (error) {
      console.error('Error deleting user:', error)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const token = localStorage.getItem('token')
      const url = editItem
        ? `${API_URL}/api/users/${editItem.user_id}`
        : `${API_URL}/api/users`
      const method = editItem ? 'PUT' : 'POST'

      const res = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      })

      const data = await res.json()
      if (data.success) {
        if (data.generated_password) {
          alert(`User created! Generated password: ${data.generated_password}\n\nPlease save this password - it won't be shown again.`)
        }
        setShowForm(false)
        setEditItem(null)
        setFormData({ user_code: '', full_name: '', email: '', password: '', role: 'STAFF' })
        fetchUsers()
      } else {
        alert(data.message || 'Error saving user')
      }
    } catch (error) {
      console.error('Error saving user:', error)
    }
  }

  const handleResetPassword = async (user) => {
    if (!confirm(`Reset mật khẩu cho "${user.full_name}"?`)) return
    try {
      const token = localStorage.getItem('token')
      const res = await authFetch(`${API_URL}/api/users/${user.user_id}/reset-password`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await res.json()
      if (data.success) {
        setResetPasswordResult({
          user: user.full_name,
          password: data.new_password
        })
      } else {
        alert(data.message || 'Error resetting password')
      }
    } catch (error) {
      console.error('Error resetting password:', error)
    }
  }

  const handleActivate = async (user) => {
    try {
      const token = localStorage.getItem('token')
      await authFetch(`${API_URL}/api/users/${user.user_id}/activate`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      })
      fetchUsers()
    } catch (error) {
      console.error('Error activating user:', error)
    }
  }

  const columns = [
    { key: 'user_code', label: 'Code' },
    { key: 'full_name', label: 'Name' },
    { key: 'email', label: 'Email' },
    { key: 'role', label: 'Role', render: (val) => (
      <span className={`role-badge role-${val?.toLowerCase()}`}>{val}</span>
    )},
    { key: 'is_active', label: 'Status', render: (val) => (
      <span className={`status-pill ${val ? 'active' : 'inactive'}`}>
        {val ? 'Active' : 'Inactive'}
      </span>
    )},
    { key: 'last_login', label: 'Last Login', render: (val) => (
      val ? new Date(val).toLocaleDateString('vi-VN') : '-'
    )},
  ]

  return (
    <div className="tab-content">
      <div className="tab-header">
        <h3>User Management</h3>
        <button className="btn-add" onClick={() => {
          setEditItem(null)
          setFormData({ user_code: '', full_name: '', email: '', password: '', role: 'STAFF' })
          setShowForm(true)
        }}>
          + Add User
        </button>
      </div>

      {loading ? (
        <div className="loading-state">Loading...</div>
      ) : (
        <table className="admin-table">
          <thead>
            <tr>
              {columns.map((col) => <th key={col.key}>{col.label}</th>)}
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.user_id}>
                {columns.map((col) => (
                  <td key={col.key}>
                    {col.render ? col.render(user[col.key], user) : user[col.key]}
                  </td>
                ))}
                <td className="action-cell">
                  <button className="btn-edit" onClick={() => {
                    setEditItem(user)
                    setFormData({
                      user_code: user.user_code,
                      full_name: user.full_name,
                      email: user.email || '',
                      password: '',
                      role: user.role,
                    })
                    setShowForm(true)
                  }}>Edit</button>
                  <button className="btn-reset" onClick={() => handleResetPassword(user)}>
                    Reset PW
                  </button>
                  {user.is_active ? (
                    <button className="btn-delete" onClick={() => handleDelete(user)}>
                      Disable
                    </button>
                  ) : (
                    <button className="btn-activate" onClick={() => handleActivate(user)}>
                      Activate
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* User Form Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>{editItem ? 'Edit User' : 'Add New User'}</h3>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>User Code</label>
                <input
                  value={formData.user_code}
                  onChange={(e) => setFormData({ ...formData, user_code: e.target.value.toUpperCase() })}
                  required
                  disabled={!!editItem}
                  placeholder="e.g., ADMIN, STAFF01"
                />
              </div>
              <div className="form-group">
                <label>Full Name</label>
                <input
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  required
                  placeholder="Nguyễn Văn A"
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                  placeholder="user@5pvietnam.com"
                />
              </div>
              {!editItem && (
                <div className="form-group">
                  <label>Password (leave empty to generate)</label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    placeholder="Leave empty to auto-generate"
                  />
                </div>
              )}
              <div className="form-group">
                <label>Role</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                >
                  <option value="STAFF">Staff</option>
                  <option value="MANAGER">Manager</option>
                  <option value="ADMIN">Admin</option>
                </select>
              </div>
              <div className="form-actions">
                <button type="button" onClick={() => setShowForm(false)}>Cancel</button>
                <button type="submit" className="btn-primary">
                  {editItem ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Password Reset Result Modal */}
      {resetPasswordResult && (
        <div className="modal-overlay" onClick={() => setResetPasswordResult(null)}>
          <div className="modal-content password-result" onClick={(e) => e.stopPropagation()}>
            <h3>Password Reset Successful</h3>
            <p>New password for <strong>{resetPasswordResult.user}</strong>:</p>
            <div className="password-display">
              <code>{resetPasswordResult.password}</code>
              <button onClick={() => {
                navigator.clipboard.writeText(resetPasswordResult.password)
                alert('Password copied to clipboard!')
              }}>Copy</button>
            </div>
            <p className="warning-text">
              Please save this password. It will not be shown again.
            </p>
            <button className="btn-primary" onClick={() => setResetPasswordResult(null)}>
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// Audit Logs Tab
function AuditLogsTab() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    user_id: '',
    action_type: '',
    entity_type: '',
    from_date: '',
    to_date: '',
    search: '',
  })
  const [users, setUsers] = useState([])

  useEffect(() => {
    fetchLogs()
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('token')
      const res = await authFetch(`${API_URL}/api/audit/users`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await res.json()
      if (data.success) {
        setUsers(data.users || [])
      }
    } catch (error) {
      console.error('Error fetching users:', error)
    }
  }

  const fetchLogs = async (filterParams = filters) => {
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const params = new URLSearchParams()
      if (filterParams.user_id) params.append('user_id', filterParams.user_id)
      if (filterParams.action_type) params.append('action_type', filterParams.action_type)
      if (filterParams.entity_type) params.append('entity_type', filterParams.entity_type)
      if (filterParams.from_date) params.append('from_date', filterParams.from_date)
      if (filterParams.to_date) params.append('to_date', filterParams.to_date)
      if (filterParams.search) params.append('search', filterParams.search)
      params.append('limit', '100')

      const res = await authFetch(`${API_URL}/api/audit/logs?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      const data = await res.json()
      if (data.success) {
        setLogs(data.logs || [])
      }
    } catch (error) {
      console.error('Error fetching logs:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value }
    setFilters(newFilters)
  }

  const applyFilters = () => {
    fetchLogs(filters)
  }

  const clearFilters = () => {
    const cleared = {
      user_id: '', action_type: '', entity_type: '',
      from_date: '', to_date: '', search: ''
    }
    setFilters(cleared)
    fetchLogs(cleared)
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    const d = new Date(dateStr)
    return d.toLocaleString('vi-VN', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    })
  }

  const getActionBadgeClass = (action) => {
    switch (action) {
      case 'LOGIN': return 'action-login'
      case 'LOGOUT': return 'action-logout'
      case 'CREATE': return 'action-create'
      case 'UPDATE': return 'action-update'
      case 'DELETE': return 'action-delete'
      default: return ''
    }
  }

  const getActionLabel = (action) => {
    const labels = {
      LOGIN: 'Đăng nhập',
      LOGOUT: 'Đăng xuất',
      CREATE: 'Tạo mới',
      UPDATE: 'Cập nhật',
      DELETE: 'Xóa'
    }
    return labels[action] || action
  }

  const getEntityLabel = (entity) => {
    const labels = {
      JOB: 'Job',
      USER: 'Người dùng',
      CUSTOMER: 'Khách hàng',
      VENDOR: 'Nhà cung cấp',
      SERVICE: 'Dịch vụ'
    }
    return labels[entity] || entity
  }

  return (
    <div className="tab-content">
      <div className="tab-header">
        <h3>Audit Logs - Lịch sử hoạt động</h3>
        <button className="btn-primary" onClick={applyFilters}>
          Tìm kiếm
        </button>
      </div>

      {/* Filters */}
      <div className="audit-filters">
        <div className="filter-row">
          <div className="filter-group">
            <label>Người dùng</label>
            <select
              value={filters.user_id}
              onChange={(e) => handleFilterChange('user_id', e.target.value)}
            >
              <option value="">Tất cả</option>
              {users.map(u => (
                <option key={u.user_id} value={u.user_id}>
                  {u.user_code} - {u.full_name}
                </option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <label>Hành động</label>
            <select
              value={filters.action_type}
              onChange={(e) => handleFilterChange('action_type', e.target.value)}
            >
              <option value="">Tất cả</option>
              <option value="LOGIN">Đăng nhập</option>
              <option value="LOGOUT">Đăng xuất</option>
              <option value="CREATE">Tạo mới</option>
              <option value="UPDATE">Cập nhật</option>
              <option value="DELETE">Xóa</option>
            </select>
          </div>
          <div className="filter-group">
            <label>Đối tượng</label>
            <select
              value={filters.entity_type}
              onChange={(e) => handleFilterChange('entity_type', e.target.value)}
            >
              <option value="">Tất cả</option>
              <option value="JOB">Job</option>
              <option value="USER">Người dùng</option>
              <option value="CUSTOMER">Khách hàng</option>
              <option value="VENDOR">Nhà cung cấp</option>
              <option value="SERVICE">Dịch vụ</option>
            </select>
          </div>
        </div>
        <div className="filter-row">
          <div className="filter-group">
            <label>Từ ngày</label>
            <input
              type="date"
              value={filters.from_date}
              onChange={(e) => handleFilterChange('from_date', e.target.value)}
            />
          </div>
          <div className="filter-group">
            <label>Đến ngày</label>
            <input
              type="date"
              value={filters.to_date}
              onChange={(e) => handleFilterChange('to_date', e.target.value)}
            />
          </div>
          <div className="filter-group search-group">
            <label>Tìm kiếm</label>
            <input
              type="text"
              placeholder="Job no, mã..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && applyFilters()}
            />
          </div>
          <button className="btn-secondary btn-clear" onClick={clearFilters}>
            Xóa bộ lọc
          </button>
        </div>
      </div>

      {/* Logs Table */}
      {loading ? (
        <div className="loading-state">Loading...</div>
      ) : logs.length === 0 ? (
        <div className="empty-state">Không có dữ liệu</div>
      ) : (
        <table className="admin-table audit-table">
          <thead>
            <tr>
              <th>Thời gian</th>
              <th>Người dùng</th>
              <th>Hành động</th>
              <th>Đối tượng</th>
              <th>Mã</th>
              <th>Mô tả</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.log_id}>
                <td className="time-cell">{formatDate(log.created_at)}</td>
                <td>
                  <span className="user-code">{log.user_code || '-'}</span>
                  {log.user_name && <span className="user-name">{log.user_name}</span>}
                </td>
                <td>
                  <span className={`action-badge ${getActionBadgeClass(log.action_type)}`}>
                    {getActionLabel(log.action_type)}
                  </span>
                </td>
                <td>{log.entity_type ? getEntityLabel(log.entity_type) : '-'}</td>
                <td className="entity-ref">{log.entity_ref || '-'}</td>
                <td className="desc-cell">{log.description || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

// Service Types Management
function ServiceTypesTab() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [formData, setFormData] = useState({
    service_code: '',
    name_vi: '',
    name_en: '',
    category: '',
    keywords: '',
    is_active: true,
  })

  const columns = [
    { key: 'service_code', label: 'Code' },
    { key: 'name_vi', label: 'Name (VI)' },
    { key: 'name_en', label: 'Name (EN)' },
    { key: 'category', label: 'Category' },
    { key: 'keywords', label: 'Keywords' },
    {
      key: 'is_active',
      label: 'Status',
      render: (val) => (
        <span className={`status-pill ${val ? 'active' : 'inactive'}`}>
          {val ? 'Active' : 'Inactive'}
        </span>
      ),
    },
  ]

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await authFetch(`${API_URL}/api/admin/service-types?include_inactive=true`)
      const json = await res.json()
      setData(json.data || [])
    } catch (err) {
      console.error('Failed to fetch service types:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleEdit = (item) => {
    setEditItem(item)
    setFormData({
      service_code: item.service_code,
      name_vi: item.name_vi || '',
      name_en: item.name_en || '',
      category: item.category || '',
      keywords: item.keywords || '',
      is_active: item.is_active,
    })
    setShowForm(true)
  }

  const handleDelete = async (item) => {
    if (!confirm(`Delete service type "${item.service_code}"?`)) return
    try {
      await authFetch(`${API_URL}/api/admin/service-types/${item.service_code}`, {
        method: 'DELETE',
      })
      fetchData()
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const url = editItem
        ? `${API_URL}/api/admin/service-types/${editItem.service_code}`
        : `${API_URL}/api/admin/service-types`
      const method = editItem ? 'PUT' : 'POST'

      await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })

      setShowForm(false)
      setEditItem(null)
      setFormData({
        service_code: '',
        name_vi: '',
        name_en: '',
        category: '',
        keywords: '',
        is_active: true,
      })
      fetchData()
    } catch (err) {
      console.error('Save failed:', err)
    }
  }

  return (
    <div className="admin-tab-content">
      <div className="tab-header">
        <h3>Service Types</h3>
        <button className="btn-primary" onClick={() => setShowForm(true)}>
          + Add Service Type
        </button>
      </div>

      <DataTable
        columns={columns}
        data={data}
        loading={loading}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>{editItem ? 'Edit Service Type' : 'Add Service Type'}</h3>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Code *</label>
                <input
                  type="text"
                  value={formData.service_code}
                  onChange={(e) =>
                    setFormData({ ...formData, service_code: e.target.value.toUpperCase() })
                  }
                  disabled={!!editItem}
                  required
                />
              </div>
              <div className="form-group">
                <label>Name (VI) *</label>
                <input
                  type="text"
                  value={formData.name_vi}
                  onChange={(e) => setFormData({ ...formData, name_vi: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Name (EN)</label>
                <input
                  type="text"
                  value={formData.name_en}
                  onChange={(e) => setFormData({ ...formData, name_en: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Category</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                >
                  <option value="">-- Select --</option>
                  <option value="TRUCKING">Trucking</option>
                  <option value="WAREHOUSE">Warehouse</option>
                  <option value="CUSTOMS">Customs</option>
                  <option value="PACKING">Packing</option>
                  <option value="CONTAINER">Container Handling</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>
              <div className="form-group">
                <label>Keywords (comma-separated, for AI detection)</label>
                <textarea
                  value={formData.keywords}
                  onChange={(e) => setFormData({ ...formData, keywords: e.target.value })}
                  placeholder="e.g., van chuyen, giao hang, truck"
                />
              </div>
              <div className="form-group checkbox">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                  Active
                </label>
              </div>
              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Save
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

// Cost Items Management
function CostItemsTab() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [filterRegion, setFilterRegion] = useState('')
  const [filterCategory, setFilterCategory] = useState('')
  const [formData, setFormData] = useState({
    cost_code: '',
    name_vi: '',
    name_en: '',
    category: '',
    region: '',
    service_type: '',
    customer_code: '',
    default_price: 0,
    selling_price: 0,
    unit: 'UNIT',
    currency: 'VND',
    notes: '',
    is_active: true,
  })

  const REGIONS = ['Miền Nam', 'Miền Bắc', 'Hà Nội', 'Hải Phòng', 'HCM', 'Đà Nẵng']
  const CATEGORIES = ['Hải quan', 'Vận tải', 'Kho bãi', 'Cước vận chuyển', 'Phụ phí', 'Khác']
  const UNITS = ['TRIP', 'CONT', 'KG', 'CBM', 'PALLET', 'SHIPMENT', 'SET', 'UNIT', 'TỜ KHAI', 'BỘ']

  const columns = [
    { key: 'cost_code', label: 'Mã' },
    { key: 'name_vi', label: 'Tên chi phí' },
    { key: 'region', label: 'Khu vực' },
    { key: 'category', label: 'Danh mục' },
    { key: 'default_price', label: 'Giá mặc định', render: (v) => formatCurrency(v) },
    { key: 'selling_price', label: 'Giá bán', render: (v) => formatCurrency(v) },
    { key: 'unit', label: 'Đơn vị' },
    {
      key: 'is_active',
      label: 'Trạng thái',
      render: (val) => (
        <span className={`status-pill ${val ? 'active' : 'inactive'}`}>
          {val ? 'Active' : 'Inactive'}
        </span>
      ),
    },
  ]

  const fetchData = async () => {
    setLoading(true)
    try {
      let url = `${API_URL}/api/admin/cost-items?include_inactive=true`
      if (filterRegion) url += `&region=${encodeURIComponent(filterRegion)}`
      if (filterCategory) url += `&category=${encodeURIComponent(filterCategory)}`
      const res = await authFetch(url)
      const json = await res.json()
      setData(json.data || [])
    } catch (err) {
      console.error('Failed to fetch cost items:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [filterRegion, filterCategory])

  const handleEdit = (item) => {
    setEditItem(item)
    setFormData({
      cost_code: item.cost_code,
      name_vi: item.name_vi || '',
      name_en: item.name_en || '',
      category: item.category || '',
      region: item.region || '',
      service_type: item.service_type || '',
      customer_code: item.customer_code || '',
      default_price: item.default_price || 0,
      selling_price: item.selling_price || 0,
      unit: item.unit || 'UNIT',
      currency: item.currency || 'VND',
      notes: item.notes || '',
      is_active: item.is_active,
    })
    setShowForm(true)
  }

  const handleDelete = async (item) => {
    if (!confirm(`Xóa chi phí "${item.name_vi}"?`)) return
    try {
      await authFetch(`${API_URL}/api/admin/cost-items/${item.cost_item_id}`, {
        method: 'DELETE',
      })
      fetchData()
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const url = editItem
        ? `${API_URL}/api/admin/cost-items/${editItem.cost_item_id}`
        : `${API_URL}/api/admin/cost-items`
      const method = editItem ? 'PUT' : 'POST'

      await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })

      setShowForm(false)
      setEditItem(null)
      setFormData({
        cost_code: '',
        name_vi: '',
        name_en: '',
        category: '',
        region: '',
        service_type: '',
        customer_code: '',
        default_price: 0,
        selling_price: 0,
        unit: 'UNIT',
        currency: 'VND',
        notes: '',
        is_active: true,
      })
      fetchData()
    } catch (err) {
      console.error('Save failed:', err)
    }
  }

  return (
    <div className="admin-tab-content">
      <div className="tab-header">
        <h3>Danh mục Chi phí</h3>
        <div className="tab-filters" style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <select value={filterRegion} onChange={(e) => setFilterRegion(e.target.value)}>
            <option value="">Tất cả khu vực</option>
            {REGIONS.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
          <select value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}>
            <option value="">Tất cả danh mục</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <button className="btn-primary" onClick={() => setShowForm(true)}>
            + Thêm Chi phí
          </button>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={data}
        loading={loading}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>{editItem ? 'Sửa Chi phí' : 'Thêm Chi phí'}</h3>
            <form onSubmit={handleSubmit}>
              <div className="form-row">
                <div className="form-group">
                  <label>Mã chi phí *</label>
                  <input
                    type="text"
                    value={formData.cost_code}
                    onChange={(e) =>
                      setFormData({ ...formData, cost_code: e.target.value.toUpperCase() })
                    }
                    disabled={!!editItem}
                    required
                    placeholder="VD: HQ-MTKLX"
                  />
                </div>
                <div className="form-group">
                  <label>Khu vực</label>
                  <select
                    value={formData.region}
                    onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                  >
                    <option value="">-- Chọn khu vực --</option>
                    {REGIONS.map((r) => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label>Tên chi phí (Tiếng Việt) *</label>
                <input
                  type="text"
                  value={formData.name_vi}
                  onChange={(e) => setFormData({ ...formData, name_vi: e.target.value })}
                  required
                  placeholder="VD: Mở tờ khai luồng xanh"
                />
              </div>
              <div className="form-group">
                <label>Tên chi phí (English)</label>
                <input
                  type="text"
                  value={formData.name_en}
                  onChange={(e) => setFormData({ ...formData, name_en: e.target.value })}
                  placeholder="VD: Green lane declaration"
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Danh mục</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  >
                    <option value="">-- Chọn danh mục --</option>
                    {CATEGORIES.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Loại dịch vụ</label>
                  <input
                    type="text"
                    value={formData.service_type}
                    onChange={(e) => setFormData({ ...formData, service_type: e.target.value })}
                    placeholder="VD: FCL, LCL, AIR"
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Giá mặc định</label>
                  <input
                    type="number"
                    value={formData.default_price}
                    onChange={(e) =>
                      setFormData({ ...formData, default_price: parseFloat(e.target.value) || 0 })
                    }
                  />
                </div>
                <div className="form-group">
                  <label>Giá bán khách</label>
                  <input
                    type="number"
                    value={formData.selling_price}
                    onChange={(e) =>
                      setFormData({ ...formData, selling_price: parseFloat(e.target.value) || 0 })
                    }
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Đơn vị tính</label>
                  <select
                    value={formData.unit}
                    onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                  >
                    {UNITS.map((u) => (
                      <option key={u} value={u}>{u}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Mã khách hàng</label>
                  <input
                    type="text"
                    value={formData.customer_code}
                    onChange={(e) => setFormData({ ...formData, customer_code: e.target.value })}
                    placeholder="Để trống = áp dụng tất cả"
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Ghi chú</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={2}
                />
              </div>
              <div className="form-group checkbox">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                  Đang sử dụng
                </label>
              </div>
              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>
                  Hủy
                </button>
                <button type="submit" className="btn-primary">
                  Lưu
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

// Vendors Management
function VendorsTab() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [formData, setFormData] = useState({
    vendor_code: '',
    vendor_name: '',
    short_name: '',
    address: '',
    phone: '',
    email: '',
    tax_code: '',
    is_active: true,
  })

  const columns = [
    { key: 'vendor_code', label: 'Code' },
    { key: 'vendor_name', label: 'Name' },
    { key: 'short_name', label: 'Short Name' },
    { key: 'phone', label: 'Phone' },
    { key: 'email', label: 'Email' },
    {
      key: 'is_active',
      label: 'Status',
      render: (val) => (
        <span className={`status-pill ${val ? 'active' : 'inactive'}`}>
          {val ? 'Active' : 'Inactive'}
        </span>
      ),
    },
  ]

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await authFetch(`${API_URL}/api/admin/vendors?include_inactive=true`)
      const json = await res.json()
      setData(json.data || [])
    } catch (err) {
      console.error('Failed to fetch vendors:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleEdit = (item) => {
    setEditItem(item)
    setFormData({
      vendor_code: item.vendor_code,
      vendor_name: item.vendor_name || '',
      short_name: item.short_name || '',
      address: item.address || '',
      phone: item.phone || '',
      email: item.email || '',
      tax_code: item.tax_code || '',
      is_active: item.is_active,
    })
    setShowForm(true)
  }

  const handleDelete = async (item) => {
    if (!confirm(`Delete vendor "${item.vendor_name}"?`)) return
    try {
      await authFetch(`${API_URL}/api/admin/vendors/${item.vendor_id}`, {
        method: 'DELETE',
      })
      fetchData()
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const url = editItem
        ? `${API_URL}/api/admin/vendors/${editItem.vendor_id}`
        : `${API_URL}/api/admin/vendors`
      const method = editItem ? 'PUT' : 'POST'

      await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })

      setShowForm(false)
      setEditItem(null)
      setFormData({
        vendor_code: '',
        vendor_name: '',
        short_name: '',
        address: '',
        phone: '',
        email: '',
        tax_code: '',
        is_active: true,
      })
      fetchData()
    } catch (err) {
      console.error('Save failed:', err)
    }
  }

  return (
    <div className="admin-tab-content">
      <div className="tab-header">
        <h3>Vendors</h3>
        <button className="btn-primary" onClick={() => setShowForm(true)}>
          + Add Vendor
        </button>
      </div>

      <DataTable
        columns={columns}
        data={data}
        loading={loading}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>{editItem ? 'Edit Vendor' : 'Add Vendor'}</h3>
            <form onSubmit={handleSubmit}>
              <div className="form-row">
                <div className="form-group">
                  <label>Code *</label>
                  <input
                    type="text"
                    value={formData.vendor_code}
                    onChange={(e) =>
                      setFormData({ ...formData, vendor_code: e.target.value.toUpperCase() })
                    }
                    disabled={!!editItem}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Tax Code</label>
                  <input
                    type="text"
                    value={formData.tax_code}
                    onChange={(e) => setFormData({ ...formData, tax_code: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Name *</label>
                <input
                  type="text"
                  value={formData.vendor_name}
                  onChange={(e) => setFormData({ ...formData, vendor_name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Short Name</label>
                <input
                  type="text"
                  value={formData.short_name}
                  onChange={(e) => setFormData({ ...formData, short_name: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Address</label>
                <input
                  type="text"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Phone</label>
                  <input
                    type="text"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group checkbox">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                  Active
                </label>
              </div>
              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Save
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

// Customers Management
function CustomersTab() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [formData, setFormData] = useState({
    customer_code: '',
    company_name: '',
    short_name: '',
    address: '',
    contact_phone: '',
    contact_email: '',
    tax_code: '',
    is_active: true,
  })

  const columns = [
    { key: 'customer_code', label: 'Code' },
    { key: 'company_name', label: 'Company Name' },
    { key: 'short_name', label: 'Short Name' },
    { key: 'contact_phone', label: 'Phone' },
    { key: 'contact_email', label: 'Email' },
    {
      key: 'is_active',
      label: 'Status',
      render: (val) => (
        <span className={`status-pill ${val ? 'active' : 'inactive'}`}>
          {val ? 'Active' : 'Inactive'}
        </span>
      ),
    },
  ]

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await authFetch(`${API_URL}/api/admin/customers?include_inactive=true`)
      const json = await res.json()
      setData(json.data || [])
    } catch (err) {
      console.error('Failed to fetch customers:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleEdit = (item) => {
    setEditItem(item)
    setFormData({
      customer_code: item.customer_code,
      company_name: item.company_name || '',
      short_name: item.short_name || '',
      address: item.address || '',
      contact_phone: item.contact_phone || '',
      contact_email: item.contact_email || '',
      tax_code: item.tax_code || '',
      is_active: item.is_active,
    })
    setShowForm(true)
  }

  const handleDelete = async (item) => {
    if (!confirm(`Delete customer "${item.company_name}"?`)) return
    try {
      await authFetch(`${API_URL}/api/admin/customers/${item.customer_id}`, {
        method: 'DELETE',
      })
      fetchData()
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const url = editItem
        ? `${API_URL}/api/admin/customers/${editItem.customer_id}`
        : `${API_URL}/api/admin/customers`
      const method = editItem ? 'PUT' : 'POST'

      await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })

      setShowForm(false)
      setEditItem(null)
      setFormData({
        customer_code: '',
        company_name: '',
        short_name: '',
        address: '',
        contact_phone: '',
        contact_email: '',
        tax_code: '',
        is_active: true,
      })
      fetchData()
    } catch (err) {
      console.error('Save failed:', err)
    }
  }

  return (
    <div className="admin-tab-content">
      <div className="tab-header">
        <h3>Customers</h3>
        <button className="btn-primary" onClick={() => setShowForm(true)}>
          + Add Customer
        </button>
      </div>

      <DataTable
        columns={columns}
        data={data}
        loading={loading}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>{editItem ? 'Edit Customer' : 'Add Customer'}</h3>
            <form onSubmit={handleSubmit}>
              <div className="form-row">
                <div className="form-group">
                  <label>Code *</label>
                  <input
                    type="text"
                    value={formData.customer_code}
                    onChange={(e) =>
                      setFormData({ ...formData, customer_code: e.target.value.toUpperCase() })
                    }
                    disabled={!!editItem}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Tax Code</label>
                  <input
                    type="text"
                    value={formData.tax_code}
                    onChange={(e) => setFormData({ ...formData, tax_code: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Company Name *</label>
                <input
                  type="text"
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Short Name</label>
                <input
                  type="text"
                  value={formData.short_name}
                  onChange={(e) => setFormData({ ...formData, short_name: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Address</label>
                <input
                  type="text"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Phone</label>
                  <input
                    type="text"
                    value={formData.contact_phone}
                    onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Email</label>
                  <input
                    type="email"
                    value={formData.contact_email}
                    onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group checkbox">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                  Active
                </label>
              </div>
              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Save
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

// Buying Rates Tab - Grouped by Vendor with filters and sub-routes
function BuyingRatesTab() {
  const [summary, setSummary] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedVendor, setSelectedVendor] = useState(null)
  const [vendorDetail, setVendorDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [showAddModal, setShowAddModal] = useState(false)
  const [showUploadModal, setShowUploadModal] = useState(false)

  // Filter states
  const [filters, setFilters] = useState({
    search: '',
    vehicleType: '',
    rateType: '',
    minPrice: '',
    maxPrice: '',
  })
  const [availableFilters, setAvailableFilters] = useState({
    vehicle_types: [],
    rate_types: [],
    sub_routes: [],
  })
  const [expandedRoutes, setExpandedRoutes] = useState({})

  const fetchSummary = async () => {
    setLoading(true)
    try {
      const res = await authFetch(`${API_URL}/api/admin/buying-rates/summary`)
      const json = await res.json()
      setSummary(json.data || [])
    } catch (err) {
      console.error('Failed to fetch summary:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchVendorDetail = async (vendorId, filterParams = {}) => {
    setDetailLoading(true)
    try {
      const params = new URLSearchParams()
      if (filterParams.search) params.append('search', filterParams.search)
      if (filterParams.vehicleType) params.append('vehicle_type', filterParams.vehicleType)
      if (filterParams.rateType) params.append('rate_type', filterParams.rateType)
      if (filterParams.minPrice) params.append('min_price', filterParams.minPrice)
      if (filterParams.maxPrice) params.append('max_price', filterParams.maxPrice)

      const url = `${API_URL}/api/admin/buying-rates/vendor/${vendorId}${params.toString() ? '?' + params : ''}`
      const res = await authFetch(url)
      const json = await res.json()
      setVendorDetail(json)
      if (json.filters) {
        setAvailableFilters(json.filters)
      }
    } catch (err) {
      console.error('Failed to fetch vendor detail:', err)
    } finally {
      setDetailLoading(false)
    }
  }

  useEffect(() => {
    fetchSummary()
  }, [])

  // Apply filters when they change
  useEffect(() => {
    if (selectedVendor) {
      const timeoutId = setTimeout(() => {
        fetchVendorDetail(selectedVendor.vendor_id, filters)
      }, 300) // Debounce search
      return () => clearTimeout(timeoutId)
    }
  }, [filters, selectedVendor])

  const handleViewVendor = (vendor) => {
    setSelectedVendor(vendor)
    setFilters({ search: '', vehicleType: '', rateType: '', minPrice: '', maxPrice: '' })
    setExpandedRoutes({})
    fetchVendorDetail(vendor.vendor_id)
  }

  const handleBack = () => {
    setSelectedVendor(null)
    setVendorDetail(null)
    setFilters({ search: '', vehicleType: '', rateType: '', minPrice: '', maxPrice: '' })
  }

  const toggleRouteExpand = (routeKey) => {
    setExpandedRoutes(prev => ({
      ...prev,
      [routeKey]: !prev[routeKey]
    }))
  }

  const clearFilters = () => {
    setFilters({ search: '', vehicleType: '', rateType: '', minPrice: '', maxPrice: '' })
  }

  const hasActiveFilters = filters.search || filters.vehicleType || filters.rateType || filters.minPrice || filters.maxPrice

  // Render vendor detail view with filters
  if (selectedVendor && vendorDetail) {
    return (
      <div className="admin-tab-content">
        <div className="tab-header">
          <button className="btn-secondary" onClick={handleBack}>
            ← Quay lại
          </button>
          <h3>{vendorDetail.vendor?.name || selectedVendor.vendor_name}</h3>
          {vendorDetail.file_reference_id && (
            <button className="btn-primary">
              Tải file báo giá gốc
            </button>
          )}
        </div>

        <div className="vendor-detail-info">
          <div className="info-row">
            <span className="info-label">Mã NCC:</span>
            <span className="info-value">{vendorDetail.vendor?.code}</span>
          </div>
          <div className="info-row">
            <span className="info-label">Ngày hiệu lực:</span>
            <span className="info-value">{vendorDetail.effective_date || 'N/A'}</span>
          </div>
          <div className="info-row">
            <span className="info-label">Tổng số rate:</span>
            <span className="info-value">{vendorDetail.total_rates} rates</span>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="filter-controls">
          <div className="filter-row">
            <div className="filter-group search-group">
              <input
                type="text"
                placeholder="Tìm theo địa điểm (ví dụ: KCN Thăng Long, Nội Bài...)"
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                className="filter-input search-input"
              />
            </div>
            <div className="filter-group">
              <select
                value={filters.vehicleType}
                onChange={(e) => setFilters({ ...filters, vehicleType: e.target.value })}
                className="filter-select"
              >
                <option value="">Tất cả loại xe</option>
                {availableFilters.vehicle_types?.map(vt => (
                  <option key={vt} value={vt}>{vt}</option>
                ))}
              </select>
            </div>
            <div className="filter-group">
              <select
                value={filters.rateType}
                onChange={(e) => setFilters({ ...filters, rateType: e.target.value })}
                className="filter-select"
              >
                <option value="">Tất cả loại rate</option>
                {availableFilters.rate_types?.map(rt => (
                  <option key={rt} value={rt}>{rt === 'REFRIGERATED' ? 'Đông lạnh' : rt}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="filter-row">
            <div className="filter-group price-group">
              <label>Giá từ:</label>
              <input
                type="number"
                placeholder="0"
                value={filters.minPrice}
                onChange={(e) => setFilters({ ...filters, minPrice: e.target.value })}
                className="filter-input price-input"
              />
            </div>
            <div className="filter-group price-group">
              <label>đến:</label>
              <input
                type="number"
                placeholder="10,000,000"
                value={filters.maxPrice}
                onChange={(e) => setFilters({ ...filters, maxPrice: e.target.value })}
                className="filter-input price-input"
              />
            </div>
            {hasActiveFilters && (
              <button className="btn-clear-filter" onClick={clearFilters}>
                Xóa bộ lọc
              </button>
            )}
          </div>
        </div>

        {detailLoading ? (
          <div className="loading-state">Đang tải chi tiết...</div>
        ) : vendorDetail.routes?.length === 0 ? (
          <div className="empty-state">Không tìm thấy kết quả phù hợp với bộ lọc</div>
        ) : (
          <div className="routes-list">
            {vendorDetail.routes?.map((route, idx) => (
              <div key={idx} className="route-card">
                <div
                  className="route-header clickable"
                  onClick={() => toggleRouteExpand(route.route)}
                >
                  <h4>
                    <span className="expand-icon">{expandedRoutes[route.route] ? '▼' : '▶'}</span>
                    {route.route}
                  </h4>
                  <span className="sub-routes-count">
                    {route.sub_routes_count || route.sub_routes?.length || 0} điểm giao
                  </span>
                </div>

                {expandedRoutes[route.route] && (
                  <div className="sub-routes-list">
                    {route.sub_routes?.map((subRoute, sIdx) => (
                      <div key={sIdx} className="sub-route-card">
                        <div className="sub-route-header">
                          <h5>{subRoute.sub_route}</h5>
                          {subRoute.rate_type && (
                            <span className={`rate-type-badge ${subRoute.rate_type.toLowerCase()}`}>
                              {subRoute.rate_type === 'REFRIGERATED' ? 'Đông lạnh' : subRoute.rate_type}
                            </span>
                          )}
                          {subRoute.temperature_range && (
                            <span className="temp-badge">{subRoute.temperature_range}</span>
                          )}
                        </div>
                        <table className="rates-matrix compact">
                          <thead>
                            <tr>
                              <th>Loại xe</th>
                              <th>Giá (VND)</th>
                              <th>Đơn vị</th>
                            </tr>
                          </thead>
                          <tbody>
                            {subRoute.rates?.map((rate, rIdx) => (
                              <tr key={rIdx}>
                                <td className="vehicle-type">{rate.vehicle_type}</td>
                                <td className="price">{Number(rate.price).toLocaleString()}</td>
                                <td className="unit">{rate.unit || 'TRIP'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  const handleRateSaved = () => {
    fetchSummary()
    if (selectedVendor) {
      fetchVendorDetail(selectedVendor.vendor_id, filters)
    }
  }

  // Render summary view (vendor cards)
  return (
    <div className="admin-tab-content">
      <div className="tab-header">
        <h3>Buying Rates - Báo giá mua vào (theo Nhà cung cấp)</h3>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn-secondary" onClick={() => setShowUploadModal(true)}>
            Upload Excel
          </button>
          <button className="btn-primary" onClick={() => setShowAddModal(true)}>
            + Thêm báo giá
          </button>
        </div>
      </div>

      <RateFormModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSave={handleRateSaved}
        rateType="buying"
      />

      <RateUploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onImported={handleRateSaved}
        rateType="buying"
      />

      {loading ? (
        <div className="loading-state">Đang tải...</div>
      ) : summary.length === 0 ? (
        <div className="empty-state">Chưa có dữ liệu báo giá</div>
      ) : (
        <div className="vendor-cards-grid">
          {summary.map((vendor) => (
            <div
              key={vendor.vendor_id}
              className="vendor-card"
              onClick={() => handleViewVendor(vendor)}
            >
              <div className="vendor-card-header">
                <h4>{vendor.vendor_name}</h4>
                <span className="vendor-code">{vendor.vendor_code}</span>
              </div>
              <div className="vendor-card-stats">
                <div className="stat">
                  <span className="stat-value">{vendor.rate_count}</span>
                  <span className="stat-label">Rates</span>
                </div>
                <div className="stat">
                  <span className="stat-value">{vendor.routes_count || vendor.routes?.length || 0}</span>
                  <span className="stat-label">Tuyến</span>
                </div>
              </div>
              <div className="vendor-card-meta">
                {vendor.vehicle_types?.length > 0 && (
                  <div className="meta-row">
                    <span className="meta-label">Loại xe:</span>
                    <span className="meta-value">{vendor.vehicle_types.slice(0, 4).join(', ')}{vendor.vehicle_types.length > 4 ? '...' : ''}</span>
                  </div>
                )}
                {vendor.rate_types?.length > 0 && (
                  <div className="meta-row">
                    <span className="meta-label">Loại:</span>
                    <span className="meta-value">
                      {vendor.rate_types.map(t => t === 'REFRIGERATED' ? 'Đông lạnh' : t).join(', ')}
                    </span>
                  </div>
                )}
                {vendor.effective_date && (
                  <div className="meta-row">
                    <span className="meta-label">Hiệu lực:</span>
                    <span className="meta-value">{vendor.effective_date}</span>
                  </div>
                )}
              </div>
              <div className="vendor-card-action">
                <span>Xem chi tiết</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Selling Rates Tab - Grouped by Customer
function SellingRatesTab() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [showUploadModal, setShowUploadModal] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await authFetch(`${API_URL}/api/admin/selling-rates?include_inactive=true`)
      const json = await res.json()
      setData(json.data || [])
    } catch (err) {
      console.error('Failed to fetch selling rates:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleRateSaved = () => {
    fetchData()
  }

  if (loading) return <div className="loading-state">Đang tải...</div>

  return (
    <div className="admin-tab-content">
      <div className="tab-header">
        <h3>Selling Rates - Báo giá bán ra (theo Khách hàng)</h3>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn-secondary" onClick={() => setShowUploadModal(true)}>
            Upload Excel
          </button>
          <button className="btn-primary" onClick={() => setShowAddModal(true)}>
            + Thêm báo giá
          </button>
        </div>
      </div>

      <RateFormModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSave={handleRateSaved}
        rateType="selling"
      />

      <RateUploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onImported={handleRateSaved}
        rateType="selling"
      />

      {data.length === 0 ? (
        <div className="empty-state">Chưa có dữ liệu báo giá bán</div>
      ) : (
        <table className="admin-table">
          <thead>
            <tr>
              <th>Khách hàng</th>
              <th>Loại xe</th>
              <th>Tuyến / Ghi chú</th>
              <th>Đơn giá</th>
              <th>ĐVT</th>
              <th>Ngày HL</th>
              <th>Trạng thái</th>
            </tr>
          </thead>
          <tbody>
            {data.map(item => (
              <tr key={item.id}>
                <td>{item.customers?.short_name || item.customer_id}</td>
                <td>{item.vehicle_type || '-'}</td>
                <td>{item.notes || (item.master_routes ? `${item.master_routes.origin} → ${item.master_routes.destination}` : '-')}</td>
                <td style={{ textAlign: 'right' }}>{formatCurrency(item.price)}</td>
                <td>{item.unit || 'TRIP'}</td>
                <td>{item.effective_date || '-'}</td>
                <td>
                  <span className={`status-badge ${item.is_active ? 'active' : 'inactive'}`}>
                    {item.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

// Legacy RatesTab for backwards compatibility
function RatesTab({ type }) {
  if (type === 'buying') {
    return <BuyingRatesTab />
  }
  return <SellingRatesTab />
}

// Main Admin Panel
export default function AdminPanel() {
  const [activeTab, setActiveTab] = useState('service-types')

  const renderTabContent = () => {
    switch (activeTab) {
      case 'users':
        return <UsersTab />
      case 'audit-logs':
        return <AuditLogsTab />
      case 'service-types':
        return <ServiceTypesTab />
      case 'cost-items':
        return <CostItemsTab />
      case 'vendors':
        return <VendorsTab />
      case 'customers':
        return <CustomersTab />
      case 'selling-rates':
        return <RatesTab type="selling" />
      case 'buying-rates':
        return <RatesTab type="buying" />
      default:
        return <ServiceTypesTab />
    }
  }

  return (
    <div className="admin-panel">
      <div className="admin-header">
        <h2>Master Data Management</h2>
      </div>

      <div className="admin-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`admin-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </div>

      <div className="admin-content">{renderTabContent()}</div>
    </div>
  )
}
