import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getOrderSummary } from '@/api/order'

export const useOrderSummaryStore = defineStore('orderSummary', () => {
  const summary = ref({
    pending_count: 0,
    paid_count: 0,
    shipped_count: 0,
    pending_review_count: 0,
    aftersale_count: 0,
  })

  async function refresh() {
    try {
      const res = await getOrderSummary()
      summary.value = {
        pending_count: res.data?.pending_count || 0,
        paid_count: res.data?.paid_count || 0,
        shipped_count: res.data?.shipped_count || 0,
        pending_review_count: res.data?.pending_review_count || 0,
        aftersale_count: res.data?.aftersale_count || 0,
      }
      return summary.value
    } catch {
      return summary.value
    }
  }

  function badgeForKey(key) {
    const map = {
      pending: summary.value.pending_count,
      paid: summary.value.paid_count,
      shipped: summary.value.shipped_count,
      pending_review: summary.value.pending_review_count,
      aftersale: summary.value.aftersale_count,
    }
    const count = map[key] || 0
    if (!count || count <= 0) return ''
    return count > 99 ? '99+' : count
  }

  return {
    summary,
    refresh,
    badgeForKey,
  }
})
