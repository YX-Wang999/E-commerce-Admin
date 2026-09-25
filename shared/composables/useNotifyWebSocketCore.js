/** Shared notify WebSocket lifecycle (reconnect backoff + auth close codes). */

const AUTH_CLOSE_CODES = new Set([4401, 4403])
const INITIAL_RECONNECT_MS = 5000
const MAX_RECONNECT_MS = 30000
const MAX_RECONNECT_ATTEMPTS = 10

export function createNotifyWebSocket({
  buildUrl,
  getToken,
  onEvent,
  onStatusChange,
  maxReconnectAttempts = MAX_RECONNECT_ATTEMPTS,
}) {
  let socket = null
  let reconnectTimer = null
  let reconnectAttempts = 0
  let stopped = false
  let connected = false
  let visibilityHandler = null

  function bindVisibilityReconnect() {
    if (visibilityHandler || typeof document === 'undefined') return
    visibilityHandler = () => {
      if (document.hidden || stopped || !getToken() || connected) return
      reconnectAttempts = 0
      connect()
    }
    document.addEventListener('visibilitychange', visibilityHandler)
  }

  function unbindVisibilityReconnect() {
    if (visibilityHandler && typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', visibilityHandler)
      visibilityHandler = null
    }
  }

  function setConnected(next) {
    if (connected === next) return
    connected = next
    onStatusChange?.(next ? 'connected' : 'disconnected')
  }

  function clearReconnectTimer() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  function scheduleReconnect() {
    if (stopped || !getToken()) return
    if (reconnectAttempts >= maxReconnectAttempts) {
      setConnected(false)
      return
    }

    clearReconnectTimer()
    reconnectAttempts += 1
    const delay = Math.min(
      reconnectAttempts === 1 ? INITIAL_RECONNECT_MS : 1000 * 2 ** (reconnectAttempts - 1),
      MAX_RECONNECT_MS,
    )

    reconnectTimer = window.setTimeout(() => {
      connect()
    }, delay)
  }

  function connect() {
    if (stopped) return
    if (!getToken()) {
      scheduleReconnect()
      return
    }

    if (socket) {
      socket.onclose = null
      socket.close()
      socket = null
    }

    setConnected(false)
    socket = new WebSocket(buildUrl())

    socket.onopen = () => {
      reconnectAttempts = 0
      setConnected(true)
    }

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        if (payload.type === 'connected') return
        onEvent?.(payload)
      } catch {
        // ignore malformed payloads
      }
    }

    socket.onclose = (event) => {
      socket = null
      setConnected(false)
      if (stopped) return
      if (AUTH_CLOSE_CODES.has(event.code)) {
        reconnectAttempts = 0
        return
      }
      scheduleReconnect()
    }

    socket.onerror = () => {
      // close handler performs reconnect/backoff
    }
  }

  function disconnect() {
    stopped = true
    clearReconnectTimer()
    unbindVisibilityReconnect()
    if (socket) {
      socket.onclose = null
      socket.close()
      socket = null
    }
    reconnectAttempts = 0
    setConnected(false)
  }

  function start() {
    stopped = false
    reconnectAttempts = 0
    bindVisibilityReconnect()
    connect()
  }

  function isConnected() {
    return connected
  }

  return { connect: start, disconnect, start, isConnected }
}
