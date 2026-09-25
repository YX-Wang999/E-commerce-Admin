<script setup>
import { computed, inject, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { confirmDialog } from '@/utils/messageBox'
import { ArrowDown, ArrowLeft, ChatLineRound, Expand, Fold, DocumentChecked } from '@element-plus/icons-vue'
import NotificationBell from '@/components/NotificationBell.vue'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { useChatBadgeStore } from '@/stores/chatBadge'
import { useApprovalBadgeStore } from '@/stores/approvalBadge'
import { useLocaleStore } from '@/stores/locale'
import { useRoleLabel } from '@/composables/useRoleLabel'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const appStore = useAppStore()
const authStore = useAuthStore()
const chatBadgeStore = useChatBadgeStore()
const approvalBadgeStore = useApprovalBadgeStore()
const localeStore = useLocaleStore()
const { roleLabels } = useRoleLabel()

const headerVisible = inject('headerScrollVisible', ref(true))

const nickname = computed(() => authStore.user?.nickname || authStore.user?.username || t('common.user'))
const roleSummary = computed(() => roleLabels(authStore.user?.roles))
const avatarText = computed(() => nickname.value.slice(0, 1).toUpperCase())
const currentLocaleLabel = computed(() => {
  const option = localeStore.localeOptions.find((item) => item.value === localeStore.locale)
  return option?.label || t('locale.label')
})

const pageTitle = computed(() => {
  if (route.meta?.i18nKey) {
    return t(route.meta.i18nKey)
  }
  return t('layout.siteTitle')
})

const showMobileBack = computed(() => appStore.isMobile && route.path !== '/dashboard')

const customerChatBadge = computed(() => chatBadgeStore.getBadgeForPath('/customers/chat'))
const merchantChatBadge = computed(() => chatBadgeStore.getBadgeForPath('/tenants/chat'))

const sidebarExpanded = computed(() => {
  if (appStore.isMobile) {
    return appStore.mobileSidebarOpen
  }
  return !appStore.sidebarCollapsed
})

function goBack() {
  if (window.history.length > 1) {
    router.back()
    return
  }
  router.push('/dashboard')
}

function goCustomerChat() {
  if (customerChatBadge.value) router.push('/customers/chat')
}

function goMerchantChat() {
  if (merchantChatBadge.value) router.push('/tenants/chat')
}

function goApprovals() {
  router.push('/approvals')
}

async function handleLogout() {
  await confirmDialog(t('layout.logoutConfirm'), t('common.tip'), {
    type: 'warning',
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
  })
  authStore.logout()
  router.push('/login')
}

function handleChangePassword() {
  router.push('/profile/change-password')
}

function handleLocaleChange(value) {
  localeStore.setLocale(value)
}
</script>

<template>
  <header
    class="app-header"
    :class="[
      appStore.isMobile ? (headerVisible ? 'header-visible' : 'header-hidden') : '',
      { 'is-mobile': appStore.isMobile },
    ]"
  >
    <div class="header-left">
      <el-button
        v-if="appStore.isMobile && showMobileBack"
        text
        class="sidebar-toggle"
        @click="goBack"
      >
        <el-icon :size="20"><ArrowLeft /></el-icon>
      </el-button>
      <el-button v-else text class="sidebar-toggle" @click="appStore.toggleSidebar()">
        <el-icon :size="20">
          <Fold v-if="sidebarExpanded" />
          <Expand v-else />
        </el-icon>
      </el-button>
      <span class="header-title">{{ appStore.isMobile ? pageTitle : t('layout.siteTitle') }}</span>
    </div>

    <div class="header-right">
      <template v-if="!appStore.isMobile">
        <el-badge
          v-if="customerChatBadge"
          :value="customerChatBadge"
          :max="99"
          class="chat-badge-wrap"
        >
          <el-button text class="chat-badge-btn" :title="t('chat.customerWorkbenchTitle')" @click="goCustomerChat">
            <el-icon :size="20"><ChatLineRound /></el-icon>
          </el-button>
        </el-badge>
        <el-badge
          v-if="merchantChatBadge"
          :value="merchantChatBadge"
          :max="99"
          class="chat-badge-wrap"
        >
          <el-button text class="chat-badge-btn" :title="t('chat.merchantWorkbenchTitle')" @click="goMerchantChat">
            <el-icon :size="20"><ChatLineRound /></el-icon>
          </el-button>
        </el-badge>
      </template>

      <el-badge
        v-if="approvalBadgeStore.pendingTotal"
        :value="approvalBadgeStore.pendingTotal"
        :max="99"
        class="chat-badge-wrap"
      >
        <el-button text class="chat-badge-btn" :title="t('approval.title')" @click="goApprovals">
          <el-icon :size="20"><DocumentChecked /></el-icon>
        </el-button>
      </el-badge>

      <NotificationBell />

      <el-dropdown v-if="!appStore.isMobile" trigger="click" @command="handleLocaleChange">
        <el-button text class="locale-btn">
          <span class="locale-label">{{ currentLocaleLabel }}</span>
          <el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item
              v-for="item in localeStore.localeOptions"
              :key="item.value"
              :command="item.value"
              :class="{ 'is-active': item.value === localeStore.locale }"
            >
              {{ item.label }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <el-dropdown trigger="click">
        <div class="user-info">
          <el-avatar :size="32">{{ avatarText }}</el-avatar>
          <div v-if="!appStore.isMobile" class="user-meta">
            <span class="username">{{ nickname }}</span>
            <span v-if="roleSummary && roleSummary !== '-'" class="user-roles">{{ roleSummary }}</span>
          </div>
          <el-icon v-if="!appStore.isMobile"><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="handleChangePassword">{{ t('layout.changePassword') }}</el-dropdown-item>
            <el-dropdown-item divided @click="handleLogout">{{ t('layout.logout') }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  flex-shrink: 0;
  width: 100%;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  transition: transform 0.3s ease;
}

.app-header.is-mobile {
  position: sticky;
  top: 0;
  z-index: 120;
  height: 50px;
  padding: 0 8px;
}

.header-hidden {
  transform: translateY(-100%);
}

.header-visible {
  transform: translateY(0);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.sidebar-toggle {
  flex-shrink: 0;
  min-width: 44px;
  min-height: 44px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.chat-badge-wrap {
  display: inline-flex;
}

.chat-badge-btn {
  min-width: 44px;
  min-height: 44px;
  color: #606266;
}

.locale-btn {
  color: #606266;
  min-height: 44px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  min-height: 44px;
  padding: 0 4px;
}

.user-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.username {
  color: #606266;
}

.user-roles {
  font-size: 12px;
  color: #909399;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.el-dropdown-menu__item.is-active) {
  color: var(--el-color-primary);
  font-weight: 600;
}

@media (max-width: 991px) {
  .header-title {
    font-size: 14px;
    max-width: 140px;
  }
}

@media (max-width: 575px) {
  .app-header {
    padding: 0 8px;
  }

  .username,
  .locale-label {
    display: none;
  }

  .header-title {
    max-width: 120px;
  }
}
</style>
