import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getApprovalSummary } from '@/api/approval'

export const useApprovalBadgeStore = defineStore('approvalBadge', () => {
  const pendingTotal = ref(0)

  async function refresh() {
    try {
      const res = await getApprovalSummary()
      pendingTotal.value = res.data?.pending_total || 0
    } catch {
      pendingTotal.value = 0
    }
  }

  function formatBadge(count) {
    if (!count || count <= 0) return ''
    return count > 99 ? '99+' : String(count)
  }

  function getBadgeForPath(path) {
    if (path === '/approvals') {
      return formatBadge(pendingTotal.value)
    }
    return ''
  }

  return {
    pendingTotal,
    refresh,
    formatBadge,
    getBadgeForPath,
  }
})
