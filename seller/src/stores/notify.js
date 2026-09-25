import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getAppealDetail, getInboxSummary, markInboxRead, replyAppeal } from '@/api/inbox'
import { flashTitleAlert } from '@shared/utils/titleAlert.js'

export const useNotifyStore = defineStore('notify', () => {
  const unreadCount = ref(0)
  const latestReply = ref(null)
  const drawerVisible = ref(false)
  const drawerAppealId = ref(null)
  const appealDetail = ref(null)
  const loading = ref(false)
  const replyText = ref('')
  const bannerVisible = ref(false)

  async function refreshSummary() {
    try {
      const res = await getInboxSummary()
      unreadCount.value = res.data?.unread_count || 0
      latestReply.value = res.data?.latest_appeal_reply || null
      bannerVisible.value = unreadCount.value > 0
      return res.data
    } catch {
      return null
    }
  }

  function handleWsPayload(payload) {
    if (payload?.type === 'chat_message') {
      return
    }
    if (payload?.type !== 'appeal_reply') return
    flashTitleAlert()
    unreadCount.value += 1
    latestReply.value = {
      id: payload.inbox_id,
      title: payload.title,
      content: payload.content,
      appeal_id: payload.appeal_id,
      created_at: payload.timestamp,
      is_read: false,
    }
    bannerVisible.value = true
    if (drawerVisible.value && drawerAppealId.value === payload.appeal_id) {
      loadAppeal(payload.appeal_id)
    }
  }

  async function openAppealDrawer(appealId, inboxId = null) {
    drawerAppealId.value = appealId
    drawerVisible.value = true
    bannerVisible.value = false
    if (inboxId) {
      try {
        await markInboxRead(inboxId)
        if (unreadCount.value > 0) unreadCount.value -= 1
      } catch {
        // ignore
      }
    }
    await loadAppeal(appealId)
  }

  async function loadAppeal(appealId) {
    loading.value = true
    try {
      const res = await getAppealDetail(appealId)
      appealDetail.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function submitReply() {
    const content = replyText.value.trim()
    if (!content || !drawerAppealId.value) return false
    await replyAppeal(drawerAppealId.value, { content })
    replyText.value = ''
    await loadAppeal(drawerAppealId.value)
    return true
  }

  function closeDrawer() {
    drawerVisible.value = false
    drawerAppealId.value = null
    appealDetail.value = null
    replyText.value = ''
  }

  return {
    unreadCount,
    latestReply,
    drawerVisible,
    drawerAppealId,
    appealDetail,
    loading,
    replyText,
    bannerVisible,
    refreshSummary,
    handleWsPayload,
    openAppealDrawer,
    loadAppeal,
    submitReply,
    closeDrawer,
  }
})
