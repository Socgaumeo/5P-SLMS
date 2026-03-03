// Centralized fetch wrapper that auto-injects JWT auth header
// Use this instead of raw fetch() for all API calls requiring authentication

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function getAuthHeaders() {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/**
 * Wrapper around fetch that auto-injects Authorization header.
 * Accepts full URL or path (auto-prepends API_URL if path starts with /).
 */
export async function authFetch(url, options = {}) {
  const fullUrl = url.startsWith('/') ? `${API_URL}${url}` : url
  const headers = { ...getAuthHeaders(), ...(options.headers || {}) }
  return fetch(fullUrl, { ...options, headers })
}

export { API_URL }
