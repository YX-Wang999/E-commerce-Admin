<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useCartStore } from '@/stores/cart'
import { useNotificationStore } from '@/stores/notification'
import { isLoggedIn } from '@/utils/auth'

const { t } = useI18n()
const route = useRoute()
const cartStore = useCartStore()
const notificationStore = useNotificationStore()

const cartBadge = computed(() => {
  const count = cartStore.count
  if (!count) return ''
  return count > 99 ? '99+' : String(count)
})

const messageBadge = computed(() => notificationStore.formatBadge(notificationStore.unreadCount))

function refreshBadges() {
  if (isLoggedIn()) {
    notificationStore.refreshUnread()
  } else {
    notificationStore.unreadCount = 0
  }
}

onMounted(refreshBadges)

watch(
  () => route.name,
  () => refreshBadges(),
)
</script>

<template>
  <van-tabbar route placeholder safe-area-inset-bottom>
    <van-tabbar-item :to="{ name: 'Home' }" icon="wap-home">{{ t('tabbar.home') }}</van-tabbar-item>
    <van-tabbar-item :to="{ name: 'Category' }" icon="apps-o">{{ t('tabbar.category') }}</van-tabbar-item>
    <van-tabbar-item :to="{ name: 'Notifications' }" icon="chat-o">
      {{ t('tabbar.messages') }}
      <template v-if="messageBadge" #icon="props">
        <van-icon :name="props.active ? 'chat' : 'chat-o'" />
        <van-badge :content="messageBadge" />
      </template>
    </van-tabbar-item>
    <van-tabbar-item :to="{ name: 'Cart' }" icon="shopping-cart-o">
      {{ t('tabbar.cart') }}
      <template v-if="cartBadge" #icon="props">
        <van-icon :name="props.active ? 'shopping-cart' : 'shopping-cart-o'" />
        <van-badge :content="cartBadge" />
      </template>
    </van-tabbar-item>
    <van-tabbar-item :to="{ name: 'Profile' }" icon="user-o">{{ t('tabbar.profile') }}</van-tabbar-item>
  </van-tabbar>
</template>

<style scoped>
:deep(.van-tabbar-item__icon) {
  position: relative;
}

:deep(.van-badge) {
  position: absolute;
  top: -4px;
  right: -10px;
}
</style>
