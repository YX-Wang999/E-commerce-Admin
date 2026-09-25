<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getSubsidyStats } from '@/api/subsidy'

const { t } = useI18n()
const loading = ref(false)
const stats = ref({
  total_subsidy_amount: '0',
  approved_product_count: 0,
  merchant_count: 0,
  submitted_count: 0,
  rejected_count: 0,
  order_count: 0,
  order_pending_report: 0,
  order_reported: 0,
  order_verified: 0,
  order_failed: 0,
})

async function fetchStats() {
  loading.value = true
  try {
    const res = await getSubsidyStats()
    stats.value = res.data || stats.value
  } finally {
    loading.value = false
  }
}

onMounted(fetchStats)
</script>

<template>
  <div v-loading="loading" class="stats-page">
    <h2>{{ t('subsidy.statsTitle') }}</h2>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">{{ t('subsidy.totalSubsidyAmount') }}</div>
        <div class="stat-value">¥{{ stats.total_subsidy_amount }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ t('subsidy.merchantCount') }}</div>
        <div class="stat-value">{{ stats.merchant_count }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ t('subsidy.approvedProductCount') }}</div>
        <div class="stat-value">{{ stats.approved_product_count }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ t('subsidy.orderCount') }}</div>
        <div class="stat-value">{{ stats.order_count }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">待上报订单</div>
        <div class="stat-value">{{ stats.order_pending_report }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">已上报</div>
        <div class="stat-value">{{ stats.order_reported }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">核验通过</div>
        <div class="stat-value">{{ stats.order_verified }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">核验失败</div>
        <div class="stat-value">{{ stats.order_failed }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">备案提交中</div>
        <div class="stat-value">{{ stats.submitted_count }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ t('subsidy.rejectedCount') }}</div>
        <div class="stat-value">{{ stats.rejected_count }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-page {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}
.stats-page h2 {
  margin: 0 0 16px;
  font-size: 18px;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}
.stat-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px;
  background: #fafafa;
}
.stat-label {
  color: #909399;
  font-size: 14px;
}
.stat-value {
  margin-top: 8px;
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}
</style>
