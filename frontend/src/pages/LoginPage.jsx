/**
 * Login Page Component
 * Enhanced with glassmorphism design and scrolling partner logos
 */

import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { authFetch, API_URL } from '../utils/auth-fetch';
import './LoginPage.css';

// Partner company logos - using image files from /partners folder
const PARTNER_LOGOS = [
  { name: 'DB Schenker', image: '/partners/db-schenker.png' },
  { name: 'Dainese', image: '/partners/dainese.png' },
  { name: 'Messer', image: '/partners/messer.png' },
  { name: 'Dongsung', image: '/partners/dongsung.png' },
  { name: 'Nippon Express', image: '/partners/nippon-express.png' },
  { name: 'Blackstone', image: '/partners/blackstone.png' },
  { name: 'Samsung', image: '/partners/samsung.png' },
  { name: 'VAF', image: '/partners/vaf.png' },
  { name: 'Meiko', image: '/partners/meiko.png' },
  { name: 'TNGEC', image: '/partners/tngec.png' },
  { name: 'New Order', image: '/partners/new-order.png' },
];

function ForgotPasswordForm({ onBack }) {
  const [email, setEmail] = useState('');
  const [channel, setChannel] = useState('both'); // 'email' | 'telegram' | 'both'
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authFetch(`${API_URL}/api/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, channel }),
      });
    } catch (_) { /* luôn hiển thị chung */ }
    const via = channel === 'email' ? 'email' : channel === 'telegram' ? 'Telegram' : 'email và Telegram';
    setMsg(`Nếu email tồn tại, hướng dẫn đặt lại mật khẩu đã được gửi qua ${via}. Vui lòng kiểm tra.`);
    setLoading(false);
  };

  const chOpts = [
    { v: 'both', label: '📧 + 💬 Cả hai' },
    { v: 'email', label: '📧 Email' },
    { v: 'telegram', label: '💬 Telegram' },
  ];

  return (
    <div className="login-form-section">
      <h1 className="login-title">Quên mật khẩu</h1>
      <p className="login-subtitle">Nhập email và chọn kênh nhận link đặt lại</p>
      {msg ? (
        <div className="error-message" style={{ background: '#dcfce7', color: '#166534', borderColor: '#86efac' }}>{msg}</div>
      ) : (
        <form onSubmit={submit} className="login-form">
          <div className="form-group">
            <label htmlFor="fp-email">Email</label>
            <input type="email" id="fp-email" value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="email@5pvietnam.com" required autoFocus />
          </div>
          <div className="form-group">
            <label>Gửi link qua</label>
            <div style={{ display: 'flex', gap: 8 }}>
              {chOpts.map((o) => (
                <button type="button" key={o.v} onClick={() => setChannel(o.v)}
                  style={{
                    flex: 1, padding: '9px 4px', borderRadius: 8, fontSize: 13, cursor: 'pointer',
                    border: channel === o.v ? '2px solid #2563eb' : '1px solid #cbd5e1',
                    background: channel === o.v ? '#eff6ff' : '#fff',
                    color: channel === o.v ? '#1d4ed8' : '#475569',
                    fontWeight: channel === o.v ? 600 : 400,
                  }}>{o.label}</button>
              ))}
            </div>
            <p style={{ fontSize: 12, color: '#64748b', marginTop: 6 }}>
              Telegram: cần đã từng nhắn bot 5P Vietnam.
            </p>
          </div>
          <button type="submit" className="login-button" disabled={loading}>
            {loading ? <span className="loading-spinner"></span> : 'Gửi link đặt lại'}
          </button>
        </form>
      )}
      <p style={{ textAlign: 'center', marginTop: 16 }}>
        <a href="#" onClick={(e) => { e.preventDefault(); onBack(); }}
          style={{ color: '#2563eb', fontSize: 14 }}>← Quay lại đăng nhập</a>
      </p>
    </div>
  );
}

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState('login'); // 'login' | 'forgot'

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await login(email, password);

    if (!result.success) {
      setError(result.message || 'Đăng nhập thất bại');
    }

    setLoading(false);
  };

  // Double the logos for seamless infinite scroll
  const duplicatedLogos = [...PARTNER_LOGOS, ...PARTNER_LOGOS];

  return (
    <div className="login-page">
      {/* Background overlay */}
      <div className="login-overlay"></div>

      {/* Main content */}
      <div className="login-content">
        {/* Glassmorphism card */}
        <div className="login-card">
          {/* Logo */}
          <div className="login-branding">
            <img src="/logo.png" alt="5P Vietnam" className="login-logo" />
          </div>

          {/* Login / Forgot form */}
          {mode === 'forgot' ? (
          <ForgotPasswordForm onBack={() => setMode('login')} />
          ) : (
          <div className="login-form-section">
            <h1 className="login-title">Đăng nhập</h1>
            <p className="login-subtitle">Chào mừng bạn quay trở lại</p>

            <form onSubmit={handleSubmit} className="login-form">
              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="email@5pvietnam.com"
                  required
                  autoFocus
                />
              </div>

              <div className="form-group">
                <label htmlFor="password">Mật khẩu</label>
                <input
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Nhập mật khẩu"
                  required
                />
              </div>

              {error && <div className="error-message">{error}</div>}

              <button type="submit" className="login-button" disabled={loading}>
                {loading ? (
                  <span className="loading-spinner"></span>
                ) : (
                  'Đăng nhập'
                )}
              </button>
            </form>
            <p style={{ textAlign: 'center', marginTop: 14 }}>
              <a href="#" onClick={(e) => { e.preventDefault(); setError(''); setMode('forgot'); }}
                style={{ color: '#2563eb', fontSize: 14 }}>Quên mật khẩu?</a>
            </p>
          </div>
          )}

          {/* Footer */}
          <div className="login-footer">
            <p>© 2026 5P Vietnam</p>
          </div>
        </div>
      </div>

      {/* Partner logos carousel - Temporarily disabled
      <div className="partner-section">
        <p className="partner-title">Trusted by leading companies</p>
        <div className="partner-logos-wrapper">
          <div className="partner-logos">
            {duplicatedLogos.map((partner, index) => (
              <div key={index} className="partner-logo" title={partner.name}>
                <img src={partner.image} alt={partner.name} />
              </div>
            ))}
          </div>
        </div>
      </div>
      */}
    </div>
  );
}
