import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getOrderPendingSummary } from '@/api/order'

const ORDER_LIST_PATH = '/orders/list'
const REFUND_LIST_PATH = '/orders/refund'

export const useOrderBadgeStore = defineStore('orderBadge', () => {
  const pendingShipmentCount = ref(0)
  const cancelingCount = ref(0)
  const pendingRefundCount = ref(0)
  let pollTimer = null

  async function refresh() {
    try {
      const res = await getOrderPendingSummary()
      pendingShipmentCount.value = res.data?.pending_shipment_count || 0
      cancelingCount.value = res.data?.canceling_count || 0
      pendingRefundCount.value = res.data?.pending_refund_count || 0
      return res.data
    } catch {
      return null
    }
  }

  function startPolling(intervalMs = 30000) {
    stopPolling()
    refresh()
    pollTimer = window.setInterval(refresh, intervalMs)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  function formatBadge(count) {
    if (!count || count <= 0) return ''
    return count > 99 ? '99+' : count
  }

  function getBadgeForPath(path) {
    if (path === ORDER_LIST_PATH) {
      return formatBadge(pendingShipmentCount.value + cancelingCount.value)
    }
    if (path === REFUND_LIST_PATH) {
      return formatBadge(pendingRefundCount.value)
    }
    return ''
  }

  return {
    pendingShipmentCount,
    cancelingCount,
    pendingRefundCount,
    refresh,
    startPolling,
    stopPolling,
    getBadgeForPath,
  }
})
