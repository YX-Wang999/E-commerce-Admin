import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getNotifications, getUnreadCount, markAllRead, markAsRead } from '@/api/notification'
import { flashTitleAlert, syncTitleUnread } from '@shared/utils/titleAlert.js'

export const useNotificationStore = defineStore('notification', () => {
  const unreadCount = ref(0)
  const items = ref([])
  const loading = ref(false)

  function applyTitle() {
    syncTitleUnread(unreadCount.value)
  }

  async function refreshUnread() {
    try {
      const res = await getUnreadCount()
      unreadCount.value = res.data?.count || 0
    } catch {
      unreadCount.value = 0
    }
    applyTitle()
  }

  async function fetchList(limit = 20) {
    loading.value = true
    try {
      const res = await getNotifications({ page: 1, page_size: limit })
      items.value = res.data?.results || res.data || []
    } catch {
      items.value = []
    } finally {
      loading.value = false
    }
  }

  async function readItem(item) {
    if (!item?.id || item.is_read) return
    await markAsRead(item.id)
    item.is_read = true
    if (unreadCount.value > 0) unreadCount.value -= 1
    applyTitle()
  }

  async function readAll() {
    await markAllRead()
    items.value.forEach((item) => {
      item.is_read = true
    })
    unreadCount.value = 0
    applyTitle()
  }

  function handleWsPayload(payload) {
    if (payload?.type !== 'notification') return
    flashTitleAlert()
    unreadCount.value += 1
    applyTitle()
    items.value.unshift({
      id: payload.notification_id,
      title: payload.title,
      content: payload.content,
      type: payload.notification_type,
      related_url: payload.related_url,
      related_id: payload.related_id,
      is_read: false,
      created_at: payload.timestamp,
    })
  }

  function formatBadge(count) {
    if (!count || count <= 0) return ''
    return count > 99 ? '99+' : String(count)
  }

  return {
    unreadCount,
    items,
    loading,
    refreshUnread,
    fetchList,
    readItem,
    readAll,
    handleWsPayload,
    formatBadge,
  }
})
