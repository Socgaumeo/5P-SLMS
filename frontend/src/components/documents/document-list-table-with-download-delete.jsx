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
  BBGH: { bg: '#FEF3C7', color: '#B45309', label: 'BBGH' },
  OTHER: { bg: '#F1F5F9', color: '#64748B', label: 'Khác' },
}

const SOURCE_ICONS = {
  telegram: '📱',
  web_upload: '🌐',
  gdrive: '☁️',
  onedrive: '☁️',
  supabase: '🗄️',
  external_link: '🔗',
}

function isImage(doc) {
  const mt = (doc.mime_type || '').toLowerCase()
  if (mt.startsWith('image/')) return true
  const ext = (doc.file_name || '').split('.').pop().toLowerCase()
  return ['jpg','jpeg','png','webp','gif'].includes(ext)
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
  const [previewUrl, setPreviewUrl] = useState(null)
  const [previewName, setPreviewName] = useState('')

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
                  {isImage(doc) && doc.external_url ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <img
                        src={doc.external_url}
                        alt={doc.file_name}
                        onClick={() => { setPreviewUrl(doc.external_url); setPreviewName(doc.file_name) }}
                        style={{ width: 48, height: 48, objectFit: 'cover', borderRadius: 4, cursor: 'zoom-in', border: '1px solid #e2e8f0' }}
                      />
                      <span>{doc.file_name}</span>
                    </div>
                  ) : (
                    doc.file_name
                  )}
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
      {previewUrl && (
        <div
          onClick={() => setPreviewUrl(null)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'zoom-out', padding: '24px' }}
        >
          <div style={{ position: 'relative', maxWidth: '95vw', maxHeight: '95vh' }} onClick={(e) => e.stopPropagation()}>
            <img src={previewUrl} alt={previewName} style={{ maxWidth: '95vw', maxHeight: '90vh', display: 'block', borderRadius: 6 }} />
            <div style={{ position: 'absolute', top: -32, right: 0, color: '#fff', fontSize: 13 }}>
              {previewName} · <a href={previewUrl} target="_blank" rel="noreferrer" style={{ color: '#93c5fd' }}>Mở tab mới</a> · <span onClick={() => setPreviewUrl(null)} style={{ cursor: 'pointer' }}>✕ Đóng</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
