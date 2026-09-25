/** Page title alert: unread count + brief 【新消息】 flash (no emoji). */

const NEW_MSG_TAG = '【新消息】'
const COUNT_PREFIX_RE = /^\(\d+\)\s/
const COUNT_PREFIX_99_RE = /^\(99\+\)\s/

let baseTitle = ''
let unreadCount = 0
let blinking = false
let blinkTimer = null
let flashTimer = null
let listenersReady = false

function stripDecorations(title) {
  let text = String(title || '').trim()
  if (text.startsWith(NEW_MSG_TAG)) {
    text = text.slice(NEW_MSG_TAG.length).trimStart()
  }
  text = text.replace(COUNT_PREFIX_99_RE, '').replace(COUNT_PREFIX_RE, '')
  return text.trim()
}

function formatCount(count) {
  if (!count || count <= 0) return ''
  return `(${count > 99 ? '99+' : count}) `
}

function buildTitle({ withNewMsg = false } = {}) {
  const countPart = formatCount(unreadCount)
  const alertPart = withNewMsg ? NEW_MSG_TAG : ''
  return `${alertPart}${countPart}${baseTitle || 'App'}`
}

function ensureListeners() {
  if (listenersReady || typeof window === 'undefined') return
  listenersReady = true

  window.addEventListener('focus', onWindowActive)
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) onWindowActive()
  })
}

function onWindowActive() {
  stopBlink()
  if (flashTimer) {
    clearTimeout(flashTimer)
    flashTimer = null
  }
  applyTitle()
}

function applyTitle(options = {}) {
  if (typeof document === 'undefined') return
  document.title = buildTitle(options)
}

function stopBlink() {
  blinking = false
  if (blinkTimer) {
    clearInterval(blinkTimer)
    blinkTimer = null
  }
}

function startBlink() {
  stopBlink()
  blinking = true
  let showNewMsg = true
  blinkTimer = window.setInterval(() => {
    if (typeof document === 'undefined') return
    document.title = showNewMsg ? buildTitle({ withNewMsg: true }) : buildTitle()
    showNewMsg = !showNewMsg
  }, 800)
}

export function captureBaseTitle() {
  if (typeof document === 'undefined') return baseTitle
  if (!baseTitle) {
    baseTitle = stripDecorations(document.title)
  }
  return baseTitle
}

export function setBaseTitle(title) {
  baseTitle = stripDecorations(title)
  applyTitle()
}

export function initTitleAlert(title) {
  ensureListeners()
  if (title) {
    setBaseTitle(title)
  } else {
    captureBaseTitle()
    applyTitle()
  }
}

/** Normal state: only unread count, e.g. "(3) 商城". */
export function syncTitleUnread(count = 0) {
  ensureListeners()
  captureBaseTitle()
  unreadCount = Math.max(0, Number(count) || 0)
  if (unreadCount === 0 && !blinking) {
    stopBlink()
  }
  if (!blinking) {
    applyTitle()
  }
}

/** New message: briefly show 【新消息】; blink when tab is in background. */
export function flashTitleAlert() {
  ensureListeners()
  captureBaseTitle()

  if (flashTimer) {
    clearTimeout(flashTimer)
    flashTimer = null
  }

  if (typeof document !== 'undefined' && document.hidden) {
    startBlink()
    return
  }

  applyTitle({ withNewMsg: true })
  flashTimer = window.setTimeout(() => {
    flashTimer = null
    if (!blinking) applyTitle()
  }, 3000)
}

export function clearTitleAlert() {
  unreadCount = 0
  stopBlink()
  if (flashTimer) {
    clearTimeout(flashTimer)
    flashTimer = null
  }
  applyTitle()
}
