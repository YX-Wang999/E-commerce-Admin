import {
  getAccessToken,
  getRefreshToken,
  hasSession,
  isLoggedIn,
  needsTokenRefresh,
} from '@/utils/auth'
import { trySilentRefresh } from '@/utils/request'

let bootstrapPromise = null

/** 应用启动时恢复登录态，须在 mount 前 await */
export function startSessionBootstrap(pinia) {
  if (bootstrapPromise) {
    return bootstrapPromise
  }

  bootstrapPromise = (async () => {
    try {
      const { useAuthStore } = await import('@/stores/auth')
      const authStore = useAuthStore(pinia)

      if (!hasSession()) {
        authStore.isLoggedIn = false
        authStore.customer = null
        authStore.token = ''
        return
      }

      authStore.token = getAccessToken()
      authStore.isLoggedIn = true

      if (needsTokenRefresh()) {
        const refreshed = await trySilentRefresh()
        if (!refreshed && !isLoggedIn()) {
          authStore.isLoggedIn = false
          authStore.customer = null
          authStore.token = ''
          return
        }
        authStore.token = getAccessToken()
        authStore.isLoggedIn = isLoggedIn()
      }

      if (isLoggedIn()) {
        await authStore.fetchProfile()
        authStore.isLoggedIn = isLoggedIn()
      }
    } catch {
      const { useAuthStore } = await import('@/stores/auth')
      const authStore = useAuthStore(pinia)
      authStore.isLoggedIn = false
      authStore.customer = null
      authStore.token = ''
    }
  })()

  return bootstrapPromise
}

export function getSessionReady() {
  return bootstrapPromise || Promise.resolve()
}
