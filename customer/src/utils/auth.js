const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

function decodeJwtPayload(token) {
  try {
    const segment = token.split('.')[1]
    if (!segment) return null
    const base64 = segment.replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(atob(base64))
  } catch {
    return null
  }
}

/** access 是否已过期（默认预留 30s 时钟偏差） */
export function isAccessTokenExpired(token = getAccessToken(), skewSeconds = 30) {
  if (!token) return true
  const payload = decodeJwtPayload(token)
  if (!payload?.exp) return false
  return payload.exp * 1000 <= Date.now() + skewSeconds * 1000
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY) || ''
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY) || ''
}

export function setTokens(access, refresh) {
  localStorage.setItem(ACCESS_TOKEN_KEY, access)
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

/** localStorage 中是否存有任意 token */
export function hasSession() {
  return Boolean(getAccessToken() || getRefreshToken())
}

/** 是否视为已登录：access 有效，或仍有 refresh 可续期 */
export function isLoggedIn() {
  const access = getAccessToken()
  if (access && !isAccessTokenExpired(access)) {
    return true
  }
  return Boolean(getRefreshToken())
}

/** 是否需要向服务端 refresh（access 缺失或已过期） */
export function needsTokenRefresh() {
  if (!getRefreshToken()) return false
  const access = getAccessToken()
  return !access || isAccessTokenExpired(access)
}
