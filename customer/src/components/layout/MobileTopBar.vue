<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import NavBadge from '@shared/components/NavBadge.vue'
import NotificationBell from '@/components/NotificationBell.vue'
import { useCartStore } from '@/stores/cart'
import { useAuthStore } from '@/stores/auth'

defineProps({
  visible: {
    type: Boolean,
    default: true,
  },
})

const router = useRouter()
const { t } = useI18n()
const cartStore = useCartStore()
const authStore = useAuthStore()

const searchOpen = ref(false)
const keyword = ref('')

function goHome() {
  router.push({ name: 'Home' })
}

function goCart() {
  router.push({ name: 'Cart' })
}

function toggleSearch() {
  searchOpen.value = !searchOpen.value
  if (!searchOpen.value) {
    keyword.value = ''
  }
}

function submitSearch() {
  const value = keyword.value.trim()
  searchOpen.value = false
  router.push({
    name: 'Search',
    query: value ? { keyword: value } : {},
  })
  keyword.value = ''
}
</script>

<template>
  <header class="mobile-topbar" :class="visible ? 'header-visible' : 'header-hidden'">
    <div v-if="!searchOpen" class="mobile-topbar__row">
      <button type="button" class="mobile-topbar__logo" @click="goHome">
        <van-icon name="shop-o" size="20" color="var(--color-primary, #ff4d4f)" />
        <span class="logo-text">{{ t('header.mallName') }}</span>
      </button>
      <div class="mobile-topbar__actions">
        <button type="button" class="icon-btn" :aria-label="t('header.search')" @click="toggleSearch">
          <van-icon name="search" size="22" />
        </button>
        <NotificationBell v-if="authStore.isLoggedIn" />
        <button type="button" class="icon-btn cart-btn" :aria-label="t('header.cart')" @click="goCart">
          <NavBadge :count="cartStore.count">
            <van-icon name="shopping-cart-o" size="22" />
          </NavBadge>
        </button>
      </div>
    </div>

    <div v-else class="mobile-topbar__search">
      <van-search
        v-model="keyword"
        show-action
        :placeholder="t('header.searchPlaceholder')"
        autofocus
        @search="submitSearch"
        @cancel="toggleSearch"
      />
    </div>
  </header>
</template>

<style scoped>
.mobile-topbar {
  position: sticky;
  top: 0;
  z-index: 120;
  background: #fff;
  border-bottom: 1px solid #eee;
  transition: transform 0.3s ease;
}

.header-hidden {
  transform: translateY(-100%);
}

.header-visible {
  transform: translateY(0);
}

.mobile-topbar__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  height: 50px;
  padding: 0 12px;
}

.mobile-topbar__logo {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
}

.logo-text {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-primary, #ff4d4f);
}

.mobile-topbar__actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  background: transparent;
  color: #323233;
  cursor: pointer;
}

.cart-btn :deep(.nav-badge) {
  transform: translate(6px, -6px);
}

.mobile-topbar__search {
  padding: 4px 0;
}

.mobile-topbar__search :deep(.van-search) {
  padding: 0 8px;
}
</style>
