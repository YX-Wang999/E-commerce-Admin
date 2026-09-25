<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import NavBadge from '@shared/components/NavBadge.vue'
import { useNotificationStore } from '@/stores/notification'

const router = useRouter()
const { t } = useI18n()
const notificationStore = useNotificationStore()

const badge = computed(() => notificationStore.unreadCount)

async function goNotifications() {
  router.push({ name: 'Notifications' })
}

onMounted(() => {
  notificationStore.refreshUnread()
})
</script>

<template>
  <button type="button" class="bell-btn" :aria-label="t('header.myMessages')" @click="goNotifications">
    <NavBadge :count="badge">
      <van-icon name="bell" size="20" />
    </NavBadge>
  </button>
</template>

<style scoped>
.bell-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: #323233;
  cursor: pointer;
  padding: 0;
}
</style>
