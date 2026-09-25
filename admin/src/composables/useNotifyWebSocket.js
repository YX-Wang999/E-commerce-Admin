import { onBeforeUnmount, ref } from 'vue'
import { createNotifyWebSocket } from '@shared/composables/useNotifyWebSocketCore.js'
import { getAccessToken } from '@/utils/auth'

export function buildNotifyWsUrl() {
  const token = getAccessToken() || ''
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/notify/?token=${encodeURIComponent(token)}`
}

export function useNotifyWebSocket(onEvent, options = {}) {
  const { onConnected } = options
  const status = ref('closed')
  const isConnected = ref(false)

  const ws = createNotifyWebSocket({
    buildUrl: buildNotifyWsUrl,
    getToken: getAccessToken,
    onEvent,
    onStatusChange: (next) => {
      status.value = next
      isConnected.value = next === 'connected'
      if (next === 'connected') {
        onConnected?.()
      }
    },
  })

  ws.start()

  onBeforeUnmount(() => ws.disconnect())

  return { status, isConnected, connect: ws.start, disconnect: ws.disconnect }
}
