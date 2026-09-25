<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { resolveNotificationRoute } from '@/utils/notificationRoute'
import { useNotificationStore } from '@/stores/notification'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const notificationStore = useNotificationStore()

const isTabRoot = computed(() => route.name === 'Notifications')

function formatTime(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

async function openItem(item) {
  try {
    await notificationStore.readItem(item)
  } catch {
    // ignore stale notification ids
  }
  const target = resolveNotificationRoute(item.related_url)
  if (target) {
    await router.push(target)
  }
}

function handleBack() {
  if (isTabRoot.value) return
  router.back()
}

onMounted(async () => {
  await Promise.all([notificationStore.fetchList(50), notificationStore.refreshUnread()])
})
</script>

<template>
  <div class="notification-page">
    <van-nav-bar
      :title="t('notification.title')"
      :left-arrow="!isTabRoot"
      fixed
      placeholder
      @click-left="handleBack"
    />
    <div class="toolbar">
      <van-button size="small" plain type="primary" @click="notificationStore.readAll()">
        {{ t('notification.markAllRead') }}
      </van-button>
    </div>

    <van-loading v-if="notificationStore.loading" class="page-loading" vertical>
      {{ t('common.loading') }}
    </van-loading>

    <van-empty
      v-else-if="!notificationStore.items.length"
      :description="t('notification.empty')"
    />

    <div v-else class="notification-list">
      <article
        v-for="item in notificationStore.items"
        :key="item.id"
        class="notification-item"
        :class="{ unread: !item.is_read }"
        @click="openItem(item)"
      >
        <div class="notification-item__title">{{ item.title }}</div>
        <div class="notification-item__content">{{ item.content }}</div>
        <div class="notification-item__time">{{ formatTime(item.created_at) }}</div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.notification-page {
  min-height: 100%;
  background: #f5f5f5;
}

.toolbar {
  display: flex;
  justify-content: flex-end;
  padding: 8px 12px;
  background: #fff;
}

.page-loading {
  padding: 48px 0;
}

.notification-list {
  padding: 8px 12px 16px;
}

.notification-item {
  margin-bottom: 8px;
  padding: 12px;
  background: #fff;
  border-radius: 8px;
  cursor: pointer;
}

.notification-item.unread {
  border-left: 3px solid #1989fa;
}

.notification-item__title {
  font-size: 15px;
  font-weight: 600;
  color: #323233;
}

.notification-item__content {
  margin-top: 6px;
  font-size: 13px;
  color: #646566;
  line-height: 1.5;
}

.notification-item__time {
  margin-top: 8px;
  font-size: 12px;
  color: #969799;
}
</style>
