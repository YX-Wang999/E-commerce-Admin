import { onBeforeUnmount, ref, watch } from 'vue'
import { buildChatWsUrl } from '@/utils/websocket'

export function useChatWebSocket(conversationIdRef, handlers = {}) {
  const status = ref('closed')
  const socketRef = ref(null)
  let typingTimer = null

  function connect() {
    const conversationId = conversationIdRef.value
    if (!conversationId) return

    disconnect()
    const url = buildChatWsUrl(conversationId)
    const socket = new WebSocket(url)
    socketRef.value = socket
    status.value = 'connecting'

    socket.onopen = () => {
      status.value = 'open'
      handlers.onOpen?.()
      socket.send(JSON.stringify({ type: 'read' }))
    }

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        if (payload.type === 'message') {
          handlers.onMessage?.(payload.data)
        } else if (payload.type === 'typing') {
          handlers.onTyping?.(payload.data)
        } else if (payload.type === 'error') {
          handlers.onError?.(payload.message)
        } else if (payload.type === 'staff_offline') {
          handlers.onStaffOffline?.(payload.message)
        }
      } catch {
        handlers.onError?.('消息解析失败')
      }
    }

    socket.onclose = () => {
      status.value = 'closed'
      handlers.onClose?.()
    }

    socket.onerror = () => {
      status.value = 'error'
      handlers.onError?.('连接异常')
    }
  }

  function disconnect() {
    if (socketRef.value) {
      socketRef.value.close()
      socketRef.value = null
    }
    status.value = 'closed'
  }

  function sendMessage(content) {
    const text = (content || '').trim()
    if (!text || !socketRef.value || socketRef.value.readyState !== WebSocket.OPEN) {
      return false
    }
    socketRef.value.send(JSON.stringify({ type: 'message', content: text }))
    return true
  }

  function sendTyping(typing = true) {
    if (!socketRef.value || socketRef.value.readyState !== WebSocket.OPEN) return
    socketRef.value.send(JSON.stringify({ type: 'typing', typing }))
  }

  function notifyTyping() {
    sendTyping(true)
    clearTimeout(typingTimer)
    typingTimer = setTimeout(() => sendTyping(false), 1200)
  }

  watch(
    conversationIdRef,
    (id) => {
      if (id) connect()
      else disconnect()
    },
    { immediate: true },
  )

  onBeforeUnmount(() => {
    clearTimeout(typingTimer)
    disconnect()
  })

  return {
    status,
    connect,
    disconnect,
    sendMessage,
    notifyTyping,
  }
}
