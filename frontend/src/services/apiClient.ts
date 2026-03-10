// services/apiClient.ts
// Axios instance with Firebase JWT injection and error normalisation.

import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { auth } from '@/config/firebase'
import { API_BASE_URL } from '@/config/api'
import { normaliseError } from '@/utils/errorHandler'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor: attach Firebase ID token ─────────────────────────
apiClient.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  const user = auth.currentUser
  if (user) {
    const token = await user.getIdToken()
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Response interceptor: normalise errors ────────────────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const msg = normaliseError(error)
    return Promise.reject(new Error(msg))
  }
)

export default apiClient
