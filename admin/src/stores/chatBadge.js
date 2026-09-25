import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getChatUnreadSummary } from '@/api/chat'

const CUSTOMER_CHAT_PATH = '/customers/chat'
const MERCHANT_CHAT_PATH = '/tenants/chat'
const MERCHANT_APPEALS_PATH = '/tenants/appeals'
const MANAGER_ROLES = new Set(['cs_manager', 'ops_manager', 'ops_director', 'super_admin'])

export const useChatBadgeStore = defineStore('chatBadge', () => {
  const unreadTotal = ref(0)
  const unrepliedConversations = ref(0)
  const customerUnreadTotal = ref(0)
  const merchantUnreadTotal = ref(0)
  const pendingTenantAppeals = ref(0)
  let pollTimer = null

  async function refresh() {
    try {
      const res = await getChatUnreadSummary()
      const data = res.data || {}
      customerUnreadTotal.value = data.customer_unread_total || 0
      merchantUnreadTotal.value = data.merchant_unread_total || 0
      pendingTenantAppeals.value = data.pending_tenant_appeals || 0
      unreadTotal.value = data.unread_total || 0
      unrepliedConversations.value = data.unreplied_conversations || 0
      return data
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

  function getParentDirectoryBadge(path) {
    if (path === '/customers') {
      return formatBadge(customerUnreadTotal.value)
    }
    if (path === '/tenants') {
      return formatBadge(merchantUnreadTotal.value)
    }
    return ''
  }

  function getBadgeForPath(path) {
    if (path === CUSTOMER_CHAT_PATH) {
      return formatBadge(customerUnreadTotal.value)
    }
    if (path === MERCHANT_CHAT_PATH) {
      return formatBadge(merchantUnreadTotal.value)
    }
    if (path === MERCHANT_APPEALS_PATH) {
      return formatBadge(pendingTenantAppeals.value)
    }
    return ''
  }

  function getDirectoryBadge(children = []) {
    let total = 0
    children.forEach((child) => {
      const badge = getBadgeForPath(child.path)
      if (!badge) return
      total += badge === '99+' ? 99 : Number(badge)
    })
    return formatBadge(total)
  }

  function isChatManager(user) {
    if (!user) return false
    if (user.is_superuser) return true
    return (user.roles || []).some((role) => MANAGER_ROLES.has(role.code))
  }

  function shouldShowManagerAlert(user, scope = 'customer') {
    if (!isChatManager(user)) return false
    const unread = scope === 'merchant' ? merchantUnreadTotal.value : customerUnreadTotal.value
    if (unread <= 0) return false
    const key = scope === 'merchant' ? 'chat_manager_alert_merchant' : 'chat_manager_alert_customer'
    const snapshot = sessionStorage.getItem(key)
    const current = String(unread)
    if (snapshot === current) return false
    return true
  }

  function markManagerAlertShown(scope = 'customer') {
    const key = scope === 'merchant' ? 'chat_manager_alert_merchant' : 'chat_manager_alert_customer'
    const unread = scope === 'merchant' ? merchantUnreadTotal.value : customerUnreadTotal.value
    sessionStorage.setItem(key, String(unread))
  }

  return {
    unreadTotal,
    unrepliedConversations,
    customerUnreadTotal,
    merchantUnreadTotal,
    pendingTenantAppeals,
    refresh,
    startPolling,
    stopPolling,
    getBadgeForPath,
    getParentDirectoryBadge,
    getDirectoryBadge,
    isChatManager,
    shouldShowManagerAlert,
    markManagerAlertShown,
  }
})
