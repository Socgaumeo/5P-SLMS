// Centralized fetch wrapper that auto-injects JWT auth header
// Use this instead of raw fetch() for all API calls requiring authentication

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function getAuthHeaders() {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// 13/10/2026 (chị Hà, job BI-32-2610-001): token hết hạn sau 8 tiếng nhưng app chỉ kiểm
// token lúc mở trang ⇒ để tab qua đêm thì MỌI API trả 401, giao diện lặng lẽ hiện rỗng
// ("Chưa có chứng từ nào") dù DB có đủ. Giờ gặp 401 là báo AuthContext đăng xuất,
// đưa về màn đăng nhập kèm thông báo.
export const AUTH_EXPIRED_EVENT = 'auth:expired'

function notifyAuthExpired(url) {
  if (url.includes('/api/auth/')) return // login/me/logout tự xử lý
  if (!localStorage.getItem('token')) return
  window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT))
}

/**
 * Wrapper around fetch that auto-injects Authorization header.
 * Accepts full URL or path (auto-prepends API_URL if path starts with /).
 */
export async function authFetch(url, options = {}) {
  const fullUrl = url.startsWith('/') ? `${API_URL}${url}` : url
  const headers = { ...getAuthHeaders(), ...(options.headers || {}) }
  const res = await fetch(fullUrl, { ...options, headers })
  if (res.status === 401) notifyAuthExpired(fullUrl)
  return res
}

export { API_URL }
