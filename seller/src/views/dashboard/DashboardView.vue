<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { getDashboardStats } from '@/api/dashboard'
import { formatMoney } from '@/utils/money'
import { useNotifyStore } from '@/stores/notify'

const { t, locale } = useI18n()
const router = useRouter()
const notifyStore = useNotifyStore()
const loading = ref(false)
const stats = ref({
  product_count: 0,
  order_count: 0,
  order_count: 0,
  customer_count: 0,
  paid_orders: 0,
  today_orders: 0,
  today_sales: '0',
  total_revenue: '0',
  low_stock: 0,
  cancelled_orders: 0,
  sales_trend: [],
  recent_orders: [],
  low_stock_products: [],
})

const chartRef = ref(null)
let chartInstance = null

const summaryCards = computed(() => [
  { key: 'today_orders', label: t('seller.todayOrders'), highlight: true },
  { key: 'order_count', label: t('seller.orderCount') },
  { key: 'paid_orders', label: t('seller.paidOrders') },
  { key: 'total_revenue', label: t('seller.totalRevenue'), format: 'money' },
  { key: 'cancelled_orders', label: t('seller.cancelledOrders') },
  { key: 'customer_count', label: t('seller.customerCount') },
])

function formatCardValue(item) {
  const raw = stats.value[item.key] ?? 0
  if (item.format === 'money') {
    return formatMoney(raw)
  }
  return raw
}

const statusMap = computed(() => ({
  pending: t('order.statusPending'),
  paid: t('order.statusPaid'),
  shipped: t('order.statusShipped'),
  completed: t('order.statusCompleted'),
  cancelled: t('order.statusCancelled'),
  refunding: t('order.statusRefunding'),
}))

const appealBanner = computed(() => notifyStore.latestReply)

const appealBannerText = computed(() => {
  if (!appealBanner.value) return ''
  const time = new Date(appealBanner.value.created_at).toLocaleString()
  return t('seller.appealBanner', { time })
})

function formatDateTime(value) {
  if (!value) return '-'
  return String(value).replace('T', ' ').slice(0, 19)
}

function renderChart() {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  const trend = stats.value.sales_trend || []
  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 24, top: 24, bottom: 32 },
    xAxis: {
      type: 'category',
      data: trend.map((item) => item.date?.slice(5) || ''),
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: t('seller.todaySales'),
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.15 },
        data: trend.map((item) => Number(item.amount || 0)),
      },
    ],
  })
}

function handleResize() {
  chartInstance?.resize()
}

async function fetchStats() {
  loading.value = true
  try {
    const res = await getDashboardStats()
    stats.value = { ...stats.value, ...res.data }
    await nextTick()
    renderChart()
  } finally {
    loading.value = false
  }
}

function goOrders(status) {
  router.push(status ? { path: '/orders', query: { status } } : '/orders')
}

function goOrderDetail(row) {
  router.push({ name: 'OrderDetail', params: { id: row.id } })
}

function goProducts() {
  router.push('/products')
}

watch(locale, () => {
  renderChart()
})

onMounted(async () => {
  await Promise.all([fetchStats(), notifyStore.refreshSummary()])
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<template>
  <div v-loading="loading">
    <el-alert
      v-if="notifyStore.bannerVisible && appealBanner"
      type="warning"
      show-icon
      :closable="false"
      class="appeal-banner"
      @click="notifyStore.openAppealDrawer(appealBanner.appeal_id, appealBanner.id)"
    >
      <template #title>⚠️ {{ appealBannerText }}</template>
    </el-alert>

    <el-alert
      v-if="stats.paid_orders > 0"
      type="warning"
      show-icon
      :closable="false"
      class="pending-banner"
    >
      <template #title>
        {{ t('seller.pendingShipAlert', { count: stats.paid_orders }) }}
        <el-button type="warning" link @click="goOrders('paid')">{{ t('seller.viewPendingShip') }} →</el-button>
      </template>
    </el-alert>

    <div class="page-header">
      <h2>{{ t('seller.dashboard') }}</h2>
    </div>

    <el-row :gutter="16" class="summary-row">
      <el-col v-for="item in summaryCards" :key="item.key" :xs="24" :sm="12" :md="8" :lg="4">
        <div class="stat-card" :class="{ highlight: item.highlight }">
          <div class="stat-value">{{ formatCardValue(item) }}</div>
          <div class="stat-label">{{ item.label }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="14">
        <div class="panel-card">
          <div class="panel-header">
            <h3>{{ t('seller.salesTrend') }}</h3>
          </div>
          <div ref="chartRef" class="chart-box" />
        </div>
      </el-col>
      <el-col :xs="24" :lg="10">
        <div class="panel-card">
          <div class="panel-header">
            <h3>{{ t('seller.lowStockList') }}</h3>
            <el-button link type="primary" @click="goProducts">{{ t('seller.products') }}</el-button>
          </div>
          <el-table :data="stats.low_stock_products" size="small" max-height="280">
            <el-table-column prop="name" :label="t('seller.productName')" min-width="120" show-overflow-tooltip />
            <el-table-column prop="stock" :label="t('seller.stock')" width="80">
              <template #default="{ row }">
                <el-tag type="danger" size="small">{{ row.stock }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!stats.low_stock_products?.length" :description="t('common.noData')" />
        </div>
      </el-col>
    </el-row>

    <div class="panel-card recent-panel">
      <div class="panel-header">
        <h3>{{ t('seller.recentOrders') }}</h3>
        <el-button link type="primary" @click="goOrders()">{{ t('seller.viewAllOrders') }}</el-button>
      </div>
      <el-table :data="stats.recent_orders" size="small" @row-click="goOrderDetail">
        <el-table-column prop="order_no" :label="t('order.orderNo')" min-width="150" />
        <el-table-column :label="t('seller.customer')" min-width="100">
          <template #default="{ row }">{{ row.customer_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="total_amount" :label="t('seller.amount')" width="90" />
        <el-table-column :label="t('seller.status')" width="100">
          <template #default="{ row }">{{ statusMap[row.status] || row.status }}</template>
        </el-table-column>
        <el-table-column :label="t('seller.orderTime')" width="160">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.appeal-banner,
.pending-banner {
  margin-bottom: 16px;
  cursor: pointer;
}

.pending-banner {
  cursor: default;
}

.summary-row {
  margin-bottom: 16px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.stat-card.highlight {
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  color: #fff;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  margin-top: 8px;
  font-size: 14px;
  opacity: 0.8;
}

.panel-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
}

.chart-box {
  height: 280px;
}

.recent-panel :deep(.el-table__row) {
  cursor: pointer;
}
</style>
