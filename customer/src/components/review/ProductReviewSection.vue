<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getProductReviews } from '@/api/review'
import { resolveImageUrl } from '@/utils/product'

const props = defineProps({
  productId: { type: [Number, String], required: true },
})

const router = useRouter()
const { t } = useI18n()

const loading = ref(true)
const stats = ref({ average_rating: 0, review_count: 0 })
const reviews = ref([])

async function load() {
  loading.value = true
  try {
    const res = await getProductReviews(props.productId, { page: 1, page_size: 3 })
    stats.value = {
      average_rating: res.data?.average_rating || 0,
      review_count: res.data?.count || res.data?.review_count || 0,
    }
    reviews.value = res.data?.results || []
  } catch {
    reviews.value = []
  } finally {
    loading.value = false
  }
}

function goAll() {
  router.push({ name: 'ProductReviews', params: { id: props.productId } })
}

function goDetail(review) {
  router.push({ name: 'ReviewDetail', params: { id: review.id } })
}

onMounted(load)
</script>

<template>
  <section class="review-section">
    <div class="section-head" @click="goAll">
      <span class="title">{{ t('review.sectionTitle') }}</span>
      <span class="score">{{ stats.average_rating || '5.0' }} · {{ t('review.totalCount', { count: stats.review_count }) }}</span>
      <van-icon name="arrow" />
    </div>
    <van-loading v-if="loading" size="20px">{{ t('common.loading') }}</van-loading>
    <van-empty v-else-if="!reviews.length" :description="t('review.noReviews')" />
    <div v-else class="review-items">
      <article v-for="item in reviews" :key="item.id" class="review-item" @click="goDetail(item)">
        <div class="row">
          <span class="name">{{ item.customer?.nickname }}</span>
          <van-rate :model-value="item.rating" readonly :size="12" color="#ee0a24" />
        </div>
        <div class="text">{{ item.content }}</div>
      </article>
      <van-button block plain type="primary" size="small" @click="goAll">{{ t('review.viewAll') }}</van-button>
    </div>
  </section>
</template>

<style scoped>
.review-section {
  margin: 12px;
  padding: 14px;
  background: #fff;
  border-radius: 10px;
}

.section-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  cursor: pointer;
}

.title {
  font-weight: 600;
  font-size: 15px;
}

.score {
  margin-left: auto;
  font-size: 13px;
  color: #ee0a24;
}

.review-item {
  padding: 10px 0;
  border-bottom: 1px solid #f5f5f5;
}

.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.name {
  font-size: 13px;
  font-weight: 600;
}

.text {
  margin-top: 6px;
  font-size: 13px;
  color: #646566;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
