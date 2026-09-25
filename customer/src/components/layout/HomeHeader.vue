<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { confirmDialog } from '@/utils/confirmDialog'
import { useAuthStore } from '@/stores/auth'
import { useCartStore } from '@/stores/cart'
import { useNotificationStore } from '@/stores/notification'
import { requireLogin } from '@/stores/loginGate'
import LocaleSwitcher from '@/components/common/LocaleSwitcher.vue'
import NotificationBell from '@/components/NotificationBell.vue'
import NavBadge from '@shared/components/NavBadge.vue'

defineProps({
  keyword: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:keyword', 'search'])

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()
const cartStore = useCartStore()
const notificationStore = useNotificationStore()

const sellerPortalUrl = import.meta.env.VITE_SELLER_URL || 'http://localhost:5175'
const sellerApplyUrl = `${sellerPortalUrl.replace(/\/$/, '')}/apply`

const hotKeywordKeys = ['phone', 'laptop', 'earphone', 'shoes', 'skincare']
const profileMenuOpen = ref(false)

const profileMenuItems = computed(() => [
  { label: t('header.profileHome'), path: '/profile' },
  { label: t('header.myOrders'), path: '/orders' },
  { label: t('header.myMessages'), path: '/notifications', showBadge: true },
  { label: t('header.mySuggestions'), path: '/suggestions' },
  { label: t('header.contactSupport'), path: '/chat' },
  { label: t('profile.settingsEntry'), path: '/profile/settings' },
])

const channelLinks = computed(() => [
  { name: 'Home', label: t('header.navHome') },
  { name: 'Category', label: t('header.navCategory') },
  { name: 'Home', label: t('header.navNewProducts'), homeChannel: 'newArrival' },
  { name: 'BillionSubsidyChannel', label: t('home.billionSubsidy') },
  { name: 'SuperDiscountChannel', label: t('home.superDiscountTitle') },
  { name: 'SeckillChannel', label: t('home.flashSale') },
  { name: 'Subsidy', label: t('home.channelSubsidy') },
  { name: 'LiveChannel', label: t('home.liveStream') },
  { name: 'FreeShippingChannel', label: t('home.freeShipping') },
])

function isActive(item) {
  if (item.homeChannel) {
    return route.name === 'Home' && route.query.channel === item.homeChannel
  }
  return route.name === item.name
}

function goChannelLink(item) {
  if (item.homeChannel) {
    router.push({ name: 'Home', query: { channel: item.homeChannel } })
    return
  }
  router.push({ name: item.name })
}

function goSearch(keyword = '') {
  router.push({
    name: 'Search',
    query: keyword ? { keyword } : {},
  })
}

async function openProtected(path) {
  profileMenuOpen.value = false
  try {
    await requireLogin({ redirect: path })
    router.push(path)
  } catch {
    // cancelled
  }
}

async function logout() {
  try {
    await confirmDialog({ title: t('common.tip'), message: t('profile.logoutConfirm') })
    authStore.logout()
    cartStore.loadGuestCart()
    notificationStore.unreadCount = 0
    router.push('/')
  } catch {
    // cancelled
  }
}
</script>

<template>
  <header class="home-header">
    <div class="top-nav">
      <div class="top-nav-inner">
        <div class="top-nav-left">
          <span class="top-link">{{ t('auth.region') }}</span>
          <template v-if="authStore.isLoggedIn">
            <span class="top-text">{{ t('auth.helloUser', { name: authStore.customer?.display_name || authStore.customer?.phone }) }}</span>
            <button type="button" class="top-link" @click="logout">{{ t('auth.logout') }}</button>
          </template>
          <template v-else>
            <router-link to="/login" class="top-link">{{ t('auth.helloLogin') }}</router-link>
            <router-link to="/register" class="top-link">{{ t('auth.freeRegister') }}</router-link>
          </template>
        </div>
        <div class="top-nav-right">
          <router-link :to="{ name: 'PointsCenter' }" class="top-link" @click.prevent="openProtected('/points')">{{ t('header.pointsCenter') }}</router-link>
          <NotificationBell v-if="authStore.isLoggedIn" />
          <router-link :to="{ name: 'Cart' }" class="top-link top-cart-link">
            <NavBadge :count="cartStore.count">
              <span>{{ t('header.cart') }}</span>
            </NavBadge>
          </router-link>
          <div
            class="top-profile-menu"
            @mouseenter="profileMenuOpen = true"
            @mouseleave="profileMenuOpen = false"
          >
            <button type="button" class="top-link top-profile-link" @click="openProtected('/profile')">
              <NavBadge :count="notificationStore.unreadCount">
                <span>{{ t('header.personalCenter') }}</span>
              </NavBadge>
              <span class="menu-arrow" :class="{ open: profileMenuOpen }">▾</span>
            </button>
            <div v-show="profileMenuOpen" class="profile-dropdown">
              <button
                v-for="item in profileMenuItems"
                :key="item.path"
                type="button"
                class="dropdown-item"
                @click="openProtected(item.path)"
              >
                <span>{{ item.label }}</span>
                <NavBadge v-if="item.showBadge" :count="notificationStore.unreadCount" />
              </button>
            </div>
          </div>
          <a :href="sellerApplyUrl" class="top-link" target="_blank" rel="noopener">{{ t('header.sellerJoin') }}</a>
          <LocaleSwitcher />
        </div>
      </div>
    </div>

    <div class="site-header">
      <div class="site-header-inner">
        <div class="logo" @click="router.push('/')">
          <div class="logo-box">{{ t('header.logoPlaceholder') }}</div>
          <span class="logo-text">{{ t('header.mallName') }}</span>
        </div>

        <div class="search-area">
          <div class="search-box">
            <input
              :value="keyword"
              class="search-input"
              :placeholder="t('header.searchPlaceholder')"
              @input="emit('update:keyword', $event.target.value)"
              @keyup.enter="emit('search', keyword)"
            />
            <button type="button" class="search-btn" @click="emit('search', keyword)">
              {{ t('header.search') }}
            </button>
          </div>
          <div class="hot-keywords">
            <button
              v-for="key in hotKeywordKeys"
              :key="key"
              type="button"
              class="hot-keyword"
              @click="goSearch(t(`header.hotKeywords.${key}`))"
            >
              {{ t(`header.hotKeywords.${key}`) }}
            </button>
          </div>
        </div>

        <div class="header-side" />
      </div>
    </div>

    <div class="channel-nav">
      <div class="channel-nav-inner">
        <button
          v-for="item in channelLinks"
          :key="`${item.name}-${item.homeChannel || ''}`"
          type="button"
          class="channel-link"
          :class="{ active: isActive(item) }"
          @click="goChannelLink(item)"
        >
          {{ item.label }}
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.home-header {
  background: #fff;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 1px 0 #eee;
}
.top-nav {
  background: #e3e4e5;
  font-size: 12px;
  color: #999;
}
.top-nav-inner,
.site-header-inner {
  max-width: 1190px;
  margin: 0 auto;
  padding: 0 16px;
}
.top-nav-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 30px;
}
.top-nav-left,
.top-nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.top-link {
  color: #999;
  text-decoration: none;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  font-size: 12px;
}
.top-link:hover {
  color: #e1251b;
}
.top-text {
  color: #666;
}
.site-header {
  padding: 12px 0 16px;
}
.site-header-inner {
  display: flex;
  align-items: flex-start;
  gap: 24px;
}
.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  cursor: pointer;
}
.logo-box {
  width: 56px;
  height: 56px;
  border: 2px dashed #ddd;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: #999;
  background: #fafafa;
}
.logo-text {
  font-size: 28px;
  font-weight: 800;
  color: #e1251b;
  letter-spacing: 1px;
}
.search-area {
  flex: 1;
  min-width: 0;
}
.search-box {
  display: flex;
  height: 40px;
  border: 2px solid #e1251b;
  border-radius: 4px;
  overflow: hidden;
}
.search-input {
  flex: 1;
  border: none;
  outline: none;
  padding: 0 14px;
  font-size: 14px;
}
.search-btn {
  width: 88px;
  border: none;
  background: #e1251b;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}
.search-btn:hover {
  background: #c81623;
}
.hot-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 8px;
}
.hot-keyword {
  border: none;
  background: none;
  padding: 0;
  font-size: 12px;
  color: #999;
  cursor: pointer;
}
.hot-keyword:hover {
  color: #e1251b;
}
.header-side {
  flex-shrink: 0;
  width: 88px;
}

.top-cart-link :deep(.nav-badge-wrap),
.top-profile-link :deep(.nav-badge-wrap) {
  display: inline-flex;
  align-items: center;
}

.top-profile-menu {
  position: relative;
}

.top-profile-link {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.menu-arrow {
  font-size: 10px;
  transition: transform 0.2s ease;
}

.menu-arrow.open {
  transform: rotate(180deg);
}

.profile-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  min-width: 148px;
  margin-top: 4px;
  padding: 6px 0;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 4px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  z-index: 200;
}

.dropdown-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  padding: 8px 14px;
  border: none;
  background: transparent;
  color: #666;
  font-size: 12px;
  text-align: left;
  cursor: pointer;
}

.dropdown-item:hover {
  background: #f7f7f7;
  color: #e1251b;
}

.channel-nav {
  border-top: 1px solid #f0f0f0;
  background: #fff;
}

.channel-nav-inner {
  max-width: 1190px;
  margin: 0 auto;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 20px;
  height: 40px;
  overflow-x: auto;
  scrollbar-width: none;
}

.channel-nav-inner::-webkit-scrollbar {
  display: none;
}

.channel-link {
  flex-shrink: 0;
  font-size: 14px;
  color: var(--color-text, #333);
  text-decoration: none;
  white-space: nowrap;
  padding: 4px 0;
  border: none;
  background: transparent;
  cursor: pointer;
  font-family: inherit;
}

.channel-link:hover,
.channel-link.active {
  color: var(--color-primary, #ff4d4f);
  font-weight: 600;
}
</style>
