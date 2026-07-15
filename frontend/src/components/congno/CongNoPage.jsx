import React, { useState, useEffect } from 'react'
import { authFetch, API_URL } from '../../utils/auth-fetch'

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
  const [showCfg, setShowCfg] = useState(false)

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 20, alignItems: 'center' }}>
        <TabBtn active={tab === 'ap'} onClick={() => setTab('ap')}>💸 Phải trả (Vendor/NCC)</TabBtn>
        <TabBtn active={tab === 'ar'} onClick={() => setTab('ar')}>💰 Phải thu (Khách hàng)</TabBtn>
        <div style={{ flex: 1 }} />
        <button style={miniBtn} onClick={() => setShowCfg(true)}>⚙️ Cấu hình kế toán</button>
      </div>
      {tab === 'ap' ? <APPanel /> : <ARPanel />}
      {showCfg && <NotifyConfigModal onClose={() => setShowCfg(false)} />}
    </div>
  )
}

function NotifyConfigModal({ onClose }) {
  const [tg, setTg] = useState('')
  const [email, setEmail] = useState('')
  useEffect(() => {
    authFetch(`${API_URL}/api/ap/notify-config`).then(r => r.json()).then(d => {
      if (d.config) { setTg(d.config.telegram_id || ''); setEmail(d.config.email || '') }
    })
  }, [])
  const save = () => {
    authFetch(`${API_URL}/api/ap/notify-config`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ telegram_id: tg, email }),
    }).then(() => { alert('Đã lưu cấu hình kế toán'); onClose() })
  }
  return (
    <div style={modalOverlay} onClick={onClose}>
      <div style={{ ...modalBox, maxWidth: 440 }} onClick={e => e.stopPropagation()}>
        <h3>Cấu hình nhận thông báo — Kế toán</h3>
        <label style={{ display: 'block', margin: '12px 0 4px', fontSize: 13 }}>Telegram ID</label>
        <input value={tg} onChange={e => setTg(e.target.value)} placeholder="VD: 348988385" style={inputStyle} />
        <label style={{ display: 'block', margin: '12px 0 4px', fontSize: 13 }}>Email</label>
        <input value={email} onChange={e => setEmail(e.target.value)} placeholder="ketoan@5pvietnam.com" style={inputStyle} />
        <div style={{ marginTop: 16, display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <button style={miniBtn} onClick={onClose}>Hủy</button>
          <button style={primaryBtn} onClick={save}>Lưu</button>
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
    const note = prompt('Ghi chú gửi kế toán (tùy chọn):', '')
    if (note === null) return
    authFetch(`${API_URL}/api/ap/notify`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cost_ids: ids, note }),
    }).then(r => r.json()).then(d => {
      if (d.detail) return alert('Lỗi: ' + d.detail)
      const ch = []; if (d.sent?.telegram) ch.push('Telegram'); if (d.sent?.email) ch.push('Email')
      alert(ch.length ? `Đã gửi KT qua ${ch.join(' + ')} (${d.count} khoản, ${vnd(d.total)})` : 'Chưa gửi được — kiểm tra cấu hình KT')
    })
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
    </div>
  )
}

// ============ AR — PHẢI THU ============
function ARPanel() {
  const [jobs, setJobs] = useState([])
  const [invoices, setInvoices] = useState([])
  const [filter, setFilter] = useState('')

  const load = () => {
    authFetch(`${API_URL}/api/ar/job-status`).then(r => r.json()).then(d => setJobs(d.jobs || []))
    authFetch(`${API_URL}/api/ar/invoices`).then(r => r.json()).then(d => setInvoices(d.invoices || []))
  }
  useEffect(load, [])

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

  const shown = filter ? jobs.filter(j => j.ar_state === filter) : jobs

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: 20 }}>
      <Card title="Trạng thái thu tiền theo Job">
        <div style={{ marginBottom: 10, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {['', 'CHUA_XUAT_HD', 'DA_XUAT_CHO_THU', 'DA_THU'].map(s => (
            <button key={s} onClick={() => setFilter(s)} style={{
              ...miniBtn, background: filter === s ? '#2563EB' : '#F1F5F9', color: filter === s ? '#fff' : '#334155',
            }}>{s ? AR_STATE[s]?.t : 'Tất cả'}</button>
          ))}
        </div>
        <table style={tableStyle}>
          <thead><tr><Th>Job</Th><Th right>Doanh thu</Th><Th>Trạng thái</Th></tr></thead>
          <tbody>
            {shown.slice(0, 100).map(j => (
              <tr key={j.job_id}>
                <Td>{j.job_no}</Td>
                <Td right>{vnd(j.total_revenue)}</Td>
                <Td><span style={{ color: AR_STATE[j.ar_state]?.c, fontWeight: 600 }}>{AR_STATE[j.ar_state]?.t}</span></Td>
              </tr>
            ))}
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
    </div>
  )
}

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
