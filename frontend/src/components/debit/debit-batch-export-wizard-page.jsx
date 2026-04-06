// frontend/src/components/debit/debit-batch-export-wizard-page.jsx
/**
 * Batch debit note export wizard page.
 * Steps: select month → customer → template → preview jobs → generate ZIP.
 * Accessible via NavItem "Xuất Debit" in sidebar.
 */

import { useState, useEffect } from 'react'
import { authFetch, API_URL } from '../../utils/auth-fetch'

export default function DebitBatchExportWizardPage() {
  // Wizard state
  const [month, setMonth] = useState(() => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  })
  const [customerId, setCustomerId] = useState('')
  const [templateId, setTemplateId] = useState('')

  // Data
  const [customers, setCustomers] = useState([])
  const [templates, setTemplates] = useState([])
  const [previewJobs, setPreviewJobs] = useState([])
  const [loadingJobs, setLoadingJobs] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')

  // Fetch customers on mount
  useEffect(() => {
    authFetch(`${API_URL}/api/customers`)
      .then((r) => r.json())
      .then((d) => setCustomers(Array.isArray(d) ? d : d.data || []))
      .catch(() => {})
  }, [])

  // Fetch templates when customer changes
  useEffect(() => {
    if (!customerId) { setTemplates([]); setTemplateId(''); return }
    authFetch(`${API_URL}/api/debit/templates?customer_id=${customerId}`)
      .then((r) => r.json())
      .then((d) => {
        const list = d.data || []
        setTemplates(list)
        if (list.length === 1) setTemplateId(list[0].id)
        else setTemplateId('')
      })
      .catch(() => setTemplates([]))
  }, [customerId])

  // Fetch preview jobs when month + customer selected
  useEffect(() => {
    if (!customerId || !month) { setPreviewJobs([]); return }
    setLoadingJobs(true)
    const params = new URLSearchParams({ customer_id: customerId, month, limit: '100' })
    authFetch(`${API_URL}/api/jobs/recent?${params}`)
      .then((r) => r.json())
      .then((d) => setPreviewJobs(d.jobs || d.data || []))
      .catch(() => setPreviewJobs([]))
      .finally(() => setLoadingJobs(false))
  }, [customerId, month])

  const handleGenerate = async () => {
    if (!templateId || !customerId || !month) return
    setGenerating(true)
    setError('')

    try {
      const res = await authFetch(`${API_URL}/api/debit/batch-generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ template_id: templateId, customer_id: parseInt(customerId), month }),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Generation failed')
      }

      // Download ZIP
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `debit_${month}.zip`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err.message)
    } finally {
      setGenerating(false)
    }
  }

  const selectedCustomer = customers.find((c) => String(c.customer_id) === String(customerId))

  return (
    <div className="debit-export-page">
      <h2 style={{ marginBottom: '20px' }}>Xuất Debit Notes</h2>

      {/* Step 1 + 2: Month + Customer */}
      <div className="debit-wizard-row">
        <div className="debit-wizard-step">
          <label className="debit-step-label">1. Chọn tháng</label>
          <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} className="doc-filter-input" />
        </div>

        <div className="debit-wizard-step">
          <label className="debit-step-label">2. Chọn khách hàng</label>
          <select value={customerId} onChange={(e) => setCustomerId(e.target.value)} className="doc-filter-select">
            <option value="">-- Chọn khách hàng --</option>
            {customers.map((c) => (
              <option key={c.customer_id} value={c.customer_id}>
                {c.short_name || c.company_name}
              </option>
            ))}
          </select>
        </div>

        <div className="debit-wizard-step">
          <label className="debit-step-label">3. Chọn template</label>
          <select value={templateId} onChange={(e) => setTemplateId(e.target.value)} className="doc-filter-select" disabled={templates.length === 0}>
            <option value="">{templates.length === 0 ? 'Chưa có template' : '-- Chọn template --'}</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>{t.template_name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Step 4: Preview Jobs */}
      {customerId && month && (
        <div style={{ marginTop: '20px' }}>
          <h3 style={{ marginBottom: '10px' }}>
            Jobs của {selectedCustomer?.short_name || selectedCustomer?.company_name || '...'} tháng {month}
          </h3>

          {loadingJobs ? (
            <div className="loading-state">Đang tải...</div>
          ) : previewJobs.length === 0 ? (
            <div className="empty-state">Không có job nào trong tháng này</div>
          ) : (
            <table className="admin-table">
              <thead>
                <tr>
                  <th>STT</th>
                  <th>Job No</th>
                  <th>Ngày tạo</th>
                  <th>Trạng thái</th>
                  <th>Doanh thu</th>
                </tr>
              </thead>
              <tbody>
                {previewJobs.map((j, idx) => (
                  <tr key={j.job_id}>
                    <td>{idx + 1}</td>
                    <td><code>{j.job_no}</code></td>
                    <td>{j.created_at ? new Date(j.created_at).toLocaleDateString('vi-VN') : '-'}</td>
                    <td>{j.status_code}</td>
                    <td>{j.total_revenue ? new Intl.NumberFormat('vi-VN').format(j.total_revenue) : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Step 5: Generate Button */}
      {error && <div className="doc-upload-error" style={{ marginTop: '12px' }}>{error}</div>}

      <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
        <button
          className="btn-primary"
          onClick={handleGenerate}
          disabled={!templateId || !customerId || !month || previewJobs.length === 0 || generating}
          style={{ padding: '10px 24px', fontSize: '15px' }}
        >
          {generating ? '⏳ Đang tạo...' : `📝 Xuất Debit Notes (${previewJobs.length} jobs)`}
        </button>
      </div>
    </div>
  )
}
