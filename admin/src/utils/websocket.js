import { getAccessToken } from '@/utils/auth'

export function buildChatWsUrl(conversationId) {
  const token = getAccessToken() || ''
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/chat/${conversationId}/?token=${encodeURIComponent(token)}`
}

export function formatChatTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()
  const time = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  if (isToday) return time
  return `${date.toLocaleDateString()} ${time}`
}
