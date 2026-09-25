<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Bell } from '@element-plus/icons-vue'
import { useNotificationStore } from '@/stores/notification'

const router = useRouter()
const { t } = useI18n()
const notificationStore = useNotificationStore()
const dropdownVisible = ref(false)

function formatTime(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

async function openDropdown() {
  dropdownVisible.value = true
  await notificationStore.fetchList()
}

async function handleClick(item) {
  dropdownVisible.value = false
  try {
    await notificationStore.readItem(item)
  } catch {
    // ignore
  }
  if (item.type === 'approval' && item.related_url) {
    router.push(item.related_url)
    return
  }
  if (item.type === 'tenant' && item.related_id) {
    router.push({ name: 'TenantDetail', params: { id: String(item.related_id) }, query: { tab: 'changes' } })
    return
  }
  if (item.related_url) {
    router.push(item.related_url)
  }
}

async function handleReadAll() {
  await notificationStore.readAll()
}

onMounted(() => {
  notificationStore.refreshUnread()
})
</script>

<template>
  <el-dropdown trigger="click" @visible-change="(v) => v && openDropdown()">
    <el-badge :value="notificationStore.unreadCount || ''" :hidden="!notificationStore.unreadCount" :max="99">
      <el-button text class="bell-btn">
        <el-icon :size="20"><Bell /></el-icon>
      </el-button>
    </el-badge>
    <template #dropdown>
      <div class="notification-panel">
        <div class="panel-header">
          <span>{{ t('notification.title') }}</span>
          <el-button link type="primary" @click.stop="handleReadAll">{{ t('notification.markAllRead') }}</el-button>
        </div>
        <div v-loading="notificationStore.loading" class="panel-list">
          <div
            v-for="item in notificationStore.items"
            :key="item.id"
            class="panel-item"
            :class="{ unread: !item.is_read }"
            @click="handleClick(item)"
          >
            <div class="item-title">{{ item.title }}</div>
            <div class="item-content">{{ item.content }}</div>
            <div class="item-time">{{ formatTime(item.created_at) }}</div>
          </div>
          <el-empty v-if="!notificationStore.loading && !notificationStore.items.length" :description="t('notification.empty')" />
        </div>
      </div>
    </template>
  </el-dropdown>
</template>

<style scoped>
.bell-btn {
  min-height: 44px;
  min-width: 44px;
}

.notification-panel {
  width: 360px;
  max-width: 90vw;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
  font-weight: 600;
}

.panel-list {
  max-height: 420px;
  overflow-y: auto;
}

.panel-item {
  padding: 12px 16px;
  border-bottom: 1px solid #f2f3f5;
  cursor: pointer;
}

.panel-item:hover {
  background: #f5f7fa;
}

.panel-item.unread {
  background: #ecf5ff;
}

.item-title {
  font-weight: 600;
  color: #303133;
}

.item-content {
  margin-top: 4px;
  font-size: 13px;
  color: #606266;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-time {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}
</style>
