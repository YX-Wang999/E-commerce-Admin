import { ref } from 'vue'
import { defineStore } from 'pinia'
import { getComplaintSummary } from '@/api/complaints'
import { getFeedbackSummary } from '@/api/feedback'

export const useComplaintBadgeStore = defineStore('complaintBadge', () => {
  const pendingCount = ref(0)
  const feedbackPendingCount = ref(0)
  let pollTimer = null

  async function refresh() {
    try {
      const [complaintRes, feedbackRes] = await Promise.all([
        getComplaintSummary(),
        getFeedbackSummary(),
      ])
      pendingCount.value = complaintRes.data?.pending_count || 0
      feedbackPendingCount.value = feedbackRes.data?.pending_count || 0
    } catch {
      pendingCount.value = 0
      feedbackPendingCount.value = 0
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
    if (path === '/orders/refunds') {
      const total = (pendingCount.value || 0) + (feedbackPendingCount.value || 0)
      return formatBadge(total)
    }
    return ''
  }

  return { pendingCount, feedbackPendingCount, refresh, startPolling, stopPolling, getBadgeForPath }
})
