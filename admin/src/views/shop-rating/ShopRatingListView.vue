<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getRatingAdjustments,
  getShopRatingAlerts,
  getShopRatings,
  reviewRatingAdjustment,
} from '@/api/shopRating'

const { t } = useI18n()

const activeTab = ref('ratings')
const ratingsLoading = ref(false)
const adjustmentsLoading = ref(false)
const alertsLoading = ref(false)
const ratings = ref([])
const adjustments = ref([])
const alerts = ref([])
const lowOnly = ref(true)

const adjustmentStatus = ref('pending')

const ADJUSTMENT_STATUS = {
  pending: { label: t('shopRating.statusPending'), type: 'warning' },
  approved: { label: t('shopRating.statusApproved'), type: 'success' },
  rejected: { label: t('shopRating.statusRejected'), type: 'info' },
}

async function fetchRatings() {
  ratingsLoading.value = true
  try {
    const res = await getShopRatings({ low_only: lowOnly.value ? 'true' : 'false' })
    ratings.value = res.data || []
  } finally {
    ratingsLoading.value = false
  }
}

async function fetchAdjustments() {
  adjustmentsLoading.value = true
  try {
    const params = {}
    if (adjustmentStatus.value) {
      params.status = adjustmentStatus.value
    }
    const res = await getRatingAdjustments(params)
    adjustments.value = res.data || []
  } finally {
    adjustmentsLoading.value = false
  }
}

async function fetchAlerts() {
  alertsLoading.value = true
  try {
    const res = await getShopRatingAlerts({ days: 7 })
    alerts.value = res.data || []
  } finally {
    alertsLoading.value = false
  }
}

function handleTabChange(name) {
  if (name === 'ratings') {
    fetchRatings()
  } else if (name === 'adjustments') {
    fetchAdjustments()
  } else if (name === 'alerts') {
    fetchAlerts()
  }
}

async function handleReview(row, status) {
  const isApprove = status === 'approved'
  try {
    const { value } = await ElMessageBox.prompt(
      t(isApprove ? 'shopRating.approvePrompt' : 'shopRating.rejectPrompt'),
      t(isApprove ? 'shopRating.approve' : 'shopRating.reject'),
      {
        inputValue: '',
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
      },
    )
    await reviewRatingAdjustment(row.id, { status, review_note: value || '' })
    ElMessage.success(t('common.success'))
    fetchAdjustments()
    fetchRatings()
  } catch {
    /* cancelled */
  }
}

onMounted(() => {
  fetchRatings()
})
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <span>{{ t('shopRating.listTitle') }}</span>
    </template>

    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane :label="t('shopRating.tabRatings')" name="ratings">
        <div class="toolbar">
          <el-checkbox v-model="lowOnly" @change="fetchRatings">
            {{ t('shopRating.lowOnly') }}
          </el-checkbox>
          <el-button @click="fetchRatings">{{ t('common.refresh') }}</el-button>
        </div>
        <el-table v-loading="ratingsLoading" :data="ratings" stripe>
          <el-table-column prop="tenant_name" :label="t('shopRating.tenant')" min-width="140" />
          <el-table-column prop="tenant_code" :label="t('shopRating.tenantCode')" width="120" />
          <el-table-column prop="overall_score" :label="t('shopRating.overallScore')" width="100" />
          <el-table-column prop="rating_label" :label="t('shopRating.ratingLabel')" width="100" />
          <el-table-column prop="total_ratings" :label="t('shopRating.totalRatings')" width="100" />
          <el-table-column prop="quality_score" :label="t('shopRating.qualityScore')" width="100" />
          <el-table-column prop="service_score" :label="t('shopRating.serviceScore')" width="100" />
          <el-table-column prop="logistics_score" :label="t('shopRating.logisticsScore')" width="100" />
          <el-table-column prop="updated_at" :label="t('common.updatedAt')" width="170" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane :label="t('shopRating.tabAdjustments')" name="adjustments">
        <div class="toolbar">
          <el-select v-model="adjustmentStatus" style="width: 160px" @change="fetchAdjustments">
            <el-option :label="t('shopRating.statusPending')" value="pending" />
            <el-option :label="t('shopRating.statusApproved')" value="approved" />
            <el-option :label="t('shopRating.statusRejected')" value="rejected" />
            <el-option :label="t('common.all')" value="" />
          </el-select>
          <el-button @click="fetchAdjustments">{{ t('common.refresh') }}</el-button>
        </div>
        <el-table v-loading="adjustmentsLoading" :data="adjustments" stripe>
          <el-table-column prop="tenant_name" :label="t('shopRating.tenant')" min-width="140" />
          <el-table-column prop="current_score" :label="t('shopRating.currentScore')" width="100" />
          <el-table-column prop="requested_score" :label="t('shopRating.requestedScore')" width="100" />
          <el-table-column prop="reason" :label="t('shopRating.reason')" min-width="180" show-overflow-tooltip />
          <el-table-column prop="status" :label="t('common.status')" width="100">
            <template #default="{ row }">
              <el-tag :type="ADJUSTMENT_STATUS[row.status]?.type || 'info'" size="small">
                {{ ADJUSTMENT_STATUS[row.status]?.label || row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" :label="t('common.createdAt')" width="170" />
          <el-table-column :label="t('common.actions')" width="180" fixed="right">
            <template #default="{ row }">
              <template v-if="row.status === 'pending'">
                <el-button link type="success" @click="handleReview(row, 'approved')">
                  {{ t('shopRating.approve') }}
                </el-button>
                <el-button link type="danger" @click="handleReview(row, 'rejected')">
                  {{ t('shopRating.reject') }}
                </el-button>
              </template>
              <span v-else class="text-muted">{{ row.review_note || '—' }}</span>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane :label="t('shopRating.tabAlerts')" name="alerts">
        <div class="toolbar">
          <el-button @click="fetchAlerts">{{ t('common.refresh') }}</el-button>
        </div>
        <el-table v-loading="alertsLoading" :data="alerts" stripe>
          <el-table-column prop="tenant_name" :label="t('shopRating.tenant')" min-width="140" />
          <el-table-column prop="total" :label="t('shopRating.alertTotal')" width="100" />
          <el-table-column prop="five_star" :label="t('shopRating.alertFiveStar')" width="100" />
          <el-table-column prop="one_star" :label="t('shopRating.alertOneStar')" width="100" />
        </el-table>
        <el-empty v-if="!alertsLoading && !alerts.length" :description="t('shopRating.noAlerts')" />
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.text-muted {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
</style>
