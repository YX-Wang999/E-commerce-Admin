import { defineStore } from 'pinia'
import { ref } from 'vue'
import { flashTitleAlert } from '@shared/utils/titleAlert.js'

export const useAlertStore = defineStore('alert', () => {
  const latestAlert = ref(null)
  const visible = ref(false)
  const unreadAlerts = ref(0)

  function showSystemAlert(payload) {
    latestAlert.value = payload
    visible.value = true
    unreadAlerts.value += 1
    flashTitleAlert()
    if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
      try {
        new Notification(payload.title || '系统通知', { body: payload.content || '' })
      } catch {
        // ignore
      }
    }
  }

  function dismiss() {
    visible.value = false
  }

  function clearUnread() {
    unreadAlerts.value = 0
  }

  return {
    latestAlert,
    visible,
    unreadAlerts,
    showSystemAlert,
    dismiss,
    clearUnread,
  }
})
