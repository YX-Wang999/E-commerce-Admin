import { onBeforeUnmount, watch } from 'vue'
import { showNotify } from 'vant'
import { createBadgePolling } from '@shared/composables/useBadgePolling.js'
import { initTitleAlert, clearTitleAlert } from '@shared/utils/titleAlert.js'
import { useNotifyWebSocket } from '@/composables/useNotifyWebSocket'
import { useAuthStore } from '@/stores/auth'
import { useCartStore } from '@/stores/cart'
import { useNotificationStore } from '@/stores/notification'
/** Mall hot-reload: WebSocket events + polling fallback when disconnected. */
export function useHotReload() {
  const authStore = useAuthStore()
  const cartStore = useCartStore()
  const notificationStore = useNotificationStore()

  function showPopup(payload) {
    showNotify({
      type: 'primary',
      message: payload.title || '新通知',
      description: payload.content,
      duration: 5000,
    })
  }

  async function refreshAllBadges() {
    await notificationStore.refreshUnread()
    await cartStore.fetchCart()
  }

  function handleWsPayload(payload) {
    if (!payload?.type) return

    if (payload.type === 'notification') {
      notificationStore.handleWsPayload(payload)
      if (payload.need_popup) {
        showPopup(payload)
      }
      return
    }

    if (payload.type === 'cart_update') {
      void cartStore.fetchCart()
    }
  }

  const { connect, disconnect, isConnected } = useNotifyWebSocket(handleWsPayload, {
    onConnected: refreshAllBadges,
  })

  const badgePolling = createBadgePolling({
    isConnected: () => isConnected.value,
    pollFn: refreshAllBadges,
    intervalMs: 30000,
  })

  function syncSession(loggedIn) {
    if (loggedIn) {
      initTitleAlert()
      void cartStore.fetchCart()
      void notificationStore.refreshUnread()
      connect()
      badgePolling.start()
    } else {
      cartStore.loadGuestCart()
      notificationStore.unreadCount = 0
      clearTitleAlert()
      disconnect()
      badgePolling.stop()
    }
  }

  watch(
    () => authStore.isLoggedIn,
    (loggedIn) => syncSession(loggedIn),
    { immediate: true },
  )

  onBeforeUnmount(() => {
    disconnect()
    badgePolling.stop()
  })

  return { isConnected }
}
