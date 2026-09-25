<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  ChatDotRound,
  Goods,
  Histogram,
  List,
  User,
} from '@element-plus/icons-vue'

const route = useRoute()
const { t } = useI18n()

const tabs = computed(() => [
  { name: 'Dashboard', to: '/dashboard', label: t('seller.tabDashboard'), icon: Histogram },
  { name: 'Orders', to: '/orders', label: t('seller.tabOrders'), icon: List },
  { name: 'Products', to: '/products', label: t('seller.tabProducts'), icon: Goods },
  { name: 'Chat', to: '/chat', label: t('seller.tabChat'), icon: ChatDotRound },
  { name: 'SettingsProfile', to: '/settings/profile', label: t('seller.tabProfile'), icon: User },
])

function isActive(tab) {
  return route.name === tab.name
}
</script>

<template>
  <nav class="mobile-tabbar">
    <router-link
      v-for="tab in tabs"
      :key="tab.name"
      :to="tab.to"
      class="tab-item"
      :class="{ active: isActive(tab) }"
    >
      <el-icon :size="20"><component :is="tab.icon" /></el-icon>
      <span>{{ tab.label }}</span>
    </router-link>
  </nav>
</template>

<style scoped>
.mobile-tabbar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 110;
  display: flex;
  height: 50px;
  padding-bottom: env(safe-area-inset-bottom, 0px);
  background: #fff;
  border-top: 1px solid #ebeef5;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.04);
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  color: #909399;
  text-decoration: none;
  font-size: 11px;
}

.tab-item.active {
  color: #409eff;
}
</style>
