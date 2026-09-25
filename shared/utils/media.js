/** Shared media URL resolver for admin / seller / customer frontends. */

import { resolveApiOrigin } from './apiBase.js'

const API_ORIGIN = resolveApiOrigin(
  typeof import.meta !== 'undefined' ? import.meta.env?.VITE_API_ORIGIN : '',
)

const MEDIA_SCOPES = ['products', 'brands', 'reviews', 'complaints']

function fixMalformedProtocol(path) {
  if (/^https?:\/[^/]/i.test(path)) {
    return path.replace(/^(https?):\/([^/])/, '$1://$2')
  }
  if (/^https?:[^/]/i.test(path)) {
    return path.replace(/^(https?):([^/])/, '$1://$2')
  }
  return path
}

function normalizeMediaPath(url) {
  if (!url) return ''

  const queryIndex = url.indexOf('?')
  const query = queryIndex >= 0 ? url.slice(queryIndex) : ''
  let path = queryIndex >= 0 ? url.slice(0, queryIndex) : url

  path = fixMalformedProtocol(path)

  // Strip backend absolute URLs (127.0.0.1:8002, server IP, etc.) → /media/...
  if (/^https?:\/\//i.test(path)) {
    const mediaIdx = path.indexOf('/media/')
    if (mediaIdx >= 0) {
      path = path.slice(mediaIdx)
    } else {
      return `${path}${query}`
    }
  }

  if (!path.startsWith('/')) {
    const stripped = path.replace(/^media\//, '')
    path = `/media/${stripped.replace(/^\/+/, '')}`
  } else if (!path.startsWith('/media/')) {
    const scopePrefix = MEDIA_SCOPES.find((scope) => path.startsWith(`/${scope}/`))
    if (scopePrefix) {
      path = `/media${path}`
    }
  }

  return `${path}${query}`
}

function resolveMediaOrigin() {
  if (typeof window !== 'undefined' && window.location?.origin) {
    return window.location.origin
  }
  return API_ORIGIN
}

/** Resolve API media paths to a browser-loadable URL, preserving ?v= cache params. */
export function resolveImageUrl(url) {
  const fullPath = normalizeMediaPath(url)
  if (!fullPath) return ''

  const pathOnly = fullPath.split('?')[0]
  if (/^https?:\/\//i.test(pathOnly)) {
    return fullPath
  }

  if (!pathOnly.startsWith('/media/')) {
    return fullPath
  }

  const origin = resolveMediaOrigin()
  if (origin) {
    return `${origin}${fullPath}`
  }
  return fullPath
}
