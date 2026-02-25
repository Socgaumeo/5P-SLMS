// frontend/src/components/admin/RateUploadModal.jsx
/**
 * Modal for uploading Excel/CSV rate files, previewing parsed rates,
 * and confirming bulk import into vendor_rates or customer_rates.
 */

import { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function RateUploadModal({ isOpen, onClose, onImported, rateType = 'buying' }) {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [importing, setImporting] = useState(false)
  const [preview, setPreview] = useState(null)
  const [error, setError] = useState('')

  // Vendor/customer selection
  const [vendors, setVendors] = useState([])
  const [customers, setCustomers] = useState([])
  const [selectedVendorId, setSelectedVendorId] = useState('')
  const [selectedCustomerId, setSelectedCustomerId] = useState('')
  const [serviceTypeCode, setServiceTypeCode] = useState('')

  // Editable rates (user can remove rows before confirming)
  const [editableRates, setEditableRates] = useState([])

  useEffect(() => {
    if (isOpen) {
      // Fetch vendors/customers for dropdown
      if (rateType === 'buying') {
        fetch(`${API_URL}/api/vendors`).then(r => r.json()).then(d => setVendors(d.vendors || []))
      } else {
        fetch(`${API_URL}/api/customers`).then(r => r.json()).then(d => setCustomers(d.customers || []))
      }
    }
  }, [isOpen, rateType])

  const resetState = () => {
    setFile(null)
    setUploading(false)
    setImporting(false)
    setPreview(null)
    setError('')
    setEditableRates([])
    setSelectedVendorId('')
    setSelectedCustomerId('')
    setServiceTypeCode('')
  }

  const handleClose = () => {
    resetState()
    onClose()
  }

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    setError('')

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('rate_type', rateType)
      if (selectedVendorId) formData.append('vendor_id', selectedVendorId)
      if (selectedCustomerId) formData.append('customer_id', selectedCustomerId)
      if (serviceTypeCode) formData.append('service_type_code', serviceTypeCode)

      const res = await fetch(`${API_URL}/api/admin/rates/upload-file`, {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()

      if (data.error) {
        setError(data.error)
      } else if (!data.parsed_rates || data.parsed_rates.length === 0) {
        setError('Không tìm thấy dữ liệu báo giá trong file. Kiểm tra lại định dạng file.')
      } else {
        setPreview(data)
        setEditableRates(data.parsed_rates.map((r, i) => ({ ...r, _id: i, _selected: true })))
      }
    } catch (e) {
      setError('Lỗi upload: ' + e.message)
    } finally {
      setUploading(false)
    }
  }

  const handleConfirmImport = async () => {
    const selectedRates = editableRates.filter(r => r._selected)
    if (selectedRates.length === 0) {
      setError('Chưa chọn báo giá nào để import')
      return
    }

    const entityId = rateType === 'buying' ? selectedVendorId : selectedCustomerId
    if (!entityId) {
      setError(rateType === 'buying' ? 'Vui lòng chọn nhà cung cấp' : 'Vui lòng chọn khách hàng')
      return
    }

    setImporting(true)
    setError('')

    try {
      const res = await fetch(`${API_URL}/api/admin/rates/confirm-import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_ref_id: preview?.file_ref_id,
          rate_type: rateType,
          vendor_id: rateType === 'buying' ? parseInt(selectedVendorId) : null,
          customer_id: rateType === 'selling' ? parseInt(selectedCustomerId) : null,
          service_type_code: serviceTypeCode || null,
          rates: selectedRates.map(({ _id, _selected, ...r }) => r),
        }),
      })
      const data = await res.json()

      if (data.success) {
        alert(`Import thành công ${data.created_count} báo giá!`)
        handleClose()
        onImported && onImported()
      } else {
        setError(data.detail || 'Import thất bại')
      }
    } catch (e) {
      setError('Lỗi import: ' + e.message)
    } finally {
      setImporting(false)
    }
  }

  const toggleRate = (id) => {
    setEditableRates(prev => prev.map(r => r._id === id ? { ...r, _selected: !r._selected } : r))
  }

  const toggleAll = (checked) => {
    setEditableRates(prev => prev.map(r => ({ ...r, _selected: checked })))
  }

  const formatPrice = (p) => p ? new Intl.NumberFormat('vi-VN').format(p) : '0'

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" style={{ maxWidth: '900px', maxHeight: '85vh' }} onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Upload báo giá từ file ({rateType === 'buying' ? 'Chi phí NCC' : 'Doanh Thu'})</h2>
          <button className="close-btn" onClick={handleClose}>&times;</button>
        </div>

        <div className="modal-body" style={{ overflowY: 'auto', maxHeight: '65vh' }}>
          {/* Step 1: File + entity selection */}
          {!preview && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Entity selector */}
              <div className="form-group">
                <label>{rateType === 'buying' ? 'Nhà cung cấp *' : 'Khách hàng *'}</label>
                {rateType === 'buying' ? (
                  <select value={selectedVendorId} onChange={e => setSelectedVendorId(e.target.value)}>
                    <option value="">-- Chọn NCC --</option>
                    {vendors.map(v => (
                      <option key={v.vendor_id} value={v.vendor_id}>
                        {v.short_name || v.company_name} ({v.vendor_code})
                      </option>
                    ))}
                  </select>
                ) : (
                  <select value={selectedCustomerId} onChange={e => setSelectedCustomerId(e.target.value)}>
                    <option value="">-- Chọn khách hàng --</option>
                    {customers.map(c => (
                      <option key={c.customer_id} value={c.customer_id}>
                        {c.short_name || c.company_name} ({c.customer_code})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* Service type */}
              <div className="form-group">
                <label>Loại dịch vụ (tùy chọn)</label>
                <select value={serviceTypeCode} onChange={e => setServiceTypeCode(e.target.value)}>
                  <option value="">-- Tất cả --</option>
                  <option value="TRUCKING_DOM">Vận chuyển nội địa</option>
                  <option value="TRUCKING_INTL">Vận chuyển quốc tế</option>
                  <option value="CUSTOMS">Thủ tục Hải quan</option>
                  <option value="PACKING">Đóng gói</option>
                  <option value="WAREHOUSE">Kho bãi</option>
                </select>
              </div>

              {/* File picker */}
              <div className="form-group">
                <label>Chọn file Excel/CSV *</label>
                <input
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={e => setFile(e.target.files[0])}
                  style={{ padding: '8px', border: '1px dashed var(--border)', borderRadius: '8px' }}
                />
                {file && (
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    {file.name} ({(file.size / 1024).toFixed(1)} KB)
                  </span>
                )}
              </div>

              {error && (
                <div style={{ padding: '10px', background: '#FEE2E2', color: '#DC2626', borderRadius: '8px', fontSize: '13px' }}>
                  {error}
                </div>
              )}
            </div>
          )}

          {/* Step 2: Preview parsed rates */}
          {preview && (
            <div>
              <div style={{ marginBottom: '12px', padding: '10px', background: 'var(--bg-secondary)', borderRadius: '8px' }}>
                <strong>File:</strong> {preview.file_name} |
                <strong> Tìm thấy:</strong> {preview.total_rates} báo giá |
                <strong> Đã chọn:</strong> {editableRates.filter(r => r._selected).length}
                {preview.sheet_info?.map((s, i) => (
                  <span key={i} style={{ marginLeft: '8px', fontSize: '11px', color: 'var(--text-secondary)' }}>
                    [{s.sheet}: {s.count} rates, {s.type}]
                  </span>
                ))}
              </div>

              {error && (
                <div style={{ padding: '10px', background: '#FEE2E2', color: '#DC2626', borderRadius: '8px', fontSize: '13px', marginBottom: '12px' }}>
                  {error}
                </div>
              )}

              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                  <thead>
                    <tr style={{ background: 'var(--bg-secondary)', borderBottom: '2px solid var(--border)' }}>
                      <th style={{ padding: '8px 4px', textAlign: 'center', width: '40px' }}>
                        <input
                          type="checkbox"
                          checked={editableRates.every(r => r._selected)}
                          onChange={e => toggleAll(e.target.checked)}
                        />
                      </th>
                      <th style={{ padding: '8px', textAlign: 'left' }}>Điểm đi</th>
                      <th style={{ padding: '8px', textAlign: 'left' }}>Điểm đến</th>
                      <th style={{ padding: '8px', textAlign: 'left' }}>Loại xe</th>
                      <th style={{ padding: '8px', textAlign: 'right' }}>Giá (VND)</th>
                      <th style={{ padding: '8px', textAlign: 'center' }}>ĐVT</th>
                      <th style={{ padding: '8px', textAlign: 'left' }}>Ghi chú</th>
                    </tr>
                  </thead>
                  <tbody>
                    {editableRates.map(rate => (
                      <tr
                        key={rate._id}
                        style={{
                          borderBottom: '1px solid var(--border)',
                          opacity: rate._selected ? 1 : 0.4,
                          background: rate._selected ? 'transparent' : 'var(--bg-secondary)',
                        }}
                      >
                        <td style={{ padding: '6px 4px', textAlign: 'center' }}>
                          <input type="checkbox" checked={rate._selected} onChange={() => toggleRate(rate._id)} />
                        </td>
                        <td style={{ padding: '6px 8px' }}>{rate.origin || '-'}</td>
                        <td style={{ padding: '6px 8px' }}>{rate.destination || '-'}</td>
                        <td style={{ padding: '6px 8px' }}>{rate.vehicle_type || '-'}</td>
                        <td style={{ padding: '6px 8px', textAlign: 'right', fontWeight: 'bold' }}>
                          {formatPrice(rate.price)}
                        </td>
                        <td style={{ padding: '6px 8px', textAlign: 'center' }}>{rate.unit || 'TRIP'}</td>
                        <td style={{ padding: '6px 8px', fontSize: '11px', color: 'var(--text-secondary)' }}>
                          {rate.notes || ''}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer" style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
          {preview && (
            <button
              className="btn-secondary"
              onClick={() => { setPreview(null); setEditableRates([]); setError(''); }}
            >
              Chọn file khác
            </button>
          )}
          <button className="btn-secondary" onClick={handleClose}>Đóng</button>

          {!preview ? (
            <button
              className="btn-primary"
              disabled={!file || uploading}
              onClick={handleUpload}
            >
              {uploading ? 'Đang phân tích...' : 'Upload & Phân tích'}
            </button>
          ) : (
            <button
              className="btn-primary"
              disabled={importing || editableRates.filter(r => r._selected).length === 0}
              onClick={handleConfirmImport}
            >
              {importing ? 'Đang import...' : `Import ${editableRates.filter(r => r._selected).length} báo giá`}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
