import { useEffect, useState, useCallback } from 'react'
import { authFetch, API_URL } from '../../utils/auth-fetch'
import { useAuth } from '../../contexts/AuthContext'
import './DieuHanhPage.css'

// Bảng điều hành job (Khánh duyệt 13/10/2026): mọi user xem, tự sửa phần việc của mình.
// Chỉ tính job có ngày thực hiện từ 01/10/2026.
const TT = {
  PENDING: ['Chờ', '#94a3b8'], ASSIGNED: ['Phân công', '#6366f1'], DISPATCHED: ['Xe chạy', '#6366f1'],
  IN_TRANSIT: ['Đang chạy', '#6366f1'], IN_PROGRESS: ['Đang làm', '#3b82f6'], DELIVERED: ['Đã giao', '#f59e0b'],
  COMPLETED: ['Xong', '#10b981'], CANCELLED: ['Huỷ', '#cbd5e1'],
}
const tt = (s) => TT[s] || [s || '?', '#cbd5e1']

export default function DieuHanhPage({ onOpenJob }) {
  const { user } = useAuth()
  const [d, setD] = useState(null)
  const [err, setErr] = useState('')
  const [cuaToi, setCuaToi] = useState(false)
  const [nguoi, setNguoi] = useState('')

  const tai = useCallback(async () => {
    try {
      const r = await authFetch(`${API_URL}/api/dieu-hanh`)
      const j = await r.json()
      if (!r.ok || !j.success) throw new Error(j.detail || j.message || `Lỗi ${r.status}`)
      setD(j); setErr('')
    } catch (e) { setErr(e.message) }
  }, [])

  useEffect(() => { tai(); const t = setInterval(tai, 60000); return () => clearInterval(t) }, [tai])

  if (err && !d) return <div className="dh"><div className="dh-alert">Không tải được bảng điều hành: {err}</div></div>
  if (!d) return <div className="dh"><div className="dh-note">Đang tải…</div></div>

  const toi = user?.user_id
  const loc = (x) => (!cuaToi || x.uid === toi) && (!nguoi || x.nguoi === nguoi)
  const nv = d.nhan_vien.filter((x) => (!cuaToi || x.uid === toi) && (!nguoi || x.ten === nguoi))
  const mx = Math.max(1, ...d.nhan_vien.map((x) => x.mo || 0))
  const chuY = d.can_chu_y.filter(loc)
  const k = d.thao_tac_24h.kenh || {}

  return (
    <div className="dh">
      <div className="dh-head">
        <div>
          <span className="dh-live">Tự làm mới mỗi 60 giây</span>
          <span className="dh-time">Số liệu lúc {d.gio} · job có ngày thực hiện từ 01/10/2026</span>
        </div>
        <div className="dh-filter">
          <label><input type="checkbox" checked={cuaToi} onChange={(e) => { setCuaToi(e.target.checked); setNguoi('') }} /> Chỉ việc của tôi</label>
          <select value={nguoi} onChange={(e) => { setNguoi(e.target.value); setCuaToi(false) }}>
            <option value="">Tất cả nhân viên</option>
            {d.nhan_vien.map((x) => <option key={x.ten} value={x.ten}>{x.ten}</option>)}
          </select>
          <button onClick={tai}>Làm mới</button>
        </div>
      </div>

      <div className="dh-kpis">
        <div className="dh-k"><div className="l">Job đang mở</div><div className="v">{d.tong_mo}</div></div>
        <div className="dh-k"><div className="l">Chờ xử lý</div><div className="v">{d.theo_tt.PENDING || 0}</div></div>
        <div className="dh-k"><div className="l">Đang làm</div><div className="v">{(d.theo_tt.IN_PROGRESS || 0) + (d.theo_tt.ASSIGNED || 0) + (d.theo_tt.DISPATCHED || 0) + (d.theo_tt.IN_TRANSIT || 0)}</div></div>
        <div className="dh-k"><div className="l">Đã giao, chưa chốt</div><div className="v">{d.theo_tt.DELIVERED || 0}</div></div>
        <div className="dh-k ok"><div className="l">Hoàn thành 7 ngày</div><div className="v">{d.xong7}</div></div>
        <div className="dh-k warn"><div className="l">Cần chú ý</div><div className="v">{d.n_chu_y}</div></div>
      </div>

      <section className="dh-sec">
        <h2>Khối lượng việc theo nhân viên <small>job đang mở do người đó tạo</small></h2>
        <div className="dh-lg"><span><i style={{ background: '#94a3b8' }} />Chờ</span><span><i style={{ background: '#3b82f6' }} />Đang làm</span><span><i style={{ background: '#f59e0b' }} />Đã giao chưa chốt</span></div>
        <div className="dh-tw"><table>
          <thead><tr><th>Nhân viên</th><th className="n">Đang mở</th><th>Phân bổ</th><th className="n">Chờ</th><th className="n">Đang làm</th><th className="n">Đã giao</th><th className="n">Quá lịch</th><th className="n">&gt;14 ngày</th><th className="n">Xong 7 ngày</th><th className="n">Thao tác 24h</th></tr></thead>
          <tbody>{nv.map((x) => {
            const p = x.PENDING || 0, dl = x.DELIVERED || 0, i = (x.mo || 0) - p - dl
            return (
              <tr key={x.ten} className={x.uid === toi ? 'me' : ''} onClick={() => { setNguoi(x.ten); setCuaToi(false) }}>
                <td className="ten">{x.ten}{x.uid === toi ? ' (tôi)' : ''}</td><td className="n b">{x.mo || 0}</td>
                <td className="bc"><div className="bar">{[[p, '#94a3b8'], [i, '#3b82f6'], [dl, '#f59e0b']].filter(([v]) => v > 0).map(([v, c], idx) => <span key={idx} style={{ width: `${(v / mx) * 100}%`, background: c }} />)}</div></td>
                <td className="n">{p}</td><td className="n">{i}</td><td className="n">{dl}</td>
                <td className={`n ${x.qua_lich ? 'bad' : ''}`}>{x.qua_lich || 0}</td><td className="n">{x.cu_14 || 0}</td>
                <td className="n good">{x.xong7 || 0}</td><td className="n">{x.thao_tac_24h || 0}</td>
              </tr>)
          })}</tbody>
        </table></div>
        <p className="dh-note">Quá lịch = có dịch vụ quá ngày thực hiện mà chưa giao/xong. Bấm tên nhân viên để lọc. Thao tác 24h = nhập trên web hoặc nhờ Sen nhập hộ.</p>
      </section>

      <section className="dh-sec">
        <h2>Job cần chú ý <small>quá lịch hoặc mở &gt;14 ngày · {chuY.length} job · bấm để mở và sửa</small></h2>
        {chuY.length === 0 ? <div className="dh-empty">Không có job nào cần chú ý 👍</div> : (
          <div className="dh-jobs">{chuY.map((a) => (
            <div key={a.job_id} className="dh-job" onClick={() => onOpenJob && onOpenJob({ job_id: a.job_id, job_no: a.job_no })}>
              <div className="jh"><b>{a.job_no}</b><span className="kh">{a.khach}</span><span className={`age ${a.tuoi > 14 ? 'bad' : ''}`}>{a.tuoi} ngày</span></div>
              <div className="jm">{a.nguoi} · {tt(a.trang_thai)[0]}{a.qua_lich ? <b className="bad"> · {a.qua_lich} dịch vụ quá lịch</b> : null}</div>
              <div className="chips">{a.dich_vu.map((s, i) => <span key={i} className="chip" style={{ borderColor: tt(s.tt)[1] }}>{s.loai} · {tt(s.tt)[0]}{s.ngay ? ` · ${s.ngay.slice(8, 10)}/${s.ngay.slice(5, 7)}` : ''}</span>)}</div>
            </div>))}</div>)}
      </section>

      <section className="dh-sec">
        <h2>Thao tác ghi nhận 24h <small>web + Sen nhập hộ</small></h2>
        <div className="dh-kpis">
          <div className="dh-k"><div className="l">Tổng</div><div className="v">{d.thao_tac_24h.tong}</div></div>
          <div className="dh-k"><div className="l">Qua Sen</div><div className="v">{k.sen || 0}</div></div>
          <div className="dh-k"><div className="l">Qua web</div><div className="v">{k.web || 0}</div></div>
          <div className="dh-k"><div className="l">Sen tự cập nhật</div><div className="v">{(k.tu_dong || 0) + (k.cron || 0)}</div></div>
        </div>
      </section>
    </div>
  )
}
