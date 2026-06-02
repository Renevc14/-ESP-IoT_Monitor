import axios from 'axios'

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL ?? 'http://localhost:8000'

export const api = axios.create({
  baseURL: GATEWAY_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true, // enviar/recibir la cookie HttpOnly del refresh token
})

// Attach access token from sessionStorage before every request
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-refresh on 401 using the HttpOnly refresh cookie
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry && !original.url?.includes('/auth/')) {
      original._retry = true
      try {
        const { data } = await axios.post(`${GATEWAY_URL}/auth/refresh`, {}, { withCredentials: true })
        sessionStorage.setItem('access_token', data.access_token)
        original.headers.Authorization = `Bearer ${data.access_token}`
        return api(original)
      } catch {
        sessionStorage.clear()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)
