<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import {
  applyRatingAdjustment,
  getRatingAdjustments,
  getShopRating,
  getShopRatingReviews,
} from '@/api/shopRating'

const { t } = useI18n()

const loading = ref(false)
const rating = ref(null)
const reviews = ref([])
const adjustments = ref([])
const submitting = ref(false)

const form = reactive({
  requested_score: 4.5,
  reason: '',
})

const canApply = computed(() => !adjustments.value.some((row) => row.status === 'pending'))

async function fetchAll() {
  loading.value = true
  try {
    const [ratingRes, reviewRes, adjRes] = await Promise.all([
      getShopRating(),
      getShopRatingReviews(),
      getRatingAdjustments(),
    ])
    rating.value = ratingRes.data
    reviews.value = reviewRes.data || []
    adjustments.value = adjRes.data || []
    if (rating.value?.overall_score != null) {
      form.requested_score = Number(rating.value.overall_score)
    }
  } finally {
    loading.value = false
  }
}

async function handleApply() {
  if (!form.reason.trim()) {
    ElMessage.warning(t('sellerShopRating.reasonRequired'))
    return
  }
  submitting.value = true
  try {
    await applyRatingAdjustment({
      requested_score: Number(form.requested_score),
      reason: form.reason.trim(),
    })
    ElMessage.success(t('sellerShopRating.applySuccess'))
    form.reason = ''
    await fetchAll()
  } finally {
    submitting.value = false
  }
}

onMounted(fetchAll)
</script>

<template>
  <div v-loading="loading" class="page-wrap">
    <el-card shadow="never">
      <template #header>{{ t('sellerShopRating.title') }}</template>
      <el-descriptions v-if="rating" :column="2" border>
        <el-descriptions-item :label="t('sellerShopRating.overallScore')">
          {{ rating.overall_score }}（{{ rating.rating_label }}）
        </el-descriptions-item>
        <el-descriptions-item :label="t('sellerShopRating.totalRatings')">
          {{ rating.total_ratings }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('sellerShopRating.qualityScore')">
          {{ rating.quality_score }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('sellerShopRating.serviceScore')">
          {{ rating.service_score }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('sellerShopRating.logisticsScore')">
          {{ rating.logistics_score }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card shadow="never" class="mt-16">
      <template #header>{{ t('sellerShopRating.reviewsTitle') }}</template>
      <el-table :data="reviews" stripe>
        <el-table-column prop="quality_score" :label="t('sellerShopRating.qualityScore')" width="90" />
        <el-table-column prop="service_score" :label="t('sellerShopRating.serviceScore')" width="90" />
        <el-table-column prop="logistics_score" :label="t('sellerShopRating.logisticsScore')" width="90" />
        <el-table-column prop="content" :label="t('sellerShopRating.reviewContent')" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" :label="t('sellerShopRating.reviewTime')" width="170" />
      </el-table>
      <el-empty v-if="!reviews.length" :description="t('sellerShopRating.noReviews')" />
    </el-card>

    <el-card shadow="never" class="mt-16">
      <template #header>{{ t('sellerShopRating.adjustTitle') }}</template>
      <p class="tip">{{ t('sellerShopRating.adjustTip') }}</p>
      <el-form :inline="true" class="adjust-form">
        <el-form-item :label="t('sellerShopRating.requestedScore')">
          <el-input-number
            v-model="form.requested_score"
            :min="1"
            :max="5"
            :step="0.1"
            :precision="1"
          />
        </el-form-item>
        <el-form-item :label="t('sellerShopRating.reason')" class="reason-item">
          <el-input v-model="form.reason" :placeholder="t('sellerShopRating.reasonPlaceholder')" style="width: 320px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" :disabled="!canApply" @click="handleApply">
            {{ t('sellerShopRating.submitApply') }}
          </el-button>
        </el-form-item>
      </el-form>
      <el-table :data="adjustments" stripe>
        <el-table-column prop="current_score" :label="t('sellerShopRating.currentScore')" width="100" />
        <el-table-column prop="requested_score" :label="t('sellerShopRating.requestedScore')" width="100" />
        <el-table-column prop="reason" :label="t('sellerShopRating.reason')" min-width="160" show-overflow-tooltip />
        <el-table-column prop="status" :label="t('seller.status')" width="100" />
        <el-table-column prop="review_note" :label="t('sellerShopRating.reviewNote')" min-width="140" show-overflow-tooltip />
        <el-table-column prop="created_at" :label="t('sellerShopRating.applyTime')" width="170" />
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.page-wrap {
  padding: 0;
}

.mt-16 {
  margin-top: 16px;
}

.tip {
  margin: 0 0 12px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.adjust-form {
  margin-bottom: 12px;
}

.reason-item {
  margin-right: 0;
}
</style>
