<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ArrowRight } from '@element-plus/icons-vue'
import {
  ChatDotRound,
  Goods,
  List,
  Medal,
  Odometer,
  Setting,
  Ticket,
  User,
  UserFilled,
} from '@element-plus/icons-vue'
import { SELLER_EXPANDED_STORAGE_KEY, SELLER_MENU_ITEMS } from '@/config/menu'
import { useChatBadgeStore } from '@/stores/chatBadge'
import { useComplaintBadgeStore } from '@/stores/complaintBadge'

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false,
  },
})

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const chatBadgeStore = useChatBadgeStore()
const complaintBadgeStore = useComplaintBadgeStore()

const iconMap = {
  Odometer,
  Goods,
  List,
  User,
  ChatDotRound,
  Setting,
  Ticket,
  UserFilled,
  Medal,
}

const menuItems = computed(() =>
  SELLER_MENU_ITEMS.map((item) => ({
    ...item,
    icon: iconMap[item.icon] || Odometer,
    label: t(item.labelKey),
    children: item.children?.map((child) => ({
      ...child,
      label: t(child.labelKey),
    })),
  })),
)

function loadExpandedKeys() {
  try {
    const raw = localStorage.getItem(SELLER_EXPANDED_STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const expandedKeys = ref(loadExpandedKeys())

function saveExpandedKeys() {
  localStorage.setItem(SELLER_EXPANDED_STORAGE_KEY, JSON.stringify(expandedKeys.value))
}

function normalizePath(path) {
  if (!path || path === '/') return '/dashboard'
  return path.replace(/\/$/, '') || '/dashboard'
}

function isPathActive(path) {
  const current = normalizePath(route.path)
  const target = normalizePath(path)
  if (target === '/dashboard') {
    return current === '/dashboard'
  }
  return current === target || current.startsWith(`${target}/`)
}

function isGroupActive(item) {
  if (item.path) return isPathActive(item.path)
  return item.children?.some((child) => isPathActive(child.path))
}

function isExpanded(item) {
  if (!item.groupKey) return false
  return expandedKeys.value.includes(item.groupKey)
}

function toggleGroup(item) {
  if (!item.groupKey) return
  const keys = [...expandedKeys.value]
  const index = keys.indexOf(item.groupKey)
  if (index >= 0) {
    keys.splice(index, 1)
  } else {
    keys.push(item.groupKey)
  }
  expandedKeys.value = keys
  saveExpandedKeys()
}

function ensureActiveGroupExpanded() {
  const keys = new Set(expandedKeys.value)
  menuItems.value.forEach((item) => {
    if (item.groupKey && isGroupActive(item)) {
      keys.add(item.groupKey)
    }
  })
  expandedKeys.value = [...keys]
  saveExpandedKeys()
}

watch(() => route.path, ensureActiveGroupExpanded, { immediate: true })

function navigate(path) {
  const target = normalizePath(path)
  if (normalizePath(route.path) !== target) {
    router.push(target)
  }
}

function handleParentClick(item) {
  if (item.children?.length) {
    if (!props.collapsed) {
      toggleGroup(item)
    } else {
      navigate(item.children[0].path)
    }
    return
  }
  if (item.path) {
    navigate(item.path)
  }
}

function getBadge(path) {
  if (path === '/chat') {
    return chatBadgeStore.formatBadge(chatBadgeStore.unreadTotal)
  }
  if (path === '/orders/refunds') {
    return complaintBadgeStore.getBadgeForPath('/orders/refunds')
  }
  return ''
}
</script>

<template>
  <nav class="sidebar-nav">
    <div v-for="item in menuItems" :key="item.groupKey || item.path" class="nav-block">
      <button
        type="button"
        class="nav-item"
        :class="{ active: isGroupActive(item), expanded: isExpanded(item) }"
        @click="handleParentClick(item)"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
        <span
          v-if="!collapsed && item.badgePath && getBadge(item.badgePath)"
          class="nav-badge"
        >
          {{ getBadge(item.badgePath) }}
        </span>
        <el-icon
          v-if="!collapsed && item.children?.length"
          class="nav-arrow"
          :class="{ rotated: isExpanded(item) }"
        >
          <ArrowRight />
        </el-icon>
      </button>

      <div
        v-if="!collapsed && item.children?.length && isExpanded(item)"
        class="submenu"
      >
        <button
          v-for="child in item.children"
          :key="child.path"
          type="button"
          class="submenu-item"
          :class="{ active: isPathActive(child.path) }"
          @click="navigate(child.path)"
        >
          <span class="submenu-label">{{ child.label }}</span>
          <span
            v-if="child.badgePath && getBadge(child.badgePath)"
            class="nav-badge submenu-badge"
          >
            {{ getBadge(child.badgePath) }}
          </span>
        </button>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.sidebar-nav {
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-block {
  display: flex;
  flex-direction: column;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.75);
  padding: 12px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  text-align: left;
}

.nav-item:hover,
.nav-item.active {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
}

.nav-label {
  white-space: nowrap;
  flex: 1;
}

.nav-arrow {
  font-size: 12px;
  transition: transform 0.2s ease;
}

.nav-arrow.rotated {
  transform: rotate(90deg);
}

.submenu {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin: 2px 0 4px;
  padding-left: 20px;
}

.submenu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.62);
  padding: 9px 14px 9px 18px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  text-align: left;
}

.submenu-item:hover,
.submenu-item.active {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.submenu-item.active {
  font-weight: 600;
}

.submenu-label {
  flex: 1;
}

.nav-badge {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: #f56c6c;
  color: #fff;
  font-size: 11px;
  line-height: 18px;
  text-align: center;
  font-weight: 600;
}

.submenu-badge {
  flex-shrink: 0;
}
</style>
