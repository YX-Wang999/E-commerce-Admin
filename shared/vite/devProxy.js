/** Shared Vite dev-server proxy for Django API + WebSocket. */

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const DEFAULT_BACKEND = 'http://127.0.0.1:8000'

const BENIGN_WS_ERROR_CODES = new Set(['ECONNABORTED', 'ECONNRESET', 'EPIPE', 'ETIMEDOUT'])

function isBenignWsError(error) {
  if (!error) return false
  if (error.code && BENIGN_WS_ERROR_CODES.has(error.code)) return true
  const message = String(error.message || '')
  return /ECONNABORTED|ECONNRESET|EPIPE/i.test(message)
}

function isConnectionRefused(error) {
  if (!error) return false
  if (error.code === 'ECONNREFUSED') return true
  return /ECONNREFUSED/i.test(String(error.message || ''))
}

/** Read adminAPI/.env so local dev proxy matches run-dev.bat port. */
export function resolveDevBackendUrl() {
  if (process.env.VITE_DEV_BACKEND) {
    return process.env.VITE_DEV_BACKEND
  }
  const envPath = path.resolve(__dirname, '../../adminAPI/.env')
  if (!fs.existsSync(envPath)) {
    return DEFAULT_BACKEND
  }
  const text = fs.readFileSync(envPath, 'utf8')
  const portMatch = text.match(/^BACKEND_PORT=(\d+)/m)
  if (!portMatch) {
    return DEFAULT_BACKEND
  }
  const bindMatch = text.match(/^BACKEND_BIND=(.+)$/m)
  const host = (bindMatch ? bindMatch[1].trim() : '127.0.0.1') || '127.0.0.1'
  return `http://${host}:${portMatch[1]}`
}

function backendStartHint(backend) {
  return `Backend unreachable (${backend}). Start: cd adminAPI && run-dev.bat`
}

function sendProxyError(res, message) {
  if (!res || res.headersSent || res.writableEnded) return
  if (typeof res.writeHead === 'function') {
    res.writeHead(502, { 'Content-Type': 'text/plain; charset=utf-8' })
    res.end(message)
    return
  }
  if (typeof res.end === 'function' && !res.destroyed) {
    try {
      res.end(message)
    } catch {
      // Socket may already be closed during WS proxy failures.
    }
  }
}

function attachHttpProxyHandlers(proxy, backend) {
  proxy.on('error', (error, _req, res) => {
    if (isBenignWsError(error)) return
    const hint = isConnectionRefused(error)
      ? backendStartHint(backend)
      : `Proxy error: ${error?.message || error}`
    console.warn('[dev-proxy] http error:', hint)
    sendProxyError(res, hint)
  })
}

function attachWsProxyHandlers(proxy, backend) {
  proxy.on('error', (error, _req, res) => {
    if (isBenignWsError(error)) return
    const hint = isConnectionRefused(error)
      ? backendStartHint(backend)
      : `WebSocket proxy error: ${error?.message || error}`
    console.warn('[dev-proxy] ws error:', hint)
    sendProxyError(res, hint)
  })

  proxy.on('proxyReqWs', (_proxyReq, _req, socket) => {
    socket.on('error', (error) => {
      if (isBenignWsError(error)) return
    })
  })

  proxy.on('close', () => {
    // noop — avoid unhandled close noise during HMR / tab refresh
  })
}

export function createDevProxy(backend = resolveDevBackendUrl()) {
  return {
    '/api': {
      target: backend,
      changeOrigin: true,
      configure: (proxy) => attachHttpProxyHandlers(proxy, backend),
    },
    '/media': {
      target: backend,
      changeOrigin: true,
      configure: (proxy) => attachHttpProxyHandlers(proxy, backend),
    },
    '/ws': {
      target: backend,
      ws: true,
      changeOrigin: true,
      configure: (proxy) => attachWsProxyHandlers(proxy, backend),
    },
  }
}
