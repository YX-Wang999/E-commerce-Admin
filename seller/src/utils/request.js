import axios from 'axios'
import { ElMessage } from 'element-plus'
import { resolveApiBaseUrl } from '@shared/utils/apiBase.js'
import {
  clearAuthStorage,
  getAccessToken,
  getRefreshToken,
  getTenantCode,
  setTokens,
} from '@/utils/auth'

const AUTH_ERROR_CODES = new Set([40100])

const API_BASE_URL = resolveApiBaseUrl(import.meta.env.VITE_API_BASE_URL)

const request = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
})

let isRefreshing = false
let pendingRequests = []
let sessionExpiredHandled = false

function getLoginPath() {
  const base = import.meta.env.BASE_URL || '/'
  return `${base}${base.endsWith('/') ? '' : '/'}login`.replace(/([^:]\/)\/+/g, '$1')
}

function isOnLoginPage() {
  const loginPath = getLoginPath()
  return window.location.pathname === loginPath || window.location.pathname.endsWith('/login')
}

function isAuthEndpoint(url = '') {
  return url.includes('/seller/auth/login/') || url.includes('/auth/refresh/')
}

function isAuthExpiredPayload(payload) {
  if (!payload || typeof payload !== 'object') {
    return false
  }
  if (typeof payload.code === 'number' && AUTH_ERROR_CODES.has(payload.code)) {
    return true
  }
  const message = String(payload.message || '')
  return /登录.*(失效|超时)|请重新登录|refresh token|token.*(invalid|expired)/i.test(message)
}

function subscribeTokenRefresh(onSuccess, onFailure) {
  pendingRequests.push({ onSuccess, onFailure })
}

function onRefreshed(token) {
  pendingRequests.splice(0).forEach(({ onSuccess }) => onSuccess(token))
}

function onRefreshFailed(error) {
  pendingRequests.splice(0).forEach(({ onFailure }) => onFailure(error))
}

function handleSessionExpired(message) {
  if (sessionExpiredHandled || isOnLoginPage()) {
    return
  }
  sessionExpiredHandled = true
  clearAuthStorage()
  isRefreshing = false
  onRefreshFailed(new Error(message || '登录已失效，请重新登录'))
  ElMessage.error(message || '登录已失效，请重新登录')
  window.location.assign(getLoginPath())
}

async function refreshAccessToken() {
  const refresh = getRefreshToken()
  if (!refresh) {
    throw new Error('No refresh token')
  }
  const response = await axios.post(
    `${API_BASE_URL}/auth/refresh/`,
    { refresh },
  )
  const { code, data, message } = response.data
  if (code !== 0) {
    throw new Error(message || 'Token refresh failed')
  }
  const access = data.access
  setTokens(access, refresh)
  return access
}

request.interceptors.request.use(
  (config) => {
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    const tenantCode = getTenantCode()
    if (tenantCode) {
      config.headers['X-Tenant-Code'] = tenantCode
    }
    return config
  },
  (error) => Promise.reject(error),
)

request.interceptors.response.use(
  (response) => {
    const payload = response.data
    if (
      payload
      && typeof payload.code === 'number'
      && payload.code !== 0
      && !response.config?.skipErrorHandler
    ) {
      if (isAuthExpiredPayload(payload)) {
        handleSessionExpired(payload.message)
        return Promise.reject(payload)
      }
      ElMessage.error(payload.message || '请求失败')
      return Promise.reject(payload)
    }
    return payload
  },
  async (error) => {
    const originalRequest = error.config
    const status = error.response?.status
    const responseData = error.response?.data

    if (originalRequest?.skipErrorHandler) {
      return Promise.reject(responseData || error)
    }

    if (status === 403 && originalRequest?.url?.includes('/seller/auth/login/')) {
      return Promise.reject(responseData || error)
    }

    if (status === 401 && originalRequest) {
      if (isAuthEndpoint(originalRequest.url)) {
        clearAuthStorage()
        return Promise.reject(error)
      }

      if (originalRequest._retry) {
        handleSessionExpired(responseData?.message)
        return Promise.reject(responseData || error)
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          subscribeTokenRefresh(
            (token) => {
              originalRequest.headers.Authorization = `Bearer ${token}`
              resolve(request(originalRequest))
            },
            reject,
          )
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const newToken = await refreshAccessToken()
        onRefreshed(newToken)
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return request(originalRequest)
      } catch (refreshError) {
        handleSessionExpired(
          refreshError?.response?.data?.message
          || refreshError?.message
          || responseData?.message,
        )
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    if (isAuthExpiredPayload(responseData) && !isAuthEndpoint(originalRequest?.url)) {
      handleSessionExpired(responseData?.message)
      return Promise.reject(responseData || error)
    }

    const message = responseData?.message || error.message || '网络错误'
    ElMessage.error(message)
    return Promise.reject(responseData || error)
  },
)

export default request
