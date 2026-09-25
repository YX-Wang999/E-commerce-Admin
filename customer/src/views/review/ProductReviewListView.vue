<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getProductReviews } from '@/api/review'
import { resolveImageUrl } from '@/utils/product'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const loading = ref(true)
const reviews = ref([])
const stats = ref({ average_rating: 0, review_count: 0 })

async function load() {
  loading.value = true
  try {
    const res = await getProductReviews(route.params.id, { page: 1, page_size: 50 })
    reviews.value = res.data?.results || []
    stats.value = {
      average_rating: res.data?.average_rating || 0,
      review_count: res.data?.count || 0,
    }
  } finally {
    loading.value = false
  }
}

function goDetail(id) {
  router.push({ name: 'ReviewDetail', params: { id } })
}

onMounted(load)
</script>

<template>
  <div class="product-reviews-page">
    <van-nav-bar
      :title="t('review.listTitle')"
      left-arrow
      fixed
      placeholder
      @click-left="router.back()"
    />
    <div class="summary">
      {{ stats.average_rating }} · {{ t('review.totalCount', { count: stats.review_count }) }}
    </div>
    <van-loading v-if="loading" class="page-loading" vertical>{{ t('common.loading') }}</van-loading>
    <van-empty v-else-if="!reviews.length" :description="t('review.noReviews')" />
    <div v-else class="list">
      <article v-for="item in reviews" :key="item.id" class="card" @click="goDetail(item.id)">
        <div class="head">
          <span>{{ item.customer?.nickname }}</span>
          <van-rate :model-value="item.rating" readonly :size="14" color="#ee0a24" />
        </div>
        <p>{{ item.content }}</p>
        <div v-if="item.images?.length" class="imgs">
          <img v-for="(img, i) in item.images.slice(0, 3)" :key="i" :src="resolveImageUrl(img)" alt="" />
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.product-reviews-page {
  min-height: 100vh;
  background: #f5f6fa;
}

.summary {
  padding: 12px 16px;
  font-size: 14px;
  color: #ee0a24;
  background: #fff;
}

.page-loading {
  padding: 40px;
  display: flex;
  justify-content: center;
}

.list {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.card {
  background: #fff;
  border-radius: 10px;
  padding: 14px;
}

.head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-weight: 600;
}

.imgs {
  display: flex;
  gap: 6px;
  margin-top: 8px;
}

.imgs img {
  width: 64px;
  height: 64px;
  object-fit: cover;
  border-radius: 6px;
}
</style>
