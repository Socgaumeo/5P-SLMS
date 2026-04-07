// frontend/src/components/documents/document-upload-zone.jsx
/**
 * Drag & drop upload zone + file picker for manual document uploads.
 * Used in JobDetailModal "Chứng từ" tab as fallback for non-Telegram uploads.
 */

import { useState, useRef } from 'react'
import { authFetch, API_URL } from '../../utils/auth-fetch'

const DOC_TYPES = [
  { value: 'AN', label: 'Arrival Notice' },
  { value: 'DEBIT', label: 'Debit Note' },
  { value: 'DO', label: 'Delivery Order' },
  { value: 'CD', label: 'Customs Declaration' },
  { value: 'CO', label: 'C/O' },
  { value: 'INVOICE', label: 'Hóa đơn' },
  { value: 'AWB', label: 'Air Waybill' },
  { value: 'BL', label: 'Bill of Lading' },
  { value: 'PACKING_LIST', label: 'Packing List' },
  { value: 'OTHER', label: 'Khác' },
]

export default function DocumentUploadZone({ jobId, onUploadSuccess }) {
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [docType, setDocType] = useState('OTHER')
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)

  const handleUpload = async (file) => {
    if (!file) return
    setError('')
    setUploading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('job_id', jobId)
      formData.append('doc_type', docType)

      const res = await authFetch(`${API_URL}/api/documents/upload`, {
        method: 'POST',
        body: formData,
        // Don't set Content-Type — browser sets it with boundary for FormData
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Upload failed')
      }

      if (onUploadSuccess) onUploadSuccess()
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleUpload(file)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) handleUpload(file)
  }

  return (
    <div className="doc-upload-zone">
      <div className="doc-upload-controls">
        <select
          value={docType}
          onChange={(e) => setDocType(e.target.value)}
          className="doc-type-select"
        >
          {DOC_TYPES.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>
      </div>

      <div
        className={`doc-dropzone ${dragOver ? 'drag-over' : ''} ${uploading ? 'uploading' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={() => setDragOver(false)}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          style={{ display: 'none' }}
          accept=".pdf,.xlsx,.xls,.docx,.doc,.png,.jpg,.jpeg"
          onChange={handleFileSelect}
        />
        {uploading ? (
          <span>Đang tải lên...</span>
        ) : (
          <>
            <span style={{ fontSize: '24px' }}>📄</span>
            <span>Kéo thả file hoặc click để chọn</span>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>
              PDF, Excel, Word, ảnh (tối đa 20MB)
            </span>
          </>
        )}
      </div>

      {error && <div className="doc-upload-error">{error}</div>}
    </div>
  )
}
