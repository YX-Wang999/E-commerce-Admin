import axios from 'axios'
import { ElMessage } from 'element-plus'
import { resolveApiBaseUrl } from '@shared/utils/apiBase.js'
import i18n from '@/i18n'
import { getDeviceId } from '@/utils/device'
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from '@/utils/auth'

const t = (key) => i18n.global.t(key)

const AUTH_ERROR_CODES = new Set([40100])

const API_BASE_URL = resolveApiBaseUrl(import.meta.env.VITE_API_BASE_URL)

const request = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
})

let isRefreshing = false
let refreshWaiters = []
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
  return url.includes('/auth/login/') || url.includes('/auth/refresh/')
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

function onRefreshed(token) {
  refreshWaiters.splice(0).forEach(({ onSuccess }) => onSuccess(token))
}

function onRefreshFailed(error) {
  refreshWaiters.splice(0).forEach(({ onFailure }) => onFailure(error))
}

function handleSessionExpired(message) {
  if (sessionExpiredHandled || isOnLoginPage()) {
    return
  }
  sessionExpiredHandled = true
  clearTokens()
  isRefreshing = false
  onRefreshFailed(new Error(message || t('auth.sessionExpired')))
  ElMessage.error(message || t('auth.sessionExpired'))
  window.location.assign(getLoginPath())
}

function subscribeTokenRefresh(onSuccess, onFailure) {
  refreshWaiters.push({ onSuccess, onFailure })
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
    config.headers['X-Device-Id'] = getDeviceId()
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

request.interceptors.response.use(
  (response) => {
    if (response.config.responseType === 'blob') {
      const contentType = response.headers['content-type'] || ''
      if (contentType.includes('application/json')) {
        return response.data.text().then((text) => {
          let payload = {}
          try {
            payload = JSON.parse(text)
          } catch {
            payload = { message: t('common.exportFailed') }
          }
          if (!response.config?.skipErrorHandler) {
            ElMessage.error(payload.message || t('common.exportFailed'))
          }
          return Promise.reject(payload)
        })
      }
      return response
    }
    const payload = response.data
    if (
      payload
      && typeof payload.code === 'number'
      && payload.code !== 0
      && payload.code !== 1001
      && !response.config?.skipErrorHandler
    ) {
      if (isAuthExpiredPayload(payload)) {
        handleSessionExpired(payload.message)
        return Promise.reject(payload)
      }
      ElMessage.error(payload.message || t('common.requestFailed'))
      return Promise.reject(payload)
    }
    return payload
  },
  async (error) => {
    const originalRequest = error.config
    const status = error.response?.status
    const responseData = error.response?.data

    if (originalRequest?.skipErrorHandler) {
      let payload = { message: error.message || t('common.networkError') }
      if (responseData && typeof responseData === 'object' && !Array.isArray(responseData)) {
        payload = responseData
      } else if (status === 404) {
        payload = {
          code: 404,
          message: t('login.captchaApiNotFound'),
        }
      }
      return Promise.reject(payload)
    }

    if (status === 401 && originalRequest) {
      if (isAuthEndpoint(originalRequest.url)) {
        clearTokens()
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

    const message = responseData?.message || error.message || t('common.networkError')
    if (!originalRequest?.skipErrorHandler) {
      ElMessage.error(message)
    }
    return Promise.reject(error)
  },
)

export default request
