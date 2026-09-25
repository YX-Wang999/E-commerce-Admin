<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { useMenuTitle } from '@/i18n'
import { useChatBadgeStore } from '@/stores/chatBadge'
import { useComplaintBadgeStore } from '@/stores/complaintBadge'
import { useOrderBadgeStore } from '@/stores/orderBadge'
import { useApprovalBadgeStore } from '@/stores/approvalBadge'
import { useTenantStore } from '@/stores/tenant'

const props = defineProps({
  menus: {
    type: Array,
    default: () => [],
  },
  collapsed: {
    type: Boolean,
    default: false,
  },
})

const route = useRoute()
const activeMenu = computed(() => route.path)
const translateMenuTitle = useMenuTitle()
const chatBadgeStore = useChatBadgeStore()
const orderBadgeStore = useOrderBadgeStore()
const complaintBadgeStore = useComplaintBadgeStore()
const approvalBadgeStore = useApprovalBadgeStore()
const tenantStore = useTenantStore()

function resolveIcon(iconName) {
  if (!iconName) {
    return ElementPlusIconsVue.Menu
  }
  return ElementPlusIconsVue[iconName] || ElementPlusIconsVue.Menu
}

function getMenuTitle(item) {
  return translateMenuTitle(item.path, item.title)
}

function getBadge(path, item) {
  const parentChatBadge = chatBadgeStore.getParentDirectoryBadge(path)
  if (parentChatBadge) return parentChatBadge
  const direct = chatBadgeStore.getBadgeForPath(path)
    || orderBadgeStore.getBadgeForPath(path)
    || complaintBadgeStore.getBadgeForPath(path)
    || approvalBadgeStore.getBadgeForPath(path)
    || tenantStore.getBadgeForPath(path)
  if (direct) return direct
  if (item?.children?.length) {
    let pending = 0
    item.children.forEach((child) => {
      const childBadge = chatBadgeStore.getBadgeForPath(child.path)
        || orderBadgeStore.getBadgeForPath(child.path)
        || complaintBadgeStore.getBadgeForPath(child.path)
        || approvalBadgeStore.getBadgeForPath(child.path)
        || tenantStore.getBadgeForPath(child.path)
      if (childBadge) pending += childBadge === '99+' ? 99 : Number(childBadge)
    })
    if (pending > 0) return pending > 99 ? '99+' : pending
  }
  return ''
}
</script>

<template>
  <template v-for="item in menus" :key="item.id">
    <el-sub-menu
      v-if="item.children && item.children.length"
      :index="item.path || String(item.id)"
    >
      <template #title>
        <el-icon>
          <component :is="resolveIcon(item.icon)" />
        </el-icon>
        <span class="menu-title-wrap">
          {{ getMenuTitle(item) }}
          <span v-if="getBadge(item.path, item)" class="menu-badge">{{ getBadge(item.path, item) }}</span>
        </span>
      </template>
      <SidebarMenu :menus="item.children" :collapsed="collapsed" />
    </el-sub-menu>

    <el-menu-item v-else :index="item.path">
      <el-icon>
        <component :is="resolveIcon(item.icon)" />
      </el-icon>
      <template #title>
        <span class="menu-title-wrap">
          {{ getMenuTitle(item) }}
          <span v-if="getBadge(item.path, item)" class="menu-badge">{{ getBadge(item.path, item) }}</span>
        </span>
      </template>
    </el-menu-item>
  </template>
</template>

<script>
export default {
  name: 'SidebarMenu',
}
</script>

<style scoped>
.menu-title-wrap {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.menu-badge {
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
</style>
