// frontend/src/components/documents/document-management-page-with-filters.jsx
/**
 * Standalone Document Management page for kế toán.
 * Filter by month, customer, doc_type. Batch download as ZIP.
 * Accessible via NavItem "Chứng từ" in sidebar.
 */

import { useState, useEffect } from 'react'
import { authFetch, API_URL } from '../../utils/auth-fetch'

const TYPE_BADGES = {
  AN: { bg: '#DBEAFE', color: '#2563EB', label: 'AN' },
  DEBIT: { bg: '#D1FAE5', color: '#059669', label: 'Debit' },
  DO: { bg: '#FEF3C7', color: '#D97706', label: 'DO' },
  CD: { bg: '#E0E7FF', color: '#4F46E5', label: 'CD' },
  CO: { bg: '#FCE7F3', color: '#DB2777', label: 'C/O' },
  INVOICE: { bg: '#FEE2E2', color: '#DC2626', label: 'Hóa đơn' },
  AWB: { bg: '#E0E7FF', color: '#4F46E5', label: 'AWB' },
  BL: { bg: '#DBEAFE', color: '#2563EB', label: 'B/L' },
  PACKING_LIST: { bg: '#F3E8FF', color: '#7C3AED', label: 'PL' },
  OTHER: { bg: '#F1F5F9', color: '#64748B', label: 'Khác' },
}

const SOURCE_ICONS = {
  telegram: '📱', web_upload: '🌐', gdrive: '☁️', onedrive: '☁️', external_link: '🔗',
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('vi-VN', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

function formatFileSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function DocumentManagementPage() {
  const [documents, setDocuments] = useState([])
  const [customers, setCustomers] = useState([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)

  // Filters
  const [month, setMonth] = useState(() => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  })
  const [customerId, setCustomerId] = useState('')
  const [docType, setDocType] = useState('')

  // Batch selection
  const [selected, setSelected] = useState(new Set())
  const [downloading, setDownloading] = useState(false)

  // Fetch customers for dropdown
  useEffect(() => {
    authFetch(`${API_URL}/api/customers`)
      .then((r) => r.json())
      .then((d) => setCustomers(Array.isArray(d) ? d : d.data || []))
      .catch(() => {})
  }, [])

  // Fetch documents when filters change
  useEffect(() => {
    fetchDocuments()
  }, [month, customerId, docType])

  const fetchDocuments = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (month) params.append('month', month)
      if (customerId) params.append('customer_id', customerId)
      if (docType) params.append('doc_type', docType)
      params.append('limit', '100')

      const res = await authFetch(`${API_URL}/api/documents?${params}`)
      const data = await res.json()
      setDocuments(data.data || [])
      setTotal(data.total || 0)
      setSelected(new Set())
    } catch {
      setDocuments([])
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async (doc) => {
    try {
      const res = await authFetch(`${API_URL}/api/documents/${doc.id}/download`)
      if (!res.ok) throw new Error('Download failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = doc.file_name
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      alert('Lỗi tải file: ' + err.message)
    }
  }

  const handleBatchDownload = async () => {
    if (selected.size === 0) return
    setDownloading(true)
    try {
      const res = await authFetch(`${API_URL}/api/documents/batch-download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_ids: [...selected] }),
      })
      if (!res.ok) throw new Error('Batch download failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `documents_${month}.zip`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      alert('Lỗi: ' + err.message)
    } finally {
      setDownloading(false)
    }
  }

  const toggleSelect = (id) => {
    const next = new Set(selected)
    next.has(id) ? next.delete(id) : next.add(id)
    setSelected(next)
  }

  const toggleAll = () => {
    if (selected.size === documents.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(documents.map((d) => d.id)))
    }
  }

  // Get customer name from nested join data
  const getCustomerName = (doc) => {
    const jobs = doc.jobs
    if (!jobs) return '-'
    const cust = jobs.customers
    return cust?.short_name || cust?.company_name || '-'
  }

  return (
    <div className="doc-management-page">
      <h2 style={{ marginBottom: '16px' }}>Quản lý Chứng từ</h2>

      {/* Filter Bar */}
      <div className="doc-filter-bar">
        <input
          type="month"
          value={month}
          onChange={(e) => setMonth(e.target.value)}
          className="doc-filter-input"
        />
        <select
          value={customerId}
          onChange={(e) => setCustomerId(e.target.value)}
          className="doc-filter-select"
        >
          <option value="">Tất cả khách hàng</option>
          {customers.map((c) => (
            <option key={c.customer_id} value={c.customer_id}>
              {c.short_name || c.company_name}
            </option>
          ))}
        </select>
        <select
          value={docType}
          onChange={(e) => setDocType(e.target.value)}
          className="doc-filter-select"
        >
          <option value="">Tất cả loại</option>
          {Object.entries(TYPE_BADGES).map(([k, v]) => (
            <option key={k} value={k}>{v.label}</option>
          ))}
        </select>

        {selected.size > 0 && (
          <button
            className="btn-primary"
            onClick={handleBatchDownload}
            disabled={downloading}
          >
            {downloading ? 'Đang tải...' : `Tải ${selected.size} file (ZIP)`}
          </button>
        )}

        <span className="doc-total-count">Tổng: {total} chứng từ</span>
      </div>

      {/* Table */}
      {loading ? (
        <div className="loading-state">Đang tải...</div>
      ) : documents.length === 0 ? (
        <div className="empty-state">Không có chứng từ nào</div>
      ) : (
        <table className="admin-table">
          <thead>
            <tr>
              <th style={{ width: '36px' }}>
                <input
                  type="checkbox"
                  checked={selected.size === documents.length && documents.length > 0}
                  onChange={toggleAll}
                />
              </th>
              <th>Job</th>
              <th>Khách hàng</th>
              <th>Loại</th>
              <th>Tên file</th>
              <th>Kích thước</th>
              <th>Nguồn</th>
              <th>Người tải</th>
              <th>Ngày</th>
              <th>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => {
              const badge = TYPE_BADGES[doc.doc_type] || TYPE_BADGES.OTHER
              return (
                <tr key={doc.id}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selected.has(doc.id)}
                      onChange={() => toggleSelect(doc.id)}
                    />
                  </td>
                  <td><code>{doc.jobs?.job_no || '-'}</code></td>
                  <td>{getCustomerName(doc)}</td>
                  <td>
                    <span
                      className="doc-type-badge"
                      style={{ backgroundColor: badge.bg, color: badge.color }}
                    >
                      {badge.label}
                    </span>
                  </td>
                  <td className="doc-filename" title={doc.file_name}>{doc.file_name}</td>
                  <td>{formatFileSize(doc.file_size)}</td>
                  <td>{SOURCE_ICONS[doc.storage_type] || '📄'}</td>
                  <td>{doc.uploaded_by_telegram || '-'}</td>
                  <td>{formatDate(doc.uploaded_at)}</td>
                  <td className="action-cell">
                    <button className="btn-edit" onClick={() => handleDownload(doc)}>
                      Tải về
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </div>
  )
}
