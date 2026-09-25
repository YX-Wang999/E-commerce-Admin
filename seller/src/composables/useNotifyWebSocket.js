import { onBeforeUnmount, ref } from 'vue'
import { createNotifyWebSocket } from '@shared/composables/useNotifyWebSocketCore.js'
import { getAccessToken, getTenantCode } from '@/utils/auth'

export function buildNotifyWsUrl() {
  const token = getAccessToken() || ''
  const tenantCode = getTenantCode() || ''
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const params = new URLSearchParams({ token })
  if (tenantCode) params.set('tenant_code', tenantCode)
  return `${protocol}//${window.location.host}/ws/notify/?${params.toString()}`
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
