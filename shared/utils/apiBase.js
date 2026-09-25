/** Normalize Vite API base URL; reject Windows paths mistaken for URLs. */

const DEFAULT_API_BASE = '/api'

function isWindowsPath(value) {
  return /^[a-zA-Z]:[\\/]/.test(value) || /^[a-zA-Z]:$/.test(value)
}

/**
 * @param {string | undefined} raw
 * @param {string} [fallback='/api']
 */
export function resolveApiBaseUrl(raw, fallback = DEFAULT_API_BASE) {
  const value = String(raw ?? '').trim()
  if (!value) return fallback

  if (isWindowsPath(value)) {
    if (typeof console !== 'undefined') {
      console.warn('[api] Invalid VITE_API_BASE_URL (Windows path ignored):', value)
    }
    return fallback
  }

  if (/^https?:\/\//i.test(value)) {
    return value.replace(/\/+$/, '') || fallback
  }

  if (value.startsWith('/') && !value.startsWith('//')) {
    return value.replace(/\/+$/, '') || fallback
  }

  if (typeof console !== 'undefined') {
    console.warn('[api] Invalid VITE_API_BASE_URL (use /api or https://...):', value)
  }
  return fallback
}

/**
 * @param {string | undefined} raw
 */
export function resolveApiOrigin(raw) {
  const value = String(raw ?? '').trim()
  if (!value) return ''

  if (isWindowsPath(value)) {
    if (typeof console !== 'undefined') {
      console.warn('[api] Invalid VITE_API_ORIGIN (Windows path ignored):', value)
    }
    return ''
  }

  if (/^https?:\/\//i.test(value)) {
    return value.replace(/\/+$/, '')
  }

  if (typeof console !== 'undefined') {
    console.warn('[api] Invalid VITE_API_ORIGIN (use https://...):', value)
  }
  return ''
}
