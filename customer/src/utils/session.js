import { needsTokenRefresh } from '@/utils/auth'
import { trySilentRefresh } from '@/utils/request'

/** 商城 C 端：切回前台时，仅在 access 过期后静默续期 */
export function setupSessionKeepAlive() {
  const renew = () => {
    if (needsTokenRefresh()) {
      trySilentRefresh().catch(() => {})
    }
  }

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      renew()
    }
  })
}
