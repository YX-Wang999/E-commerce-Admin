<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getSellerPointsOverview, getSellerPointsTransactions } from '@/api/sellerPoints'

const { t } = useI18n()

const loading = ref(false)
const overview = ref({ alerts: [], recent_high_issue: [], active_tenant_rules: 0 })
const transactions = ref([])
const total = ref(0)
const page = ref(1)

async function fetchOverview() {
  const res = await getSellerPointsOverview()
  overview.value = res.data || {}
}

async function fetchTransactions() {
  loading.value = true
  try {
    const res = await getSellerPointsTransactions({ page: page.value, page_size: 20 })
    transactions.value = res.data?.results || res.data || []
    total.value = res.data?.count || transactions.value.length
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await Promise.all([fetchOverview(), fetchTransactions()])
})
</script>

<template>
  <div class="page-stack">
    <el-card shadow="never">
      <template #header>
        <span>{{ t('points.sellerMonitorTitle') }}</span>
      </template>
      <p class="page-tip">{{ t('points.sellerMonitorTip') }}</p>
      <el-alert
        v-for="item in overview.alerts"
        :key="item.tenant_id"
        type="warning"
        :title="`${item.tenant_name}：${item.message}（${item.total_issued} 分）`"
        show-icon
        class="alert-item"
      />
      <el-statistic :title="t('points.activeSellerRules')" :value="overview.active_tenant_rules || 0" />
    </el-card>

    <el-card v-loading="loading" shadow="never">
      <template #header>
        <span>{{ t('points.sellerTransactionsTitle') }}</span>
      </template>
      <el-table :data="transactions" border stripe>
        <el-table-column prop="tenant_name" :label="t('points.tenantName')" min-width="120" />
        <el-table-column prop="customer_name" :label="t('points.customerName')" min-width="100" />
        <el-table-column prop="amount" :label="t('points.changeAmount')" width="90" />
        <el-table-column prop="trans_type_display" :label="t('points.changeType')" width="110" />
        <el-table-column prop="description" :label="t('points.description')" min-width="160" show-overflow-tooltip />
        <el-table-column prop="created_at" :label="t('common.createTime')" min-width="160" />
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.page-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-tip {
  margin: 0 0 12px;
  color: #909399;
  font-size: 13px;
}

.alert-item {
  margin-bottom: 8px;
}
</style>
