/**
 * Authentication Context
 * Manages user authentication state and provides login/logout functions
 */

import { createContext, useContext, useState, useEffect, useRef } from 'react';
import { AUTH_EXPIRED_EVENT } from '../utils/auth-fetch';

const AuthContext = createContext(null);

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // Check token validity on mount
  useEffect(() => {
    if (token) {
      checkAuth();
    } else {
      setLoading(false);
    }
  }, []);

  const checkAuth = async () => {
    try {
      const response = await fetch(`${API_URL}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setUser(data.user);
        } else {
          // Token invalid
          logout();
        }
      } else {
        logout();
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (data.success) {
        setToken(data.token);
        setUser(data.user);
        localStorage.setItem('token', data.token);
        return { success: true };
      } else {
        return { success: false, message: data.message };
      }
    } catch (error) {
      console.error('Login failed:', error);
      return { success: false, message: 'Lỗi kết nối server' };
    }
  };

  const logout = () => {
    // Call logout endpoint (fire and forget)
    if (token) {
      fetch(`${API_URL}/api/auth/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }).catch(() => {});
    }

    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
  };

  // 13/10/2026: token hết hạn giữa chừng (tab mở > 8 tiếng) → authFetch bắn AUTH_EXPIRED_EVENT.
  // Trước đây app không biết, mọi danh sách hiện rỗng. Giờ báo 1 lần rồi về màn đăng nhập.
  const expiredNotified = useRef(false);
  useEffect(() => {
    const onExpired = () => {
      if (expiredNotified.current) return;
      expiredNotified.current = true;
      alert('Phiên đăng nhập đã hết hạn. Anh/chị vui lòng đăng nhập lại.');
      logout();
      expiredNotified.current = false;
    };
    window.addEventListener(AUTH_EXPIRED_EVENT, onExpired);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, onExpired);
  });

  // Kiểm lại token khi người dùng quay lại tab (máy ngủ / để qua đêm)
  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState !== 'visible') return;
      const t = localStorage.getItem('token');
      if (!t) return;
      try {
        const payload = JSON.parse(atob(t.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
        if (payload.exp && payload.exp * 1000 < Date.now()) {
          window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT));
        }
      } catch { /* token lạ — để API tự trả 401 */ }
    };
    document.addEventListener('visibilitychange', onVisible);
    return () => document.removeEventListener('visibilitychange', onVisible);
  }, []);

  const hasRole = (role) => {
    if (!user) return false;
    if (user.role === 'ADMIN') return true;
    return user.role === role;
  };

  const isAdmin = () => hasRole('ADMIN');
  const isManager = () => hasRole('ADMIN') || hasRole('MANAGER');

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    hasRole,
    isAdmin,
    isManager,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Utility function for API calls with auth
export async function fetchWithAuth(url, options = {}) {
  const token = localStorage.getItem('token');

  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json',
    },
  });
}

export default AuthContext;
