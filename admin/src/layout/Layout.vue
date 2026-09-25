<script setup>
import { computed, onMounted, onUnmounted, provide, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessageBox } from 'element-plus'
import SidebarMenu from '@/layout/components/SidebarMenu.vue'
import AppHeader from '@/layout/components/AppHeader.vue'
import AnnouncementBanner from '@/layout/components/AnnouncementBanner.vue'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import GlobalSystemAlert from '@/components/GlobalSystemAlert.vue'
import { useAlertStore } from '@/stores/alert'
import { useChatBadgeStore } from '@/stores/chatBadge'
import { useNotificationStore } from '@/stores/notification'
import { useOrderBadgeStore } from '@/stores/orderBadge'
import { useComplaintBadgeStore } from '@/stores/complaintBadge'
import { useApprovalBadgeStore } from '@/stores/approvalBadge'
import { createBadgePolling } from '@shared/composables/useBadgePolling.js'
import { flashTitleAlert } from '@shared/utils/titleAlert.js'
import { isOrderRelatedNotification } from '@shared/utils/orderNotificationTypes.js'
import { useNotifyWebSocket } from '@/composables/useNotifyWebSocket'
import { useScrollHeader } from '@shared/composables/useScrollHeader.js'
import { useTenantStore } from '@/stores/tenant'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const appStore = useAppStore()
const authStore = useAuthStore()
const chatBadgeStore = useChatBadgeStore()
const orderBadgeStore = useOrderBadgeStore()
const complaintBadgeStore = useComplaintBadgeStore()
const tenantStore = useTenantStore()
const alertStore = useAlertStore()
const notificationStore = useNotificationStore()
const approvalBadgeStore = useApprovalBadgeStore()
const announcementBannerRef = ref(null)
const contentRef = ref(null)
const { headerVisible } = useScrollHeader(contentRef)

provide('headerScrollVisible', headerVisible)

const menus = computed(() => authStore.menus)
const activeMenu = computed(() => route.path)

const asideWidth = computed(() => {
  if (appStore.isMobile) {
    return '220px'
  }
  return appStore.sidebarCollapsed ? '64px' : '220px'
})

const menuCollapsed = computed(() => {
  if (appStore.isMobile) {
    return false
  }
  return appStore.sidebarCollapsed
})

const asideClass = computed(() => ({
  'is-mobile': appStore.isMobile,
  'is-open': appStore.mobileSidebarOpen,
  'is-collapse': appStore.sidebarCollapsed && !appStore.isMobile,
}))

function handleResize() {
  appStore.applyViewport(window.innerWidth)
}

function handleMenuSelect(path) {
  if (path && path !== route.path) {
    router.push(path)
  }
  if (appStore.isMobile) {
    appStore.closeMobileSidebar()
  }
}

function hasMenuPath(targetPath) {
  const paths = []
  function walk(items = []) {
    items.forEach((item) => {
      if (item.path) paths.push(item.path)
      if (item.children?.length) walk(item.children)
    })
  }
  walk(authStore.menus)
  return paths.includes(targetPath)
}

function hasChatMenuAccess() {
  return hasMenuPath('/customers/chat') || hasMenuPath('/tenants/chat')
}

async function maybeShowManagerAlert(scope = 'customer') {
  await chatBadgeStore.refresh()
  if (!chatBadgeStore.shouldShowManagerAlert(authStore.user, scope)) {
    return
  }
  chatBadgeStore.markManagerAlertShown(scope)
  const unread = scope === 'merchant'
    ? chatBadgeStore.merchantUnreadTotal
    : chatBadgeStore.customerUnreadTotal
  const target = scope === 'merchant' ? '/tenants/chat' : '/customers/chat'
  ElMessageBox.alert(
    t('chat.managerUnreadAlert', {
      count: chatBadgeStore.unrepliedConversations,
      messages: unread,
    }),
    t('chat.managerUnreadTitle'),
    {
      confirmButtonText: t('chat.goToWorkbench'),
      type: 'warning',
    },
  )
    .then(() => {
      router.push(target)
    })
    .catch(() => {})
}

function hasTenantMenuAccess() {
  return hasMenuPath('/tenants/list') || hasMenuPath('/system/tenants')
}

function hasComplaintMenuAccess() {
  return hasMenuPath('/customers/complaints')
}

function hasOrderMenuAccess() {
  return hasMenuPath('/orders/list') || hasMenuPath('/orders/refund')
}

function hasApprovalMenuAccess() {
  return hasMenuPath('/approvals')
}

async function refreshAllBadges() {
  await notificationStore.refreshUnread()
  if (hasApprovalMenuAccess()) {
    await approvalBadgeStore.refresh()
  }
  if (hasChatMenuAccess()) {
    await chatBadgeStore.refresh()
  }
  if (hasOrderMenuAccess()) {
    await orderBadgeStore.refresh()
  }
  if (hasComplaintMenuAccess()) {
    await complaintBadgeStore.refresh()
  }
}

function handleNotifyPayload(payload) {
  if (payload?.type === 'system_alert') {
    flashTitleAlert()
    alertStore.showSystemAlert(payload)
    chatBadgeStore.refresh()
    notificationStore.refreshUnread()
    if (payload.order_id || String(payload.target_url || '').includes('/orders')) {
      orderBadgeStore.refresh()
    }
  }
  if (payload?.type === 'notification') {
    notificationStore.handleWsPayload(payload)
    if (payload.notification_type === 'approval' || payload.notification_type === 'approval_pending') {
      approvalBadgeStore.refresh()
    }
    if (payload.need_popup) {
      flashTitleAlert()
      alertStore.showSystemAlert({
        title: payload.title,
        content: payload.content,
        target_url: payload.related_url,
        level: payload.level || 'info',
      })
    }
    if (isOrderRelatedNotification(payload.notification_type)) {
      orderBadgeStore.refresh()
    }
    if (payload.notification_type === 'complaint') {
      complaintBadgeStore.refresh()
    }
  }
  if (payload?.type === 'announcement') {
    notificationStore.refreshUnread()
    announcementBannerRef.value?.refresh?.()
  }
}

const { isConnected } = useNotifyWebSocket(handleNotifyPayload, { onConnected: refreshAllBadges })

const badgePolling = createBadgePolling({
  isConnected: () => isConnected.value,
  pollFn: refreshAllBadges,
  intervalMs: 30000,
})

watch(
  () => route.path,
  (path) => {
    if (path.startsWith('/customers/chat') || path.startsWith('/tenants/chat')) {
      chatBadgeStore.refresh()
    }
  },
)

watch(
  () => authStore.menus,
  (menus) => {
    if (menus?.length && hasChatMenuAccess()) {
      chatBadgeStore.startPolling()
      maybeShowManagerAlert('customer')
      maybeShowManagerAlert('merchant')
    } else {
      chatBadgeStore.stopPolling()
    }
    if (menus?.length && hasTenantMenuAccess()) {
      tenantStore.startStatsPolling()
    } else {
      tenantStore.stopStatsPolling()
    }
    if (menus?.length && hasOrderMenuAccess()) {
      orderBadgeStore.startPolling()
    } else {
      orderBadgeStore.stopPolling()
    }
    if (menus?.length && hasComplaintMenuAccess()) {
      complaintBadgeStore.startPolling()
    } else {
      complaintBadgeStore.stopPolling()
    }
    if (menus?.length && hasApprovalMenuAccess()) {
      approvalBadgeStore.refresh()
    }
  },
  { immediate: true },
)

onMounted(() => {
  appStore.initViewport()
  void refreshAllBadges()
  badgePolling.start()
  window.addEventListener('resize', handleResize, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  badgePolling.stop()
  chatBadgeStore.stopPolling()
  orderBadgeStore.stopPolling()
  complaintBadgeStore.stopPolling()
  tenantStore.stopStatsPolling()
})
</script>

<template>
  <el-container class="layout-container">
    <div
      v-if="appStore.isMobile && appStore.mobileSidebarOpen"
      class="mobile-mask"
      @click="appStore.closeMobileSidebar()"
    />

    <el-aside :width="asideWidth" class="layout-aside" :class="asideClass">
      <div class="logo-wrap">
        <span v-if="!menuCollapsed" class="logo-text">{{ t('layout.siteTitle') }}</span>
        <span v-else class="logo-mini">A</span>
      </div>
      <el-scrollbar class="sidebar-scroll" height="calc(100vh - 56px)">
        <el-menu
          :default-active="activeMenu"
          :collapse="menuCollapsed"
          :collapse-transition="false"
          background-color="#001529"
          text-color="#ffffffa6"
          active-text-color="#fff"
          router
          @select="handleMenuSelect"
        >
          <SidebarMenu :menus="menus" :collapsed="menuCollapsed" />
        </el-menu>
      </el-scrollbar>
    </el-aside>

    <el-container class="layout-main">
      <AppHeader />
      <AnnouncementBanner ref="announcementBannerRef" />
      <el-main class="layout-content">
        <div ref="contentRef" class="layout-scroll">
          <router-view />
        </div>
      </el-main>
    </el-container>
    <GlobalSystemAlert />
  </el-container>
</template>

<style scoped>
.layout-container {
  width: 100%;
  height: 100%;
  min-height: 100vh;
}

.layout-aside {
  flex-shrink: 0;
  height: 100vh;
  background: #001529;
  transition: width 0.3s ease, transform 0.3s ease;
  overflow: hidden;
  position: sticky;
  top: 0;
  z-index: 1001;
  display: flex;
  flex-direction: column;
}

.sidebar-scroll {
  flex: 1;
  min-height: 0;
}

.layout-aside.is-mobile {
  position: fixed;
  left: 0;
  top: 0;
  transform: translateX(-100%);
}

.layout-aside.is-mobile.is-open {
  transform: translateX(0);
}

.mobile-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 1000;
}

.logo-wrap {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo-text {
  font-size: 16px;
  white-space: nowrap;
  padding: 0 12px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.logo-mini {
  font-size: 18px;
}

.layout-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  overflow: hidden;
}

.layout-content {
  flex: 1;
  width: 100%;
  padding: 0;
  overflow: hidden;
  box-sizing: border-box;
}

.layout-scroll {
  height: 100%;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding: 16px;
  box-sizing: border-box;
}

@media (max-width: 991px) {
  .layout-scroll {
    padding: 12px;
  }
}

@media (max-width: 575px) {
  .layout-scroll {
    padding: 8px;
  }
}
</style>

<style>
.layout-aside .el-menu {
  border-right: none;
}

.layout-container.el-container {
  width: 100%;
}

.layout-main > .el-main {
  --el-main-padding: 0;
}
</style>
