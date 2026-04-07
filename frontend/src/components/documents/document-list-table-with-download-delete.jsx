// frontend/src/components/documents/document-list-table-with-download-delete.jsx
/**
 * Table listing documents attached to a job.
 * Shows doc type badge, filename, source (Telegram/Web), uploader, date.
 * Actions: download, delete (with permission check).
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
  telegram: '📱',
  web_upload: '🌐',
  gdrive: '☁️',
  onedrive: '☁️',
  external_link: '🔗',
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function formatFileSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function DocumentListTable({ jobId, refreshTrigger, currentUser }) {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchDocuments = async () => {
    try {
      setLoading(true)
      const res = await authFetch(`${API_URL}/api/documents?job_id=${jobId}`)
      const data = await res.json()
      setDocuments(data.data || [])
    } catch (err) {
      setError('Không thể tải danh sách chứng từ')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (jobId) fetchDocuments()
  }, [jobId, refreshTrigger])

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

  const handleDelete = async (doc) => {
    if (!confirm(`Xóa chứng từ "${doc.file_name}"?`)) return
    try {
      const res = await authFetch(`${API_URL}/api/documents/${doc.id}`, { method: 'DELETE' })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Delete failed')
      }
      fetchDocuments()
    } catch (err) {
      alert('Lỗi xóa: ' + err.message)
    }
  }

  const canDelete = (doc) => {
    if (!currentUser) return false
    if (currentUser.role === 'ADMIN') return true
    return doc.uploaded_by === currentUser.user_id
  }

  if (loading) return <div className="loading-state">Đang tải...</div>
  if (error) return <div className="error-state">{error}</div>
  if (documents.length === 0) return <div className="empty-state">Chưa có chứng từ nào</div>

  return (
    <div className="doc-list-table">
      <table className="admin-table">
        <thead>
          <tr>
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
                  <span
                    className="doc-type-badge"
                    style={{ backgroundColor: badge.bg, color: badge.color }}
                  >
                    {badge.label}
                  </span>
                </td>
                <td className="doc-filename" title={doc.file_name}>
                  {doc.file_name}
                </td>
                <td>{formatFileSize(doc.file_size)}</td>
                <td title={doc.storage_type}>
                  {SOURCE_ICONS[doc.storage_type] || '📄'}
                </td>
                <td>{doc.uploaded_by_telegram || '-'}</td>
                <td>{formatDate(doc.uploaded_at)}</td>
                <td className="action-cell">
                  <button className="btn-edit" onClick={() => handleDownload(doc)}>
                    Tải về
                  </button>
                  {canDelete(doc) && (
                    <button className="btn-delete" onClick={() => handleDelete(doc)}>
                      Xóa
                    </button>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
