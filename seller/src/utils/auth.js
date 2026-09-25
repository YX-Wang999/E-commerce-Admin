const ACCESS_TOKEN_KEY = 'seller_access_token'
const REFRESH_TOKEN_KEY = 'seller_refresh_token'
const TENANT_CODE_KEY = 'seller_tenant_code'
const TENANT_INFO_KEY = 'seller_tenant_info'

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY) || ''
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY) || ''
}

export function getTenantCode() {
  return localStorage.getItem(TENANT_CODE_KEY) || ''
}

export function getTenantInfo() {
  try {
    const raw = localStorage.getItem(TENANT_INFO_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function setTokens(access, refresh) {
  localStorage.setItem(ACCESS_TOKEN_KEY, access)
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
}

export function setTenantCode(code) {
  if (code) {
    localStorage.setItem(TENANT_CODE_KEY, code)
  } else {
    localStorage.removeItem(TENANT_CODE_KEY)
  }
}

export function setTenantInfo(tenant) {
  if (tenant) {
    localStorage.setItem(TENANT_INFO_KEY, JSON.stringify(tenant))
  } else {
    localStorage.removeItem(TENANT_INFO_KEY)
  }
}

export function clearAuthStorage() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(TENANT_CODE_KEY)
  localStorage.removeItem(TENANT_INFO_KEY)
}

export function isLoggedIn() {
  return Boolean(getAccessToken() && getTenantCode())
}
