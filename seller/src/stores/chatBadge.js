import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getChatUnreadSummary } from '@/api/chat'

export const useChatBadgeStore = defineStore('chatBadge', () => {
  const unreadTotal = ref(0)
  const unrepliedConversations = ref(0)
  let pollTimer = null

  async function refresh() {
    try {
      const res = await getChatUnreadSummary()
      const data = res.data || {}
      unreadTotal.value = data.unread_total || 0
      unrepliedConversations.value = data.unreplied_conversations || 0
      return data
    } catch {
      return null
    }
  }

  function startPolling(intervalMs = 15000) {
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
    return count > 99 ? '99+' : String(count)
  }

  return {
    unreadTotal,
    unrepliedConversations,
    refresh,
    startPolling,
    stopPolling,
    formatBadge,
  }
})
