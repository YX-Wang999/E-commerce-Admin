import axios from 'axios'
import { resolveApiBaseUrl } from '@shared/utils/apiBase.js'
import { LOGIN_REQUIRED_CODE } from '@/constants/api'
import i18n from '@/i18n'
import { toastError } from '@/utils/feedback'
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  isAccessTokenExpired,
  isLoggedIn,
  needsTokenRefresh,
  setTokens,
} from '@/utils/auth'

const { t } = i18n.global

const API_BASE_URL = resolveApiBaseUrl(import.meta.env.VITE_API_BASE_URL)

const request = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
})

let isRefreshing = false
let refreshWaiters = []
let activeRefreshPromise = null

function subscribeTokenRefresh(onSuccess, onFailure) {
  refreshWaiters.push({ onSuccess, onFailure })
}

function onRefreshed(token) {
  refreshWaiters.splice(0).forEach(({ onSuccess }) => onSuccess(token))
}

function onRefreshFailed(error) {
  refreshWaiters.splice(0).forEach(({ onFailure }) => onFailure(error))
}

function isDefinitiveAuthFailure(error) {
  const status = error?.response?.status
  const code = error?.response?.data?.code
  return status === 401 || code === 40100
}

function shouldClearSessionAfterRefreshFailure(error) {
  if (!isDefinitiveAuthFailure(error)) {
    return false
  }
  const access = getAccessToken()
  return !access || isAccessTokenExpired(access)
}

async function maybeClearSession(error) {
  if (shouldClearSessionAfterRefreshFailure(error)) {
    await clearSessionSilently()
  }
}

/** 全局唯一 refresh，避免页面加载时多路 401 并发刷新导致误清会话 */
function ensureFreshAccessToken() {
  if (activeRefreshPromise) {
    return activeRefreshPromise
  }

  const refresh = getRefreshToken()
  if (!refresh) {
    return Promise.reject(new Error('No refresh token'))
  }

  isRefreshing = true
  activeRefreshPromise = refreshAccessToken()
    .then((token) => {
      onRefreshed(token)
      return token
    })
    .catch(async (error) => {
      await maybeClearSession(error)
      onRefreshFailed(error)
      throw error
    })
    .finally(() => {
      activeRefreshPromise = null
      isRefreshing = false
    })

  return activeRefreshPromise
}

/** C 端会话失效：静默清 token，不弹「超时」、不强制跳登录页 */
async function clearSessionSilently() {
  try {
    const { useAuthStore } = await import('@/stores/auth')
    useAuthStore().logout()
  } catch {
    clearTokens()
  }
}

function isAuthEndpoint(url = '') {
  return url.includes('/customers/auth/login/') || url.includes('/customers/auth/refresh/')
}

async function refreshAccessToken() {
  const refresh = getRefreshToken()
  if (!refresh) {
    throw new Error('No refresh token')
  }
  try {
    const response = await axios.post(
      `${API_BASE_URL}/customers/auth/refresh/`,
      { refresh },
    )
    const { code, data, message } = response.data
    if (code !== 0) {
      const err = new Error(message || 'Token refresh failed')
      err.response = { status: 401, data: { code } }
      throw err
    }
    setTokens(data.access, data.refresh || refresh)
    return data.access
  } catch (error) {
    if (!error.response && error.message) {
      error.isNetworkError = true
    }
    throw error
  }
}

async function promptLoginRequired(payload) {
  const { useLoginGateStore } = await import('@/stores/loginGate')
  useLoginGateStore().open({ redirect: `${window.location.pathname}${window.location.search}` })
  return Promise.reject(payload)
}

/** 仅在 access 过期或缺失时续期；网络失败且 access 仍有效时不踢人 */
export async function trySilentRefresh(options = {}) {
  const { force = false } = options

  if (!getRefreshToken()) {
    return false
  }

  if (!force && !needsTokenRefresh()) {
    return true
  }

  try {
    await ensureFreshAccessToken()
    return true
  } catch {
    if (getAccessToken() && !isAccessTokenExpired()) {
      return true
    }
    return false
  }
}

request.interceptors.request.use(
  (config) => {
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
    const payload = response.data
    if (
      payload
      && typeof payload.code === 'number'
      && payload.code !== 0
      && payload.code !== 1001
    ) {
      if (payload.code === LOGIN_REQUIRED_CODE) {
        return promptLoginRequired(payload)
      }
      return Promise.reject(payload)
    }
    return payload
  },
  async (error) => {
    const originalRequest = error.config
    const status = error.response?.status
    const responseData = error.response?.data

    if (originalRequest?.skipErrorHandler) {
      const payload =
        responseData && typeof responseData === 'object'
          ? responseData
          : { message: error.message || t('common.networkError') }
      return Promise.reject(payload)
    }

    if (status === 401 && originalRequest) {
      if (isAuthEndpoint(originalRequest.url)) {
        if (shouldClearSessionAfterRefreshFailure(error)) {
          await clearSessionSilently()
        }
        return Promise.reject(responseData || error)
      }

      if (originalRequest._retry) {
        if (shouldClearSessionAfterRefreshFailure(error)) {
          await clearSessionSilently()
        }
        return Promise.reject(responseData || error)
      }

      if (!getRefreshToken()) {
        await clearSessionSilently()
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

      try {
        const newToken = await ensureFreshAccessToken()
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return request(originalRequest)
      } catch (refreshError) {
        return Promise.reject(refreshError)
      }
    }

    if (responseData?.code === LOGIN_REQUIRED_CODE) {
      return promptLoginRequired(responseData)
    }

    const message = responseData?.message || error.message || t('common.networkError')
    if (!originalRequest?.skipErrorHandler) {
      toastError(message)
    }
    return Promise.reject(responseData || { message })
  },
)

export default request
