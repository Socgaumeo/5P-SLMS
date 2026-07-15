import React, { useState, useEffect } from 'react'
import { authFetch, API_URL } from '../../utils/auth-fetch'
import { useAuth } from '../../contexts/AuthContext'

const vnd = (n) => (Number(n || 0)).toLocaleString('vi-VN') + 'đ'
const STATUS_LABEL = { unpaid: '⏳ Chưa TT', partial: '🟡 Một phần', paid: '✅ Đã TT' }
const AR_STATE = {
  CHUA_XUAT_HD: { t: 'Chưa xuất HĐ', c: '#94A3B8' },
  DA_XUAT_CHO_THU: { t: 'Chờ thu', c: '#F59E0B' },
  THU_MOT_PHAN: { t: 'Thu một phần', c: '#EAB308' },
  DA_THU: { t: 'Đã thu', c: '#22C55E' },
}

export default function CongNoPage() {
  const [tab, setTab] = useState('ap') // ap = phải trả (pain điểm CS), ar = phải thu

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 20, alignItems: 'center' }}>
        <TabBtn active={tab === 'ap'} onClick={() => setTab('ap')}>💸 Phải trả (Vendor/NCC)</TabBtn>
        <TabBtn active={tab === 'ar'} onClick={() => setTab('ar')}>💰 Phải thu (Khách hàng)</TabBtn>
      </div>
      {tab === 'ap' ? <APPanel /> : <ARPanel />}
    </div>
  )
}

// Modal chọn người nhận + GỬI ngay (dùng cho cả bảng kê đã lập lẫn chi phí chưa lập)
function SendNotifyModal({ onClose, costIds, billId, label }) {
  const { user } = useAuth()
  const [users, setUsers] = useState([])
  const [tgIds, setTgIds] = useState([])
  const [emails, setEmails] = useState([])
  const [newEmail, setNewEmail] = useState('')
  const [note, setNote] = useState('')
  const [sending, setSending] = useState(false)

  useEffect(() => {
    authFetch(`${API_URL}/api/ap/users`).then(r => r.json()).then(d => setUsers(d.users || []))
  }, [])

  const toggleUser = (uid) => setTgIds(p => p.includes(uid) ? p.filter(x => x !== uid) : [...p, uid])
  const addEmail = () => {
    const e = newEmail.trim()
    if (e && /.+@.+\..+/.test(e) && !emails.includes(e)) { setEmails([...emails, e]); setNewEmail('') }
  }
  const rmEmail = (e) => setEmails(emails.filter(x => x !== e))

  const send = () => {
    if (!tgIds.length && !emails.length) return alert('Chọn ít nhất 1 người nhận (Telegram hoặc Email)')
    setSending(true)
    const body = { telegram_user_ids: tgIds, emails, note, requested_by: user?.user_id }
    if (billId) body.bill_id = billId; else body.cost_ids = costIds
    authFetch(`${API_URL}/api/ap/notify`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(r => r.json()).then(d => {
      setSending(false)
      if (d.detail) return alert('Lỗi: ' + d.detail)
      const ch = []
      if (d.sent?.telegram) ch.push(`Telegram (${d.sent.telegram} người)`)
      if (d.sent?.email) ch.push(`Email (${d.sent.email} người)`)
      let msg = ch.length ? `✅ Đã gửi ${ch.join(' + ')}\n${d.count} khoản — ${vnd(d.total)}` : '⚠️ Chưa gửi được'
      if (!d.smtp_configured && emails.length) msg += '\n(Server chưa cấu hình SMTP nên email chưa gửi)'
      alert(msg); onClose()
    }).catch(() => { setSending(false); alert('Lỗi kết nối') })
  }

  return (
    <div style={modalOverlay} onClick={onClose}>
      <div style={{ ...modalBox, maxWidth: 520 }} onClick={e => e.stopPropagation()}>
        <h3>📨 Gửi kế toán duyệt chi</h3>
        {label && <p style={{ color: '#64748B', fontSize: 13, margin: '4px 0 0' }}>{label}</p>}

        <label style={{ display: 'block', margin: '14px 0 6px', fontSize: 13, fontWeight: 600 }}>📲 Người nhận Telegram</label>
        <div style={{ maxHeight: 180, overflow: 'auto', border: '1px solid #E2E8F0', borderRadius: 6, padding: 8 }}>
          {users.map(u => (
            <label key={u.user_id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '3px 0', fontSize: 13, cursor: 'pointer' }}>
              <input type="checkbox" checked={tgIds.includes(u.user_id)} onChange={() => toggleUser(u.user_id)} />
              <span>{u.full_name}</span>
              <span style={{ color: '#94A3B8', fontSize: 11 }}>
                {u.telegram_id ? `TG:${u.telegram_id}` : '⚠️ chưa có TG'} {u.email ? `· ${u.email}` : ''}
              </span>
            </label>
          ))}
          {!users.length && <span style={{ color: '#94A3B8', fontSize: 12 }}>Đang tải...</span>}
        </div>
        <p style={{ color: '#94A3B8', fontSize: 11, margin: '4px 0 0' }}>User được chọn nhận cả Telegram + email (nếu DB có email). TG cần đã Start bot 1 lần.</p>

        <label style={{ display: 'block', margin: '14px 0 6px', fontSize: 13, fontWeight: 600 }}>📧 Email nhận thêm</label>
        <div style={{ display: 'flex', gap: 6 }}>
          <input value={newEmail} onChange={e => setNewEmail(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && addEmail()}
            placeholder="ketoan@example.com" style={inputStyle} />
          <button style={miniBtn} onClick={addEmail}>+ Thêm</button>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
          {emails.map(e => (
            <span key={e} style={{ background: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: 12, padding: '2px 10px', fontSize: 12 }}>
              {e} <span onClick={() => rmEmail(e)} style={{ cursor: 'pointer', color: '#DC2626', marginLeft: 4 }}>✕</span>
            </span>
          ))}
        </div>

        <label style={{ display: 'block', margin: '14px 0 6px', fontSize: 13, fontWeight: 600 }}>Ghi chú (tùy chọn)</label>
        <input value={note} onChange={e => setNote(e.target.value)} placeholder="VD: Ưu tiên trả trước 20/7" style={inputStyle} />

        <div style={{ marginTop: 20, display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <button style={miniBtn} onClick={onClose}>Hủy</button>
          <button style={{ ...primaryBtn, background: '#059669', opacity: sending ? 0.6 : 1 }} disabled={sending} onClick={send}>
            {sending ? 'Đang gửi...' : '📨 Gửi ngay'}
          </button>
        </div>
      </div>
    </div>
  )
}

function TabBtn({ active, onClick, children }) {
  return (
    <button onClick={onClick} style={{
      padding: '10px 18px', border: 'none', borderRadius: 8, cursor: 'pointer',
      fontWeight: 600, fontSize: 14,
      background: active ? '#2563EB' : '#F1F5F9', color: active ? '#fff' : '#334155',
    }}>{children}</button>
  )
}

// ============ AP — PHẢI TRẢ ============
function APPanel() {
  const [vendors, setVendors] = useState([])
  const [bills, setBills] = useState([])
  const [sel, setSel] = useState(null) // vendor được chọn xem chi tiết
  const [costs, setCosts] = useState([])
  const [loading, setLoading] = useState(false)
  const [checked, setChecked] = useState({}) // cost_id → bool (tick chọn thanh toán)
  const [sendModal, setSendModal] = useState(null) // {costIds?, billId?, label}

  const loadSummary = () => {
    authFetch(`${API_URL}/api/ap/unbilled`).then(r => r.json()).then(d => setVendors(d.vendors || []))
    authFetch(`${API_URL}/api/ap/bills`).then(r => r.json()).then(d => setBills(d.bills || []))
  }
  useEffect(loadSummary, [])

  const openVendor = (v) => {
    setSel(v); setLoading(true); setChecked({})
    authFetch(`${API_URL}/api/ap/unbilled?vendor_id=${v.vendor_id}`).then(r => r.json())
      .then(d => { setCosts(d.costs || []); setChecked(Object.fromEntries((d.costs || []).map(c => [c.cost_id, true]))); setLoading(false) })
  }

  const selectedIds = () => costs.filter(c => checked[c.cost_id]).map(c => c.cost_id)
  const selectedTotal = () => costs.filter(c => checked[c.cost_id]).reduce((s, c) => s + Number(c.amount || 0), 0)
  const toggle = (id) => setChecked(p => ({ ...p, [id]: !p[id] }))
  const toggleAll = () => {
    const all = costs.every(c => checked[c.cost_id])
    setChecked(Object.fromEntries(costs.map(c => [c.cost_id, !all])))
  }

  const exportExcel = () => {
    const ids = selectedIds()
    if (!ids.length) return alert('Chưa chọn dòng nào')
    authFetch(`${API_URL}/api/ap/export`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cost_ids: ids, title: `BẢNG KÊ CHI PHÍ — ${sel.vendor_name}` }),
    }).then(r => r.blob()).then(b => {
      const url = URL.createObjectURL(b); const a = document.createElement('a')
      a.href = url; a.download = `bangke_${sel.vendor_name}.xlsx`; a.click(); URL.revokeObjectURL(url)
    })
  }

  const notifyKT = () => {
    const ids = selectedIds()
    if (!ids.length) return alert('Chưa chọn dòng nào')
    setSendModal({ costIds: ids, label: `${sel.vendor_name} — ${ids.length} khoản, ${vnd(selectedTotal())}` })
  }
  const notifyBill = (bill) => {
    setSendModal({ billId: bill.bill_id, label: `Bảng kê ${bill.bill_no || '#' + bill.bill_id} — ${vnd(bill.total_amount)}` })
  }

  const createBillSelected = () => {
    const ids = selectedIds()
    if (!ids.length) return alert('Chưa chọn dòng nào')
    if (!confirm(`Lập bảng kê ${ids.length} khoản (${vnd(selectedTotal())}) cho ${sel.vendor_name}?`)) return
    authFetch(`${API_URL}/api/ap/bills`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ vendor_id: sel.vendor_id, cost_ids: ids }),
    }).then(r => r.json()).then(() => { setSel(null); setCosts([]); loadSummary() })
  }

  const markPaid = (bill) => {
    if (!confirm(`Đánh dấu đã trả ${vnd(bill.total_amount)} cho bảng kê ${bill.bill_no || bill.bill_id}?`)) return
    authFetch(`${API_URL}/api/ap/bills/${bill.bill_id}/payment`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ paid_amount: bill.total_amount }),
    }).then(() => loadSummary())
  }

  const editStatus = (bill) => {
    const s = prompt(`Sửa tình trạng bảng kê ${bill.bill_no || bill.bill_id}:\nunpaid = chưa TT | partial = một phần | paid = đã TT`, bill.payment_status)
    if (!s || !['unpaid', 'partial', 'paid'].includes(s)) return
    const body = { payment_status: s }
    if (s === 'paid') body.paid_amount = bill.total_amount
    if (s === 'unpaid') body.paid_amount = 0
    authFetch(`${API_URL}/api/ap/bills/${bill.bill_id}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(() => loadSummary())
  }

  const delBill = (bill) => {
    if (!confirm(`XÓA bảng kê ${bill.bill_no || bill.bill_id}? Chi phí sẽ quay lại danh sách "chờ thanh toán".`)) return
    authFetch(`${API_URL}/api/ap/bills/${bill.bill_id}`, { method: 'DELETE' }).then(() => loadSummary())
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
      <Card title="Chi phí CHỜ thanh toán (theo Vendor)">
        <table style={tableStyle}>
          <thead><tr><Th>Vendor</Th><Th>Số khoản</Th><Th right>Tổng</Th><Th></Th></tr></thead>
          <tbody>
            {vendors.map(v => (
              <tr key={v.vendor_id}>
                <Td>{v.vendor_name || `#${v.vendor_id}`}</Td>
                <Td>{v.count}</Td>
                <Td right>{vnd(v.total)}</Td>
                <Td><button style={miniBtn} onClick={() => openVendor(v)}>Xem</button></Td>
              </tr>
            ))}
            {!vendors.length && <tr><Td colSpan={4} style={{ color: '#94A3B8' }}>Không có chi phí chờ</Td></tr>}
          </tbody>
        </table>
      </Card>

      <Card title="Bảng kê đã lập">
        <table style={tableStyle}>
          <thead><tr><Th>Bảng kê</Th><Th right>Tổng</Th><Th>TT</Th><Th>Thao tác</Th></tr></thead>
          <tbody>
            {bills.map(b => (
              <tr key={b.bill_id}>
                <Td>{b.bill_no || `#${b.bill_id}`}</Td>
                <Td right>{vnd(b.total_amount)}</Td>
                <Td>{STATUS_LABEL[b.payment_status]}</Td>
                <Td>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button style={{ ...miniBtn, background: '#DCFCE7' }} onClick={() => notifyBill(b)}>📨 Gửi KT</button>
                    {b.payment_status !== 'paid' && <button style={miniBtn} onClick={() => markPaid(b)}>Đã trả</button>}
                    <button style={miniBtn} onClick={() => editStatus(b)}>✏️</button>
                    <button style={{ ...miniBtn, color: '#DC2626' }} onClick={() => delBill(b)}>🗑️</button>
                  </div>
                </Td>
              </tr>
            ))}
            {!bills.length && <tr><Td colSpan={4} style={{ color: '#94A3B8' }}>Chưa có bảng kê</Td></tr>}
          </tbody>
        </table>
      </Card>

      {sel && (
        <div style={modalOverlay} onClick={() => setSel(null)}>
          <div style={{ ...modalBox, maxWidth: 1100 }} onClick={e => e.stopPropagation()}>
            <h3>Chi tiết chi phí — {sel.vendor_name}</h3>
            <p style={{ color: '#64748B', fontSize: 12, margin: '4px 0 12px' }}>Thông tin đối chiếu: biển số xe, tuyến, INV, số tờ khai, B/L, số HĐ</p>
            {loading ? <p>Đang tải...</p> : (
              <div style={{ overflowX: 'auto' }}>
              <table style={tableStyle}>
                <thead><tr>
                  <Th><input type="checkbox" checked={costs.length > 0 && costs.every(c => checked[c.cost_id])} onChange={toggleAll} /></Th>
                  <Th>Job</Th><Th>Ngày</Th><Th>Tên phí</Th>
                  <Th>Biển số</Th><Th>Tuyến</Th><Th>Số TK</Th><Th>B/L-AWB</Th><Th>Số HĐ</Th>
                  <Th right>Tiền</Th>
                </tr></thead>
                <tbody>
                  {costs.map(c => (
                    <tr key={c.cost_id} style={{ background: checked[c.cost_id] ? '#EFF6FF' : 'transparent' }}>
                      <Td><input type="checkbox" checked={!!checked[c.cost_id]} onChange={() => toggle(c.cost_id)} /></Td>
                      <Td>{c.job_no}</Td><Td>{c.cost_date}</Td>
                      <Td>{c.cost_name}{c.is_reimbursement ? ' (chi hộ)' : ''}</Td>
                      <Td>{c.plate_number || '—'}</Td>
                      <Td>{c.route || [c.origin_address, c.dest_address].filter(Boolean).join(' → ') || '—'}</Td>
                      <Td>{c.declaration_no || '—'}</Td>
                      <Td>{c.bl_awb_no || '—'}</Td>
                      <Td>{c.job_invoice_no || '—'}</Td>
                      <Td right>{vnd(c.amount)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
              </div>
            )}
            <div style={{ marginTop: 16, display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
              <span style={{ fontWeight: 600 }}>Đã chọn: {selectedIds().length} khoản — {vnd(selectedTotal())}</span>
              <div style={{ flex: 1 }} />
              <button style={miniBtn} onClick={() => setSel(null)}>Đóng</button>
              <button style={miniBtn} onClick={exportExcel}>📥 Xuất Excel</button>
              <button style={{ ...primaryBtn, background: '#059669' }} onClick={notifyKT}>📨 Gửi KT duyệt chi</button>
              <button style={primaryBtn} onClick={createBillSelected}>📋 Lập bảng kê + track trả</button>
            </div>
          </div>
        </div>
      )}

      {sendModal && <SendNotifyModal {...sendModal} onClose={() => setSendModal(null)} />}
    </div>
  )
}

// ============ AR — PHẢI THU ============
function ARPanel() {
  const [customers, setCustomers] = useState([])
  const [invoices, setInvoices] = useState([])
  const [sel, setSel] = useState(null)      // khách hàng đang xem chi tiết
  const [jobs, setJobs] = useState([])       // job của khách đang xem
  const [loading, setLoading] = useState(false)
  const [checked, setChecked] = useState({})
  const [sortBy, setSortBy] = useState('eta')
  const [sortDir, setSortDir] = useState('asc')

  const load = () => {
    authFetch(`${API_URL}/api/ar/by-customer`).then(r => r.json()).then(d => setCustomers(d.customers || []))
    authFetch(`${API_URL}/api/ar/invoices`).then(r => r.json()).then(d => setInvoices(d.invoices || []))
  }
  useEffect(load, [])

  const openCustomer = (c) => {
    setSel(c); setLoading(true); setChecked({})
    authFetch(`${API_URL}/api/ar/job-status?state=CHUA_XUAT_HD&customer_id=${c.customer_id}`).then(r => r.json())
      .then(d => {
        const js = d.jobs || []
        setJobs(js); setChecked(Object.fromEntries(js.map(j => [j.job_id, true]))); setLoading(false)
      })
  }

  const sortJobs = (list) => {
    const dir = sortDir === 'asc' ? 1 : -1
    return [...list].sort((a, b) => {
      let x = a[sortBy], y = b[sortBy]
      if (sortBy === 'total_revenue') { x = Number(x || 0); y = Number(y || 0) }
      else { x = String(x || ''); y = String(y || '') }
      return x < y ? -dir : x > y ? dir : 0
    })
  }
  const clickSort = (col) => {
    if (sortBy === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortBy(col); setSortDir('asc') }
  }
  const sortIcon = (col) => sortBy === col ? (sortDir === 'asc' ? ' ▲' : ' ▼') : ''

  const selJobIds = () => jobs.filter(j => checked[j.job_id]).map(j => j.job_id)
  const selTotal = () => jobs.filter(j => checked[j.job_id]).reduce((s, j) => s + Number(j.total_revenue || 0), 0)
  const toggle = (id) => setChecked(p => ({ ...p, [id]: !p[id] }))
  const toggleAll = () => {
    const all = jobs.every(j => checked[j.job_id])
    setChecked(Object.fromEntries(jobs.map(j => [j.job_id, !all])))
  }

  const createInvoice = () => {
    const ids = selJobIds()
    if (!ids.length) return alert('Chưa chọn job nào')
    if (!confirm(`Xuất HĐ gộp ${ids.length} job (${vnd(selTotal())}) cho ${sel.customer_name}?`)) return
    authFetch(`${API_URL}/api/ar/invoices`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ customer_id: sel.customer_id, job_ids: ids }),
    }).then(r => r.json()).then(() => { setSel(null); setJobs([]); load() })
  }

  const markPaid = (inv) => {
    if (!confirm(`Đánh dấu đã thu ${vnd(inv.total)} cho HĐ ${inv.invoice_no || inv.invoice_id}?`)) return
    authFetch(`${API_URL}/api/ar/invoices/${inv.invoice_id}/payment`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ paid_amount: inv.total }),
    }).then(() => load())
  }

  const editStatus = (inv) => {
    const s = prompt(`Sửa tình trạng HĐ ${inv.invoice_no || inv.invoice_id}:\nunpaid = chưa thu | partial = một phần | paid = đã thu`, inv.payment_status)
    if (!s || !['unpaid', 'partial', 'paid'].includes(s)) return
    const body = { payment_status: s }
    if (s === 'paid') body.paid_amount = inv.total
    if (s === 'unpaid') body.paid_amount = 0
    authFetch(`${API_URL}/api/ar/invoices/${inv.invoice_id}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(() => load())
  }

  const delInv = (inv) => {
    if (!confirm(`XÓA HĐ ${inv.invoice_no || inv.invoice_id}? Job sẽ quay lại "chưa xuất HĐ".`)) return
    authFetch(`${API_URL}/api/ar/invoices/${inv.invoice_id}`, { method: 'DELETE' }).then(() => load())
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: 20 }}>
      <Card title="Phải thu theo khách hàng (job chưa xuất HĐ)">
        <table style={tableStyle}>
          <thead><tr><Th>Khách hàng</Th><Th right>Số job</Th><Th right>Doanh thu</Th><Th></Th></tr></thead>
          <tbody>
            {customers.map(c => (
              <tr key={c.customer_id}>
                <Td>{c.customer_name}</Td>
                <Td right>{c.job_count}</Td>
                <Td right>{vnd(c.total)}</Td>
                <Td><button style={miniBtn} onClick={() => openCustomer(c)}>👁️ Xem</button></Td>
              </tr>
            ))}
            {!customers.length && <tr><Td colSpan={4} style={{ color: '#94A3B8' }}>Không có công nợ phải thu</Td></tr>}
          </tbody>
        </table>
      </Card>

      <Card title="Hóa đơn đã xuất">
        <table style={tableStyle}>
          <thead><tr><Th>HĐ</Th><Th right>Tổng</Th><Th>TT</Th><Th></Th></tr></thead>
          <tbody>
            {invoices.map(inv => (
              <tr key={inv.invoice_id}>
                <Td>{inv.invoice_no || `#${inv.invoice_id}`}</Td>
                <Td right>{vnd(inv.total)}</Td>
                <Td>{STATUS_LABEL[inv.payment_status]}</Td>
                <Td>
                  <div style={{ display: 'flex', gap: 4 }}>
                    {inv.payment_status !== 'paid' && <button style={miniBtn} onClick={() => markPaid(inv)}>Đã thu</button>}
                    <button style={miniBtn} onClick={() => editStatus(inv)}>✏️</button>
                    <button style={{ ...miniBtn, color: '#DC2626' }} onClick={() => delInv(inv)}>🗑️</button>
                  </div>
                </Td>
              </tr>
            ))}
            {!invoices.length && <tr><Td colSpan={4} style={{ color: '#94A3B8' }}>Chưa có hóa đơn. Tạo HĐ từ danh sách job.</Td></tr>}
          </tbody>
        </table>
      </Card>

      {sel && (
        <div style={modalOverlay} onClick={() => setSel(null)}>
          <div style={{ ...modalBox, maxWidth: 900 }} onClick={e => e.stopPropagation()}>
            <h3>Chi tiết phải thu — {sel.customer_name}</h3>
            <p style={{ color: '#64748B', fontSize: 12, margin: '4px 0 12px' }}>Click tiêu đề cột để sắp xếp (loại DV / ngày / doanh thu)</p>
            {loading ? <p>Đang tải...</p> : (
              <div style={{ overflowX: 'auto' }}>
              <table style={tableStyle}>
                <thead><tr>
                  <Th><input type="checkbox" checked={jobs.length > 0 && jobs.every(j => checked[j.job_id])} onChange={toggleAll} /></Th>
                  <Th><span style={sortHdr} onClick={() => clickSort('job_no')}>Job{sortIcon('job_no')}</span></Th>
                  <Th><span style={sortHdr} onClick={() => clickSort('service_type_code')}>Loại DV{sortIcon('service_type_code')}</span></Th>
                  <Th><span style={sortHdr} onClick={() => clickSort('eta')}>ETA{sortIcon('eta')}</span></Th>
                  <Th right><span style={sortHdr} onClick={() => clickSort('total_revenue')}>Doanh thu{sortIcon('total_revenue')}</span></Th>
                </tr></thead>
                <tbody>
                  {sortJobs(jobs).map(j => (
                    <tr key={j.job_id} style={{ background: checked[j.job_id] ? '#EFF6FF' : 'transparent' }}>
                      <Td><input type="checkbox" checked={!!checked[j.job_id]} onChange={() => toggle(j.job_id)} /></Td>
                      <Td>{j.job_no}</Td>
                      <Td>{j.service_type_code || '—'}</Td>
                      <Td>{j.eta || j.etd || '—'}</Td>
                      <Td right>{vnd(j.total_revenue)}</Td>
                    </tr>
                  ))}
                </tbody>
              </table>
              </div>
            )}
            <div style={{ marginTop: 16, display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
              <span style={{ fontWeight: 600 }}>Đã chọn: {selJobIds().length} job — {vnd(selTotal())}</span>
              <div style={{ flex: 1 }} />
              <button style={miniBtn} onClick={() => setSel(null)}>Đóng</button>
              <button style={primaryBtn} onClick={createInvoice}>🧾 Xuất HĐ gộp + track thu</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
const sortHdr = { cursor: 'pointer', userSelect: 'none' }

// ============ shared UI ============
const tableStyle = { width: '100%', borderCollapse: 'collapse', fontSize: 13 }
const miniBtn = { padding: '4px 10px', border: '1px solid #CBD5E1', borderRadius: 6, background: '#F1F5F9', cursor: 'pointer', fontSize: 12 }
const primaryBtn = { padding: '8px 16px', border: 'none', borderRadius: 6, background: '#2563EB', color: '#fff', cursor: 'pointer', fontWeight: 600 }
const modalOverlay = { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }
const modalBox = { background: '#fff', borderRadius: 12, padding: 24, maxWidth: 700, maxHeight: '80vh', overflow: 'auto', width: '90%' }
const inputStyle = { width: '100%', padding: '8px 10px', border: '1px solid #CBD5E1', borderRadius: 6, fontSize: 14, boxSizing: 'border-box' }

function Card({ title, children }) {
  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: 18, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
      <h3 style={{ margin: '0 0 14px', fontSize: 15 }}>{title}</h3>
      {children}
    </div>
  )
}
const Th = ({ children, right }) => <th style={{ textAlign: right ? 'right' : 'left', padding: '6px 8px', borderBottom: '2px solid #E2E8F0', color: '#64748B', fontSize: 12 }}>{children}</th>
const Td = ({ children, right, colSpan, style }) => <td colSpan={colSpan} style={{ textAlign: right ? 'right' : 'left', padding: '6px 8px', borderBottom: '1px solid #F1F5F9', ...style }}>{children}</td>
