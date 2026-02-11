/**
 * Login Page Component
 * Enhanced with glassmorphism design and scrolling partner logos
 */

import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
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

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

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

          {/* Login form */}
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
          </div>

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
