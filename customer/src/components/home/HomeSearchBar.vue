<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useCartStore } from '@/stores/cart'

const router = useRouter()
const { t } = useI18n()
const cartStore = useCartStore()

const cartBadge = computed(() => {
  const count = cartStore.count
  if (!count) return ''
  return count > 99 ? '99+' : String(count)
})

function goSearch() {
  router.push({ name: 'Search' })
}

function goCart() {
  router.push({ name: 'Cart' })
}
</script>

<template>
  <header class="home-search-bar">
    <div class="search-box" @click="goSearch">
      <van-icon name="search" size="16" color="#969799" />
      <span class="search-placeholder">{{ t('home.searchPlaceholder') }}</span>
    </div>
    <button type="button" class="cart-btn" :aria-label="t('header.cart')" @click="goCart">
      <van-badge :content="cartBadge" :show-zero="false">
        <van-icon name="shopping-cart-o" size="22" />
      </van-badge>
    </button>
  </header>
</template>

<style scoped>
.home-search-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 12px;
  height: 56px;
  padding: 0 12px;
  background: #fff;
  box-sizing: border-box;
}

.search-box {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  height: 36px;
  padding: 0 14px;
  background: #f5f5f5;
  border-radius: 20px;
  cursor: pointer;
}

.search-placeholder {
  font-size: 14px;
  color: #969799;
}

.cart-btn {
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

.cart-btn :deep(.van-badge) {
  transform: translate(6px, -6px);
}
</style>
