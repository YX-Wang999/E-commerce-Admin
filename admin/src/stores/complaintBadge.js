import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getComplaintStats } from '@/api/complaint'

export const useComplaintBadgeStore = defineStore('complaintBadge', () => {
  const pendingCount = ref(0)
  let pollTimer = null

  async function refresh() {
    try {
      const res = await getComplaintStats()
      pendingCount.value = res.data?.pending_count || 0
    } catch {
      pendingCount.value = 0
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
    if (path === '/customers/complaints') {
      return formatBadge(pendingCount.value)
    }
    return ''
  }

  return { pendingCount, refresh, startPolling, stopPolling, getBadgeForPath }
})
