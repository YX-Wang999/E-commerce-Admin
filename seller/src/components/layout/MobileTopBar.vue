<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ArrowLeft } from '@element-plus/icons-vue'
import NotificationBell from '@/components/NotificationBell.vue'
import { useAuthStore } from '@/stores/auth'

const TAB_ROOTS = new Set(['Dashboard', 'Orders', 'Products', 'Chat', 'SettingsProfile'])

defineProps({
  visible: {
    type: Boolean,
    default: true,
  },
  pageTitle: {
    type: String,
    default: '',
  },
})

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()

const showBack = computed(() => !TAB_ROOTS.has(String(route.name)))

const avatarText = computed(() =>
  (authStore.user?.nickname || authStore.user?.username || 'U').slice(0, 1).toUpperCase(),
)

function goBack() {
  if (window.history.length > 1) {
    router.back()
    return
  }
  router.push({ name: 'Dashboard' })
}

function goProfile() {
  router.push({ name: 'SettingsProfile' })
}

async function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <header class="mobile-topbar" :class="visible ? 'header-visible' : 'header-hidden'">
    <div class="mobile-topbar__left">
      <el-button v-if="showBack" text class="back-btn" @click="goBack">
        <el-icon :size="20"><ArrowLeft /></el-icon>
      </el-button>
    </div>

    <div class="mobile-topbar__title">{{ pageTitle }}</div>

    <div class="mobile-topbar__right">
      <NotificationBell />
      <el-dropdown trigger="click">
        <button type="button" class="avatar-btn">
          <span class="avatar-circle">{{ avatarText }}</span>
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="goProfile">{{ t('seller.menuProfile') }}</el-dropdown-item>
            <el-dropdown-item divided @click="handleLogout">{{ t('seller.logout') }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<style scoped>
.mobile-topbar {
  position: sticky;
  top: 0;
  z-index: 120;
  display: grid;
  grid-template-columns: 48px 1fr auto;
  align-items: center;
  gap: 8px;
  height: 50px;
  padding: 0 8px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  transition: transform 0.3s ease;
}

.header-hidden {
  transform: translateY(-100%);
}

.header-visible {
  transform: translateY(0);
}

.mobile-topbar__title {
  font-size: 16px;
  font-weight: 600;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-topbar__right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.back-btn {
  min-width: 40px;
  min-height: 40px;
}

.avatar-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 0 4px;
}

.avatar-circle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}

.mobile-topbar__right :deep(.el-button.is-circle) {
  width: 36px;
  height: 36px;
}
</style>
