/**
 * Landing Page — trang giới thiệu công khai www.5pvietnam.com
 * Hiện khi chưa đăng nhập; nút "Đăng nhập" (góc trên phải) mở /login.
 */
import './LandingPage.css';

const SERVICES = [
  { icon: '🚚', vi: 'Vận tải đường bộ', en: 'Trucking', desc: 'Xe tải và container nội địa, xuyên biên giới; giao tận nhà máy, khu công nghiệp.' },
  { icon: '✈️', vi: 'Hàng không', en: 'Air freight', desc: 'Xuất nhập khẩu hàng không quốc tế, gom hàng, giao nhận tại sân bay Nội Bài.' },
  { icon: '🚢', vi: 'Đường biển & container', en: 'Sea freight', desc: 'FCL, LCL đi và đến các cảng quốc tế qua Hải Phòng; booking, vận đơn, khai thác cảng.' },
  { icon: '📋', vi: 'Thủ tục hải quan', en: 'Customs brokerage', desc: 'Khai báo, kiểm hoá, C/O, tư vấn mã HS và loại hình tờ khai.' },
  { icon: '🏭', vi: 'Kho bãi', en: 'Warehousing', desc: 'Lưu kho, bốc xếp, quản lý xuất nhập tồn.' },
  { icon: '📦', vi: 'Đóng gói', en: 'Packing', desc: 'Đóng pallet, gia cố, chèn lót cho hàng dễ vỡ và hàng xuất khẩu.' },
];

const AI_POINTS = [
  { t: 'Chứng từ chuẩn ngay từ đầu', d: 'Invoice, packing list, vận đơn, tờ khai được đối chiếu chéo trước khi khai báo — hạn chế phát sinh sửa đổi, phạt chậm.' },
  { t: 'Theo sát từng lô hàng', d: 'Lịch trình, chứng từ và chi phí nằm chung trên một hệ thống, thông tin luôn sẵn sàng khi Quý khách cần.' },
  { t: 'Không để lô hàng phải chờ', d: 'Thiếu chứng từ là đúng người phụ trách được nhắc ngay, không để việc trôi qua ngày.' },
  { t: 'AI hỗ trợ, con người chịu trách nhiệm', d: 'Mọi cập nhật dữ liệu đều có nhân viên 5P kiểm duyệt trước khi ghi nhận.' },
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
          <p className="lp-eyebrow">International Freight · Customs · Logistics</p>
          <h1>Đưa hàng hoá của bạn ra thế giới — nhanh, đúng hẹn, minh bạch</h1>
          <p className="lp-lead">
            5P Vietnam là đối tác logistics trọn gói của doanh nghiệp sản xuất và xuất nhập khẩu:
            vận chuyển quốc tế bằng đường hàng không, đường biển và đường bộ xuyên biên giới, cùng thủ tục hải quan,
            kho bãi và giao nhận nội địa. Một đầu mối duy nhất theo sát lô hàng từ cửa nhà máy đến tay người nhận,
            với hệ thống vận hành bằng AI.
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
          <h2>Công nghệ AI — lô hàng luôn trong tầm kiểm soát</h2>
          <p className="lp-sub">
            5P tự phát triển hệ thống quản lý logistics SLMS và trợ lý vận hành AI Sen, chạy trên mô hình Claude của Anthropic.
            Mỗi lô hàng của Quý khách được theo dõi từ lúc nhận booking đến khi giao xong: chứng từ kiểm tra kỹ, xử lý nhanh, sai sót được chặn từ sớm.
          </p>
          <ul className="lp-ai-list">
            {AI_POINTS.map((x) => (
              <li key={x.t}><strong>{x.t}</strong><span>{x.d}</span></li>
            ))}
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
            <h4>Điện thoại</h4>
            <p><a href="tel:+84848346886">084 834 6886</a></p>
            <h4 style={{ marginTop: 14 }}>Email</h4>
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
