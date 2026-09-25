import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import i18n from '@/i18n'
import { initTitleAlert } from '@shared/utils/titleAlert.js'
import { setupSessionKeepAlive } from '@/utils/session'
import { startSessionBootstrap } from '@/utils/sessionBootstrap'
import { useCartStore } from '@/stores/cart'
import { isLoggedIn } from '@/utils/auth'

import 'vant/lib/index.css'
import '@/assets/theme.css'
import '@/assets/ui-overrides.css'
import { Lazyload } from 'vant'
import { injectDialogStyles } from '@/utils/injectDialogStyles'

injectDialogStyles()

const app = createApp(App)
const pinia = createPinia()

app.use(Lazyload)

app.use(pinia)
app.use(i18n)

async function init() {
  initTitleAlert('商城')
  try {
    await startSessionBootstrap(pinia)
  } catch {
    // 会话恢复失败不应阻塞应用挂载，避免白屏
  }

  app.use(router)
  app.mount('#app')

  setupSessionKeepAlive()
  if (isLoggedIn()) {
    useCartStore(pinia).fetchCart()
  }
}

init()
