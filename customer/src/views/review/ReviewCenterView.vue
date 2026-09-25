<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import ReviewPublishSheet from '@/components/review/ReviewPublishSheet.vue'
import { getReviewUserCenter } from '@/api/review'
import { resolveImageUrl } from '@/utils/product'
import { resolveErrorMessage } from '@/utils/feedback'
import { showToast } from 'vant'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const activeTab = ref('pending')
const loading = ref(false)
const items = ref([])
const publishVisible = ref(false)
const publishTarget = ref(null)
const publishMode = ref('create')
const publishReviewId = ref(null)

const tabs = computed(() => [
  { key: 'pending', label: t('review.tabPending') },
  { key: 'follow_up', label: t('review.tabFollowUp') },
  { key: 'reviewed', label: t('review.tabReviewed') },
])

async function fetchList() {
  loading.value = true
  try {
    const res = await getReviewUserCenter({ tab: activeTab.value })
    items.value = res.data?.items || []
  } catch (error) {
    items.value = []
    showToast(resolveErrorMessage(error, 'review.loadFailed'))
  } finally {
    loading.value = false
  }
}

function openPublish(item) {
  publishTarget.value = item
  publishMode.value = 'create'
  publishReviewId.value = null
  publishVisible.value = true
}

function openFollowUp(review) {
  publishTarget.value = null
  publishMode.value = 'follow_up'
  publishReviewId.value = review.id
  publishVisible.value = true
}

function goDetail(review) {
  router.push({ name: 'ReviewDetail', params: { id: review.id } })
}

function formatDate(value) {
  return value ? String(value).replace('T', ' ').slice(0, 10) : ''
}

onMounted(() => {
  if (route.query.tab) activeTab.value = route.query.tab
  fetchList()
})

watch(activeTab, fetchList)

watch(
  () => route.query.publish,
  (v) => {
    if (v === '1' && route.query.order_id && route.query.product_id) {
      publishTarget.value = {
        order_id: Number(route.query.order_id),
        product_id: Number(route.query.product_id),
        product_name: route.query.product_name || '',
        order_no: route.query.order_no || '',
        product_image: route.query.product_image || '',
      }
      publishMode.value = 'create'
      publishVisible.value = true
    }
  },
  { immediate: true },
)
</script>

<template>
  <div class="review-center-page">
    <van-nav-bar
      :title="t('review.centerTitle')"
      left-arrow
      fixed
      placeholder
      @click-left="router.back()"
    />

    <van-tabs v-model:active="activeTab" sticky offset-top="46">
      <van-tab v-for="tab in tabs" :key="tab.key" :name="tab.key" :title="tab.label" />
    </van-tabs>

    <van-loading v-if="loading" class="page-loading" vertical>{{ t('common.loading') }}</van-loading>
    <van-empty v-else-if="!items.length" :description="t('review.empty')" />

    <div v-else class="review-list">
      <!-- 待评价 -->
      <template v-if="activeTab === 'pending'">
        <article v-for="item in items" :key="`${item.order_id}-${item.product_id}`" class="card">
          <div class="card-row">
            <img v-if="item.product_image" :src="resolveImageUrl(item.product_image)" class="thumb" alt="" />
            <div class="card-body">
              <div class="title">{{ item.product_name }}</div>
              <div class="meta">{{ t('checkout.orderNo', { no: item.order_no }) }}</div>
              <van-button size="small" type="primary" round @click="openPublish(item)">
                {{ t('review.goReview') }}
              </van-button>
            </div>
          </div>
        </article>
      </template>

      <!-- 可追评 / 已评价 -->
      <template v-else>
        <article v-for="review in items" :key="review.id" class="card review-card" @click="goDetail(review)">
          <div class="review-head">
            <span class="nickname">{{ review.customer?.nickname }}</span>
            <van-rate :model-value="review.rating" readonly :size="14" color="#ee0a24" />
          </div>
          <div class="review-content">{{ review.content }}</div>
          <div v-if="review.images?.length" class="img-row">
            <img v-for="(img, i) in review.images.slice(0, 4)" :key="i" :src="resolveImageUrl(img)" alt="" />
          </div>
          <div class="review-meta">
            <span>{{ formatDate(review.created_at) }}</span>
            <span v-if="review.product?.name">{{ t('review.productLabel') }}：{{ review.product.name }}</span>
          </div>
          <div class="stats">
            <span>👁 {{ review.view_count }}</span>
            <span>💬 {{ review.comment_count }}</span>
            <span>👍 {{ review.like_count }}</span>
          </div>
          <van-button
            v-if="activeTab === 'follow_up'"
            size="mini"
            type="primary"
            plain
            class="follow-btn"
            @click.stop="openFollowUp(review)"
          >
            {{ t('review.followUp') }}
          </van-button>
        </article>
      </template>
    </div>

    <ReviewPublishSheet
      v-model:show="publishVisible"
      :target="publishTarget"
      :mode="publishMode"
      :review-id="publishReviewId"
      @success="fetchList"
    />
  </div>
</template>

<style scoped>
.review-center-page {
  min-height: 100vh;
  background: #f5f6fa;
  padding-bottom: 24px;
}

.page-loading {
  padding: 48px 0;
  display: flex;
  justify-content: center;
}

.review-list {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.card {
  background: #fff;
  border-radius: 10px;
  padding: 14px;
}

.card-row {
  display: flex;
  gap: 12px;
}

.thumb {
  width: 72px;
  height: 72px;
  border-radius: 8px;
  object-fit: cover;
  flex-shrink: 0;
}

.card-body .title {
  font-size: 15px;
  font-weight: 600;
}

.meta {
  font-size: 12px;
  color: #969799;
  margin: 6px 0 10px;
}

.review-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nickname {
  font-weight: 600;
  font-size: 14px;
}

.review-content {
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.5;
  color: #323233;
}

.img-row {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.img-row img {
  width: 72px;
  height: 72px;
  object-fit: cover;
  border-radius: 6px;
}

.review-meta {
  margin-top: 8px;
  font-size: 12px;
  color: #969799;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stats {
  margin-top: 8px;
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #646566;
}

.follow-btn {
  margin-top: 10px;
}
</style>
