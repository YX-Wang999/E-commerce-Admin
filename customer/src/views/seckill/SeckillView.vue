<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getSeckillProducts } from '@/api/promotion'
import { formatPrice, resolveImageUrl } from '@/utils/product'

const router = useRouter()
const { t } = useI18n()

const items = ref([])
const loading = ref(true)

async function fetchData() {
  loading.value = true
  try {
    const res = await getSeckillProducts()
    items.value = res.data || []
  } finally {
    loading.value = false
  }
}

function goProduct(item) {
  router.push({ name: 'ProductDetail', params: { id: item.product_id }, query: { seckill_id: item.activity_id } })
}

onMounted(fetchData)
</script>

<template>
  <div class="seckill-page">
    <van-nav-bar :title="t('seckill.title')" left-arrow fixed placeholder @click-left="router.back()" />

    <van-loading v-if="loading" class="page-loading" vertical>{{ t('common.loading') }}</van-loading>
    <van-empty v-else-if="!items.length" :description="t('seckill.empty')" />

    <div v-else class="seckill-grid">
      <div v-for="item in items" :key="`${item.activity_id}-${item.product_id}`" class="seckill-card" @click="goProduct(item)">
        <img :src="resolveImageUrl(item.image)" class="seckill-card__img" alt="" />
        <div class="seckill-card__body">
          <div class="seckill-card__name">{{ item.product_name }}</div>
          <div class="seckill-card__price">
            <span class="seckill-price">{{ formatPrice(item.seckill_price) }}</span>
            <span class="origin-price">{{ formatPrice(item.original_price) }}</span>
          </div>
          <div class="seckill-card__meta">
            {{ t('seckill.stockLeft', { count: item.seckill_stock }) }}
          </div>
          <van-button type="danger" size="small" block round>{{ t('seckill.buyNow') }}</van-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.seckill-page {
  min-height: 100vh;
  background: #f5f6fa;
  padding-bottom: 16px;
}

.page-loading {
  padding: 60px 0;
  display: flex;
  justify-content: center;
}

.seckill-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  padding: 12px;
}

.seckill-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.seckill-card__img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  background: #f0f2f5;
}

.seckill-card__body {
  padding: 10px;
}

.seckill-card__name {
  font-size: 13px;
  line-height: 1.4;
  height: 36px;
  overflow: hidden;
}

.seckill-price {
  color: #ee0a24;
  font-weight: 700;
  font-size: 16px;
}

.origin-price {
  margin-left: 6px;
  color: #969799;
  font-size: 12px;
  text-decoration: line-through;
}

.seckill-card__meta {
  margin: 6px 0 8px;
  font-size: 12px;
  color: #969799;
}
</style>
