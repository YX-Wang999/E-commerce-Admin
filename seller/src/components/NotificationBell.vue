<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Bell } from '@element-plus/icons-vue'
import { markAllInboxRead } from '@/api/inbox'
import { useNotificationStore } from '@/stores/notification'
import { useNotifyStore } from '@/stores/notify'

const router = useRouter()
const { t } = useI18n()
const notificationStore = useNotificationStore()
const notifyStore = useNotifyStore()

const totalUnread = computed(() => (notificationStore.unreadCount || 0) + (notifyStore.unreadCount || 0))

function formatTime(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

async function openDropdown() {
  await notificationStore.fetchList()
}

async function handleClick(item) {
  await notificationStore.readItem(item)
  if (item.related_url) {
    router.push(item.related_url)
  }
}

async function handleReadAll() {
  await Promise.all([
    notificationStore.readAll(),
    markAllInboxRead().catch(() => null),
  ])
  notifyStore.unreadCount = 0
  notifyStore.bannerVisible = false
}

function openAppealInbox() {
  const latest = notifyStore.latestReply
  if (latest?.appeal_id) {
    notifyStore.openAppealDrawer(latest.appeal_id, latest.id)
    return
  }
  notifyStore.refreshSummary()
}

onMounted(() => {
  notificationStore.refreshUnread()
})
</script>

<template>
  <el-dropdown trigger="click" @visible-change="(v) => v && openDropdown()">
    <el-badge :value="totalUnread || ''" :hidden="!totalUnread" :max="99">
      <el-button circle>
        <el-icon><Bell /></el-icon>
      </el-button>
    </el-badge>
    <template #dropdown>
      <div class="notification-panel">
        <div class="panel-header">
          <span>{{ t('seller.notificationTitle') }}</span>
          <el-button link type="primary" @click.stop="handleReadAll">{{ t('seller.markAllRead') }}</el-button>
        </div>
        <div v-if="notifyStore.unreadCount" class="appeal-entry" @click="openAppealInbox">
          {{ t('seller.appealUnread', { count: notifyStore.unreadCount }) }}
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
          <el-empty
            v-if="!notificationStore.loading && !notificationStore.items.length && !notifyStore.unreadCount"
            :description="t('seller.notificationEmpty')"
          />
        </div>
      </div>
    </template>
  </el-dropdown>
</template>

<style scoped>
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

.appeal-entry {
  padding: 10px 16px;
  background: #fdf6ec;
  color: #e6a23c;
  font-size: 13px;
  cursor: pointer;
  border-bottom: 1px solid #faecd8;
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
