/**
 * Landing Page — trang giới thiệu công khai www.5pvietnam.com
 * Hiện khi chưa đăng nhập; nút "Đăng nhập" (góc trên phải) mở /login.
 */
import './LandingPage.css';

const SERVICES = [
  { icon: '🚚', vi: 'Vận tải đường bộ', en: 'Trucking', desc: 'Xe tải và container nội địa, xuyên biên giới; giao tận nhà máy, khu công nghiệp.' },
  { icon: '✈️', vi: 'Hàng không', en: 'Air freight', desc: 'Xuất nhập khẩu hàng không, gom hàng, giao nhận tại Nội Bài.' },
  { icon: '🚢', vi: 'Đường biển & container', en: 'Sea freight', desc: 'FCL, LCL qua Hải Phòng; booking, vận đơn, khai thác cảng.' },
  { icon: '📋', vi: 'Thủ tục hải quan', en: 'Customs brokerage', desc: 'Khai báo, kiểm hoá, C/O, tư vấn mã HS và loại hình tờ khai.' },
  { icon: '🏭', vi: 'Kho bãi', en: 'Warehousing', desc: 'Lưu kho, bốc xếp, quản lý xuất nhập tồn.' },
  { icon: '📦', vi: 'Đóng gói', en: 'Packing', desc: 'Đóng pallet, gia cố, chèn lót cho hàng dễ vỡ và hàng xuất khẩu.' },
];

const AI_POINTS = [
  'Đọc và đối chiếu chứng từ: invoice, packing list, vận đơn, tờ khai',
  'Theo dõi lô hàng, chi phí, doanh thu trên hệ thống SLMS',
  'Nhắc đúng người khi lô hàng thiếu chứng từ',
  'Nhân viên làm việc qua Telegram và Zalo, có người duyệt trước khi ghi dữ liệu',
];

function goLogin() {
  window.location.href = '/login';
}

export default function LandingPage() {
  const year = new Date().getFullYear();
  return (
    <div className="lp">
      <header className="lp-nav">
        <a className="lp-brand" href="/">
          <img src="/logo.png" alt="5P Vietnam" />
        </a>
        <nav className="lp-links">
          <a href="#dich-vu">Dịch vụ</a>
          <a href="#cong-nghe">Công nghệ</a>
          <a href="#lien-he">Liên hệ</a>
        </nav>
        <button className="lp-login" onClick={goLogin}>Đăng nhập</button>
      </header>

      <section className="lp-hero">
        <div className="lp-hero-overlay" />
        <div className="lp-hero-inner">
          <p className="lp-eyebrow">Logistics · Customs · Warehousing</p>
          <h1>Giao nhận và vận tải trọn gói, vận hành bằng AI</h1>
          <p className="lp-lead">
            5P Vietnam lo trọn chặng hàng của doanh nghiệp sản xuất và xuất nhập khẩu:
            đường bộ, hàng không, đường biển, hải quan và kho bãi tại miền Bắc Việt Nam.
          </p>
          <div className="lp-cta">
            <a className="lp-btn lp-btn-primary" href="#lien-he">Liên hệ báo giá</a>
            <a className="lp-btn lp-btn-ghost" href="#dich-vu">Xem dịch vụ</a>
          </div>
        </div>
      </section>

      <section className="lp-section" id="dich-vu">
        <h2>Dịch vụ</h2>
        <p className="lp-sub">Một đầu mối cho cả chuỗi giao nhận.</p>
        <div className="lp-grid">
          {SERVICES.map((s) => (
            <div className="lp-card" key={s.en}>
              <div className="lp-card-icon">{s.icon}</div>
              <h3>{s.vi}</h3>
              <span className="lp-card-en">{s.en}</span>
              <p>{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="lp-section lp-ai" id="cong-nghe">
        <div className="lp-ai-text">
          <h2>Vận hành bằng AI</h2>
          <p className="lp-sub">
            Chúng tôi tự xây hệ thống quản lý logistics SLMS và trợ lý vận hành Sen,
            chạy trên mô hình Claude. Nhân viên dùng hằng ngày để xử lý lô hàng nhanh và ít sai sót hơn.
          </p>
          <ul>
            {AI_POINTS.map((t) => <li key={t}>{t}</li>)}
          </ul>
        </div>
        <div className="lp-ai-badge">
          <span>SLMS</span>
          <small>Smart Logistics Management System</small>
        </div>
      </section>

      <section className="lp-section lp-contact" id="lien-he">
        <h2>Liên hệ</h2>
        <div className="lp-contact-grid">
          <div>
            <h4>Công ty TNHH Thương mại và Dịch vụ 5P Việt Nam</h4>
            <p>5P Vietnam Trading and Service Co., Ltd</p>
            <p>Mã số thuế: 0110523309</p>
          </div>
          <div>
            <h4>Địa chỉ</h4>
            <p>Số nhà 2, ngõ 1H, phố Trần Quang Diệu, Hà Nội, Việt Nam</p>
          </div>
          <div>
            <h4>Email</h4>
            <p><a href="mailto:info@5pvietnam.com">info@5pvietnam.com</a></p>
          </div>
        </div>
      </section>

      <footer className="lp-footer">
        © {year} 5P Vietnam Trading and Service Co., Ltd
      </footer>
    </div>
  );
}
