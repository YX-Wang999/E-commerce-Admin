import { defineStore } from 'pinia'
import { ref } from 'vue'
import { isLoggedIn } from '@/utils/auth'
import { useAuthStore } from '@/stores/auth'
import { getSessionReady } from '@/utils/sessionBootstrap'

export const useLoginGateStore = defineStore('loginGate', () => {
  const visible = ref(false)
  const redirect = ref('/')
  let pendingResolve = null
  let pendingReject = null

  function open(options = {}) {
    redirect.value = options.redirect || '/'
    visible.value = true
    return new Promise((resolve, reject) => {
      pendingResolve = resolve
      pendingReject = reject
    })
  }

  function succeed() {
    visible.value = false
    pendingResolve?.(true)
    pendingResolve = null
    pendingReject = null
  }

  function cancel() {
    visible.value = false
    pendingReject?.('cancel')
    pendingResolve = null
    pendingReject = null
  }

  return {
    visible,
    redirect,
    open,
    succeed,
    cancel,
  }
})

/** 在需要登录的操作前调用，已登录直接通过，否则弹出登录框 */
export async function requireLogin(options = {}) {
  await getSessionReady()

  if (!isLoggedIn()) {
    const gate = useLoginGateStore()
    return gate.open(options)
  }

  const authStore = useAuthStore()
  authStore.isLoggedIn = true

  if (!authStore.customer) {
    try {
      await authStore.hydrateSession()
    } catch {
      // token 仍在则允许继续，避免误踢；401 清 token 由 request 拦截器统一处理
    }
  }

  if (!isLoggedIn()) {
    const gate = useLoginGateStore()
    return gate.open(options)
  }

  return true
}
