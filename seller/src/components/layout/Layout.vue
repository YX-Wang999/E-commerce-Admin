<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessageBox } from 'element-plus'
import { Expand, Fold } from '@element-plus/icons-vue'
import Sidebar from './Sidebar.vue'
import MobileTopBar from './MobileTopBar.vue'
import MobileTabBar from './MobileTabBar.vue'
import AppealReplyDrawer from '@/components/appeal/AppealReplyDrawer.vue'
import NotificationBell from '@/components/NotificationBell.vue'
import LocaleSwitcher from '@/components/LocaleSwitcher.vue'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { useNotifyStore } from '@/stores/notify'
import { useNotificationStore } from '@/stores/notification'
import { useChatBadgeStore } from '@/stores/chatBadge'
import { useComplaintBadgeStore } from '@/stores/complaintBadge'
import { useNotifyWebSocket } from '@/composables/useNotifyWebSocket'
import { createBadgePolling } from '@shared/composables/useBadgePolling.js'
import { flashTitleAlert, syncTitleUnread } from '@shared/utils/titleAlert.js'
import { useMenuTitle } from '@/i18n'
import { useScrollHeader } from '@shared/composables/useScrollHeader.js'

const MOBILE_TAB_ROUTES = new Set(['Dashboard', 'Orders', 'Products', 'Chat', 'SettingsProfile'])

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const menuTitle = useMenuTitle()
const appStore = useAppStore()
const authStore = useAuthStore()
const notifyStore = useNotifyStore()
const notificationStore = useNotificationStore()
const chatBadgeStore = useChatBadgeStore()
const complaintBadgeStore = useComplaintBadgeStore()

const toastVisible = ref(false)
const toastPayload = ref(null)
const mobileMainRef = ref(null)
let toastTimer = null

const pageTitle = computed(() => {
  if (route.meta?.titleKey) {
    return t(route.meta.titleKey)
  }
  const normalized = route.path === '/' ? '/dashboard' : route.path.replace(/\/$/, '')
  return menuTitle(normalized, t('seller.brandTitle'))
})

const showMobileTabBar = computed(
  () => appStore.isMobile && MOBILE_TAB_ROUTES.has(String(route.name)),
)

const { headerVisible } = useScrollHeader(mobileMainRef)

const staffRoleLabel = computed(() => {
  const map = {
    owner: t('seller.staffRoleOwner'),
    manager: t('seller.staffRoleManager'),
    staff: t('seller.staffRoleStaff'),
  }
  return map[authStore.staffRole] || authStore.staffRole
})

function showToast(payload) {
  toastPayload.value = payload
  toastVisible.value = true
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toastVisible.value = false
  }, 8000)
}

async function refreshAllBadges() {
  await notificationStore.refreshUnread()
  await notifyStore.refreshSummary()
  await chatBadgeStore.refresh()
  await complaintBadgeStore.refresh()
}

function handleWsPayload(payload) {
  notifyStore.handleWsPayload(payload)
  notificationStore.handleWsPayload(payload)
  if (payload?.type === 'chat_message') {
    flashTitleAlert()
    chatBadgeStore.refresh()
    showToast(payload)
    return
  }
  if (payload?.type === 'notification' && payload.need_popup) {
    showToast({
      title: payload.title,
      content: payload.content,
      type: 'notification',
      related_url: payload.related_url,
    })
  }
  if (payload?.type === 'appeal_reply') {
    showToast(payload)
  }
}

const { isConnected } = useNotifyWebSocket(handleWsPayload, { onConnected: refreshAllBadges })

const badgePolling = createBadgePolling({
  isConnected: () => isConnected.value,
  pollFn: refreshAllBadges,
  intervalMs: 30000,
})

const titleUnreadTotal = computed(
  () => (notificationStore.unreadCount || 0) + (notifyStore.unreadCount || 0),
)

watch(titleUnreadTotal, (total) => syncTitleUnread(total), { immediate: true })

function openFromToast() {
  const payload = toastPayload.value
  toastVisible.value = false
  if (payload?.type === 'chat_message') {
    const query = payload.conversation_id
      ? { conversation_id: String(payload.conversation_id) }
      : undefined
    router.push({ path: '/chat', query })
    return
  }
  if (payload?.type === 'notification' && payload.related_url) {
    router.push(payload.related_url)
    return
  }
  if (payload?.appeal_id) {
    notifyStore.openAppealDrawer(payload.appeal_id, payload.inbox_id)
  }
}

function openAppealInbox() {
  const latest = notifyStore.latestReply
  if (latest?.appeal_id) {
    notifyStore.openAppealDrawer(latest.appeal_id, latest.id)
    return
  }
  notifyStore.refreshSummary()
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm(t('seller.logoutConfirm'), t('common.tip'), {
      type: 'warning',
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
    })
    authStore.logout()
    router.push('/login')
  } catch {
    // cancelled
  }
}

function handleResize() {
  appStore.applyViewport(window.innerWidth)
}

onMounted(() => {
  appStore.applyViewport(window.innerWidth)
  window.addEventListener('resize', handleResize, { passive: true })
  void refreshAllBadges()
  chatBadgeStore.startPolling()
  complaintBadgeStore.startPolling()
  badgePolling.start()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (toastTimer) clearTimeout(toastTimer)
  chatBadgeStore.stopPolling()
  complaintBadgeStore.stopPolling()
  badgePolling.stop()
})
</script>

<template>
  <div v-if="appStore.isMobile" class="seller-mobile-shell">
    <MobileTopBar :visible="headerVisible" :page-title="pageTitle" />

    <main
      ref="mobileMainRef"
      class="seller-mobile-main"
      :class="{ 'has-tabbar': showMobileTabBar }"
    >
      <router-view />
    </main>

    <MobileTabBar v-if="showMobileTabBar" />

    <AppealReplyDrawer />

    <transition name="toast-fade">
      <div v-if="toastVisible && toastPayload" class="appeal-toast" @click="openFromToast">
        <div class="toast-title">{{ toastPayload.title }}</div>
        <div class="toast-content">{{ toastPayload.content }}</div>
        <div class="toast-action">
          {{ toastPayload.type === 'chat_message' ? t('seller.toastClickChat') : t('seller.toastClickReply') }}
        </div>
      </div>
    </transition>
  </div>

  <el-container v-else class="seller-layout">
    <el-aside :width="appStore.sidebarCollapsed ? '64px' : '220px'" class="seller-aside">
      <div class="brand">
        <span v-if="!appStore.sidebarCollapsed">🏪 {{ t('seller.brandTitle') }}</span>
        <span v-else>🏪</span>
      </div>
      <Sidebar :collapsed="appStore.sidebarCollapsed" />
    </el-aside>

    <el-container>
      <el-header class="seller-header">
        <div class="header-left">
          <el-button text @click="appStore.toggleSidebar()">
            <el-icon><component :is="appStore.sidebarCollapsed ? Expand : Fold" /></el-icon>
          </el-button>
          <span class="page-title">{{ pageTitle }}</span>
        </div>
        <div class="header-right">
          <LocaleSwitcher />
          <NotificationBell />
          <span class="tenant-name">{{ authStore.tenant?.name || t('seller.defaultTenant') }}</span>
          <el-tag size="small" type="info">{{ staffRoleLabel }}</el-tag>
          <span class="user-name">{{ authStore.user?.nickname || authStore.user?.username }}</span>
          <el-button type="danger" link @click="handleLogout">{{ t('seller.logout') }}</el-button>
        </div>
      </el-header>

      <el-main class="seller-main">
        <router-view />
      </el-main>
    </el-container>

    <AppealReplyDrawer />

    <transition name="toast-fade">
      <div v-if="toastVisible && toastPayload" class="appeal-toast" @click="openFromToast">
        <div class="toast-title">{{ toastPayload.title }}</div>
        <div class="toast-content">{{ toastPayload.content }}</div>
        <div class="toast-action">
          {{ toastPayload.type === 'chat_message' ? t('seller.toastClickChat') : t('seller.toastClickReply') }}
        </div>
      </div>
    </transition>
  </el-container>
</template>

<style scoped>
.seller-mobile-shell {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f5f7fa;
}

.seller-mobile-main {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding: 12px;
}

.seller-mobile-main.has-tabbar {
  padding-bottom: calc(62px + env(safe-area-inset-bottom, 0px));
}

.seller-layout {
  min-height: 100vh;
}

.seller-aside {
  background: #001529;
  color: #fff;
  transition: width 0.2s;
  overflow: hidden;
}

.brand {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.seller-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  height: 56px;
  padding: 0 20px;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
}

.tenant-name {
  color: #606266;
  font-size: 14px;
}

.user-name {
  color: #303133;
  font-size: 14px;
}

.seller-main {
  padding: 20px;
  background: #f5f7fa;
}

.appeal-toast {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 4000;
  width: 320px;
  padding: 16px;
  background: #fff;
  border: 2px solid #f56c6c;
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(245, 108, 108, 0.28);
  cursor: pointer;
}

.toast-title {
  font-weight: 700;
  color: #c45656;
  margin-bottom: 8px;
}

.toast-content {
  color: #606266;
  font-size: 13px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.toast-action {
  margin-top: 10px;
  font-size: 12px;
  color: #409eff;
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: all 0.25s ease;
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateY(12px);
}
</style>

