<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useProductList } from '@/composables/useProductList'
import { formatPrice, resolveImageUrl } from '@/utils/product'

const router = useRouter()
const { t } = useI18n()

const activePeriod = ref('all')

const periodDaysMap = {
  all: 30,
  today: 1,
  week: 7,
  month: 30,
}

const periodTabs = computed(() => [
  { key: 'all', label: t('newProducts.tabAll') },
  { key: 'today', label: t('newProducts.tabToday') },
  { key: 'week', label: t('newProducts.tabWeek') },
  { key: 'month', label: t('newProducts.tabMonth') },
])

const { products, loading, loadingMore, finished, error, load, loadMore, retry } = useProductList(() => ({
  is_new: true,
  days: periodDaysMap[activePeriod.value] ?? 30,
}))

function isNewProduct(createdAt) {
  if (!createdAt) return false
  return Date.now() - new Date(createdAt).getTime() < 24 * 60 * 60 * 1000
}

function formatPublishedAt(createdAt) {
  if (!createdAt) return ''
  return String(createdAt).slice(0, 16).replace('T', ' ')
}

function soldCount(product) {
  if (product.sold_count != null) return product.sold_count
  return product.tenant?.sold_count ?? 0
}

function goProduct(product) {
  router.push({ name: 'ProductDetail', params: { id: product.id } })
}

function onListLoad() {
  if (!products.value.length && !loading.value && !finished.value) {
    load(true)
    return
  }
  loadMore()
}

watch(activePeriod, () => load(true), { immediate: true })
</script>

<template>
  <section class="new-products-panel">
    <div class="panel-head">
      <div class="panel-title">{{ t('newProducts.title') }}</div>
      <div class="panel-sub">{{ t('newProducts.subtitle') }}</div>
    </div>

    <div class="period-row">
      <button
        v-for="tab in periodTabs"
        :key="tab.key"
        type="button"
        class="period-chip"
        :class="{ active: activePeriod === tab.key }"
        @click="activePeriod = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <van-loading v-if="loading && !products.length" class="panel-loading" size="24px">
      {{ t('common.loading') }}
    </van-loading>

    <van-empty v-else-if="!loading && !products.length && !error" :description="t('newProducts.empty')" />

    <div v-else-if="error" class="error-wrap">
      <van-empty :description="t('newProducts.loadFailed')" />
      <van-button round type="primary" size="small" @click="retry">{{ t('newProducts.retry') }}</van-button>
    </div>

    <van-list
      v-else
      v-model:loading="loadingMore"
      :finished="finished"
      :finished-text="t('product.noMore')"
      @load="onListLoad"
    >
      <article
        v-for="product in products"
        :key="product.id"
        class="product-row card-interactive"
        @click="goProduct(product)"
      >
        <div class="thumb-wrap">
          <img
            v-if="product.image"
            :src="resolveImageUrl(product.image)"
            :alt="product.name"
            class="thumb"
          />
          <div v-else class="thumb thumb-fallback">{{ product.name?.charAt(0) }}</div>
        </div>
        <div class="info">
          <div class="name-row">
            <span v-if="isNewProduct(product.created_at)" class="new-badge">NEW</span>
            <span class="name">{{ product.name }}</span>
          </div>
          <div class="published">{{ t('newProducts.publishedAt', { time: formatPublishedAt(product.created_at) }) }}</div>
          <div class="price">{{ formatPrice(product.price) }}</div>
          <div class="sold">{{ t('product.soldCount', { count: soldCount(product) }) }}</div>
        </div>
      </article>
    </van-list>
  </section>
</template>

<style scoped>
.new-products-panel {
  padding: 12px 0 16px;
}

.panel-head {
  padding: 4px 12px 10px;
}

.panel-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text, #333);
}

.panel-sub {
  margin-top: 4px;
  font-size: 13px;
  color: var(--color-text-hint, #999);
}

.period-row {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 0 12px 10px;
  -webkit-overflow-scrolling: touch;
}

.period-chip {
  flex-shrink: 0;
  border: 1px solid var(--color-border, #f0f0f0);
  background: #fff;
  color: var(--color-text-secondary, #666);
  border-radius: 999px;
  padding: 5px 14px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.period-chip.active {
  border-color: var(--color-primary, #ff4d4f);
  color: var(--color-primary, #ff4d4f);
  background: #fff1f0;
}

.panel-loading {
  display: flex;
  justify-content: center;
  padding: 32px 0;
}

.error-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px 16px;
}

.product-row {
  display: flex;
  gap: 12px;
  margin: 0 12px 10px;
  padding: 12px;
  background: #fff;
  border-radius: 12px;
  cursor: pointer;
}

.thumb-wrap {
  flex-shrink: 0;
}

.thumb {
  width: 120px;
  height: 120px;
  border-radius: 10px;
  object-fit: cover;
  background: var(--color-bg, #f5f5f5);
}

.thumb-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: var(--color-text-hint, #999);
}

.info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
}

.name-row {
  display: flex;
  align-items: flex-start;
  gap: 6px;
}

.new-badge {
  flex-shrink: 0;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--color-primary, #ff4d4f);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  line-height: 18px;
}

.name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text, #333);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.published {
  font-size: 12px;
  color: var(--color-text-hint, #999);
}

.price {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-primary, #ff4d4f);
}

.sold {
  font-size: 12px;
  color: var(--color-text-secondary, #666);
}
</style>
