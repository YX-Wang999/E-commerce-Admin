<script setup>
import { watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import LoginSheet from '@/components/auth/LoginSheet.vue'
import AppConfirmHost from '@/components/common/AppConfirmHost.vue'
import { useLoginGateStore } from '@/stores/loginGate'
import { isLoggedIn } from '@/utils/auth'

const route = useRoute()
const router = useRouter()
const loginGate = useLoginGateStore()

function stripLoginQuery() {
  if (!route.query.login && !route.query.redirect) return
  const nextQuery = { ...route.query }
  delete nextQuery.login
  delete nextQuery.redirect
  router.replace({ path: route.path, query: nextQuery })
}

function openLoginFromQuery() {
  if (route.query.login !== '1') return

  const redirect = route.query.redirect ? String(route.query.redirect) : '/'

  if (isLoggedIn()) {
    stripLoginQuery()
    if (redirect && redirect !== route.fullPath) {
      router.replace(redirect)
    }
    return
  }

  if (loginGate.visible) return

  stripLoginQuery()
  loginGate.open({ redirect }).catch(() => {})
}

watch(
  () => [route.query.login, route.query.redirect, route.path],
  openLoginFromQuery,
  { immediate: true },
)
</script>

<template>
  <router-view />
  <LoginSheet />
  <AppConfirmHost />
</template>

<style>
html {
  color-scheme: light;
}

body {
  margin: 0;
  background: var(--color-bg, #f5f5f5);
  color: var(--color-text, #333);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* Toast 样式见 assets/ui-overrides.css 与同文件下方 */
.app-toast {
  color: #fff !important;
  background: rgba(50, 50, 51, 0.92) !important;
}
.app-toast .van-toast__text,
.app-toast .van-toast__icon {
  color: #fff !important;
}
.app-toast--fail {
  background: #fff !important;
  color: #323233 !important;
  border: 1px solid #ffd6d6;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}
.app-toast--fail .van-toast__text {
  color: #323233 !important;
}
.app-toast--fail .van-toast__icon {
  color: #ee0a24 !important;
}
</style>
