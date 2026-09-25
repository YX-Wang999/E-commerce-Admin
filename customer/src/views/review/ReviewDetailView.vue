<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showToast } from 'vant'
import {
  commentReview,
  getReviewComments,
  getReviewDetail,
  incrementReviewView,
  likeReview,
} from '@/api/review'
import { resolveImageUrl } from '@/utils/product'
import { resolveErrorMessage, toastSuccess } from '@/utils/feedback'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const loading = ref(true)
const review = ref(null)
const comments = ref([])
const commentText = ref('')
const submitting = ref(false)
const liking = ref(false)

async function loadAll() {
  loading.value = true
  try {
    const id = route.params.id
    const [detailRes, commentsRes] = await Promise.all([
      getReviewDetail(id),
      getReviewComments(id),
    ])
    review.value = detailRes.data
    comments.value = commentsRes.data?.results || []
    incrementReviewView(id).then((res) => {
      if (review.value) review.value.view_count = res.data?.view_count ?? review.value.view_count
    }).catch(() => {})
  } catch (error) {
    review.value = null
    showToast(resolveErrorMessage(error, 'review.loadFailed'))
  } finally {
    loading.value = false
  }
}

async function handleLike() {
  if (!review.value?.id || liking.value) return
  liking.value = true
  try {
    const res = await likeReview(review.value.id)
    review.value.liked = res.data?.liked
    review.value.like_count = res.data?.like_count
  } catch (error) {
    showToast(resolveErrorMessage(error, 'review.likeFailed'))
  } finally {
    liking.value = false
  }
}

async function handleComment() {
  if (!commentText.value.trim() || submitting.value) return
  submitting.value = true
  try {
    const res = await commentReview(review.value.id, { content: commentText.value.trim() })
    comments.value.push(res.data)
    review.value.comment_count += 1
    commentText.value = ''
    toastSuccess(res.message || t('review.commentSuccess'))
  } catch (error) {
    showToast(resolveErrorMessage(error, 'review.commentFailed'))
  } finally {
    submitting.value = false
  }
}

function formatDate(value) {
  return value ? String(value).replace('T', ' ').slice(0, 16) : ''
}

onMounted(loadAll)
</script>

<template>
  <div class="review-detail-page">
    <van-nav-bar
      :title="t('review.detailTitle')"
      left-arrow
      fixed
      placeholder
      @click-left="router.back()"
    />

    <van-loading v-if="loading" class="page-loading" vertical>{{ t('common.loading') }}</van-loading>
    <van-empty v-else-if="!review" :description="t('review.notFound')" />

    <template v-else>
      <section class="card">
        <div class="head">
          <div class="avatar">{{ (review.customer?.nickname || 'U').charAt(0) }}</div>
          <div>
            <div class="name">{{ review.customer?.nickname }}</div>
            <div class="stats-line">
              {{ t('review.viewCount', { count: review.view_count }) }}
              · {{ t('review.likeCount', { count: review.like_count }) }}
              · {{ t('review.commentCount', { count: review.comment_count }) }}
            </div>
          </div>
        </div>
        <van-rate :model-value="review.rating" readonly :size="18" color="#ee0a24" class="rate" />
        <div class="content">{{ review.content }}</div>
        <div v-if="review.images?.length" class="img-grid">
          <img v-for="(img, i) in review.images" :key="i" :src="resolveImageUrl(img)" alt="" />
        </div>
        <div class="date">{{ formatDate(review.created_at) }}</div>
        <div v-if="review.product?.name" class="product">{{ t('review.productLabel') }}：{{ review.product.name }}</div>
        <div class="actions">
          <van-button size="small" :type="review.liked ? 'primary' : 'default'" :loading="liking" @click="handleLike">
            👍 {{ review.like_count }}
          </van-button>
          <van-tag v-if="review.is_public" type="success">{{ t('review.publicTag') }}</van-tag>
        </div>
        <div v-if="review.follow_up_content" class="follow-up">
          <div class="follow-label">{{ t('review.followUpBlock') }}</div>
          <div>{{ review.follow_up_content }}</div>
        </div>
      </section>

      <section class="card comments">
        <div class="section-title">{{ t('review.commentsTitle', { count: comments.length }) }}</div>
        <div v-for="c in comments" :key="c.id" class="comment-item">
          <div class="comment-name">{{ c.customer?.nickname }}</div>
          <div class="comment-text">{{ c.content }}</div>
          <div class="comment-date">{{ formatDate(c.created_at) }}</div>
        </div>
        <van-empty v-if="!comments.length" :description="t('review.noComments')" />
        <van-field
          v-if="review.allow_comment"
          v-model="commentText"
          rows="2"
          autosize
          type="textarea"
          :placeholder="t('review.commentPlaceholder')"
        />
        <van-button
          v-if="review.allow_comment"
          type="primary"
          block
          round
          size="small"
          :loading="submitting"
          @click="handleComment"
        >
          {{ t('review.sendComment') }}
        </van-button>
      </section>
    </template>
  </div>
</template>

<style scoped>
.review-detail-page {
  min-height: 100vh;
  background: #f5f6fa;
  padding-bottom: 24px;
}

.page-loading {
  padding: 48px 0;
  display: flex;
  justify-content: center;
}

.card {
  margin: 12px;
  padding: 14px;
  background: #fff;
  border-radius: 10px;
}

.head {
  display: flex;
  gap: 10px;
  align-items: center;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #ee0a24;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.name {
  font-weight: 600;
}

.stats-line {
  font-size: 12px;
  color: #969799;
  margin-top: 4px;
}

.rate {
  margin: 10px 0;
}

.content {
  font-size: 15px;
  line-height: 1.6;
}

.img-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.img-grid img {
  width: 88px;
  height: 88px;
  object-fit: cover;
  border-radius: 8px;
}

.date, .product {
  margin-top: 8px;
  font-size: 12px;
  color: #969799;
}

.actions {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.follow-up {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #eee;
  font-size: 14px;
}

.follow-label {
  font-weight: 600;
  margin-bottom: 6px;
}

.section-title {
  font-weight: 600;
  margin-bottom: 10px;
}

.comment-item {
  padding: 8px 0;
  border-bottom: 1px solid #f5f5f5;
}

.comment-name {
  font-size: 13px;
  font-weight: 600;
}

.comment-text {
  font-size: 14px;
  margin-top: 4px;
}

.comment-date {
  font-size: 11px;
  color: #969799;
  margin-top: 4px;
}
</style>
