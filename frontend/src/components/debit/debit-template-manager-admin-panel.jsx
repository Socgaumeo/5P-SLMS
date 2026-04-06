// frontend/src/components/debit/debit-template-manager-admin-panel.jsx
/**
 * Admin panel tab for managing debit templates.
 * CRUD: list, create (upload Excel + field mapping), edit, delete.
 * Rendered inside AdminPanel as a tab.
 */

import { useState, useEffect } from 'react'
import { authFetch, API_URL } from '../../utils/auth-fetch'

export default function DebitTemplateManagerPanel() {
  const [templates, setTemplates] = useState([])
  const [customers, setCustomers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [error, setError] = useState('')

  // Form state
  const [formName, setFormName] = useState('')
  const [formCustomerId, setFormCustomerId] = useState('')
  const [formMapping, setFormMapping] = useState('{}')
  const [formFile, setFormFile] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchTemplates()
    authFetch(`${API_URL}/api/admin/customers`).then(r => r.json()).then(d => setCustomers(d.data || []))
  }, [])

  const fetchTemplates = async () => {
    setLoading(true)
    try {
      const res = await authFetch(`${API_URL}/api/debit/templates`)
      const data = await res.json()
      setTemplates(data.data || [])
    } catch { setTemplates([]) }
    finally { setLoading(false) }
  }

  const resetForm = () => {
    setFormName(''); setFormCustomerId(''); setFormMapping('{}'); setFormFile(null)
    setEditItem(null); setShowForm(false); setError('')
  }

  const handleEdit = (tmpl) => {
    setEditItem(tmpl)
    setFormName(tmpl.template_name)
    setFormCustomerId(String(tmpl.customer_id))
    setFormMapping(JSON.stringify(tmpl.field_mapping, null, 2))
    setFormFile(null)
    setShowForm(true)
  }

  const handleSave = async () => {
    if (!formName || !formCustomerId) { setError('Tên và khách hàng bắt buộc'); return }
    try { JSON.parse(formMapping) } catch { setError('Field mapping JSON không hợp lệ'); return }

    setSaving(true); setError('')
    try {
      const formData = new FormData()
      formData.append('template_name', formName)
      formData.append('customer_id', formCustomerId)
      formData.append('field_mapping', formMapping)
      if (formFile) formData.append('file', formFile)

      const url = editItem
        ? `${API_URL}/api/debit/templates/${editItem.id}`
        : `${API_URL}/api/debit/templates`
      const method = editItem ? 'PUT' : 'POST'

      const res = await authFetch(url, { method, body: formData })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Save failed')
      }
      resetForm()
      fetchTemplates()
    } catch (err) {
      setError(err.message)
    } finally { setSaving(false) }
  }

  const handleDelete = async (tmpl) => {
    if (!confirm(`Xóa template "${tmpl.template_name}"?`)) return
    try {
      await authFetch(`${API_URL}/api/debit/templates/${tmpl.id}`, { method: 'DELETE' })
      fetchTemplates()
    } catch (err) { alert('Lỗi: ' + err.message) }
  }

  const getCustomerName = (cid) => {
    const c = customers.find(x => x.customer_id === cid)
    return c?.short_name || c?.company_name || '-'
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
        <h3>Debit Templates</h3>
        <button className="btn-primary" onClick={() => { resetForm(); setShowForm(true) }}>+ Thêm Template</button>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px', marginBottom: '16px' }}>
          <h4>{editItem ? 'Sửa Template' : 'Thêm Template Mới'}</h4>
          <div style={{ display: 'grid', gap: '10px', marginTop: '10px' }}>
            <input placeholder="Tên template" value={formName} onChange={e => setFormName(e.target.value)} style={{ padding: '8px', border: '1px solid #e2e8f0', borderRadius: '6px' }} />
            <select value={formCustomerId} onChange={e => setFormCustomerId(e.target.value)} className="doc-filter-select">
              <option value="">-- Chọn khách hàng --</option>
              {customers.map(c => <option key={c.customer_id} value={c.customer_id}>{c.short_name || c.company_name}</option>)}
            </select>
            <div>
              <label style={{ fontSize: '13px', fontWeight: '500' }}>File Excel template:</label>
              <input type="file" accept=".xlsx,.xls" onChange={e => setFormFile(e.target.files[0])} style={{ marginTop: '4px' }} />
            </div>
            <div>
              <label style={{ fontSize: '13px', fontWeight: '500' }}>Field Mapping (JSON):</label>
              <textarea value={formMapping} onChange={e => setFormMapping(e.target.value)} rows={8} style={{ width: '100%', fontFamily: 'monospace', fontSize: '12px', padding: '8px', border: '1px solid #e2e8f0', borderRadius: '6px', marginTop: '4px' }} />
            </div>
          </div>
          {error && <div className="doc-upload-error">{error}</div>}
          <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
            <button className="btn-primary" onClick={handleSave} disabled={saving}>{saving ? 'Đang lưu...' : 'Lưu'}</button>
            <button className="btn-secondary" onClick={resetForm}>Hủy</button>
          </div>
        </div>
      )}

      {/* Table */}
      {loading ? <div className="loading-state">Đang tải...</div> :
        templates.length === 0 ? <div className="empty-state">Chưa có template nào</div> : (
          <table className="admin-table">
            <thead><tr><th>Tên</th><th>Khách hàng</th><th>Ngày tạo</th><th>Thao tác</th></tr></thead>
            <tbody>
              {templates.map(t => (
                <tr key={t.id}>
                  <td>{t.template_name}</td>
                  <td>{t.customers?.short_name || t.customers?.company_name || getCustomerName(t.customer_id)}</td>
                  <td>{t.created_at ? new Date(t.created_at).toLocaleDateString('vi-VN') : '-'}</td>
                  <td className="action-cell">
                    <button className="btn-edit" onClick={() => handleEdit(t)}>Sửa</button>
                    <button className="btn-delete" onClick={() => handleDelete(t)}>Xóa</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
    </div>
  )
}
