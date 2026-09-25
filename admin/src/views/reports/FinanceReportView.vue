<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { getFinanceSummary } from '@/api/report'

const { t, locale } = useI18n()
const loading = ref(false)
const summary = ref({})
const chartRef = ref(null)
let chartInstance = null
let trendData = []

const cards = computed(() => [
  { label: t('report.totalRevenue'), value: summary.value.total_revenue ?? '0' },
  { label: t('report.paidOrderCount'), value: summary.value.order_count ?? 0 },
  { label: t('report.avgOrderAmount'), value: summary.value.avg_order_amount ?? '0' },
])

async function loadData() {
  loading.value = true
  try {
    const res = await getFinanceSummary()
    summary.value = res.data.summary || {}
    trendData = res.data.trend || []
    await nextTick()
    renderChart(trendData)
  } finally {
    loading.value = false
  }
}

function renderChart(trend) {
  if (!chartRef.value) {
    return
  }
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  chartInstance.setOption({
    title: { text: t('report.revenueTrend30d'), left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    legend: { data: [t('dashboard.salesAmount'), t('dashboard.orderCount')], bottom: 0 },
    grid: { left: 48, right: 48, top: 48, bottom: 48 },
    xAxis: { type: 'category', data: trend.map((item) => item.date) },
    yAxis: [
      { type: 'value', name: t('dashboard.salesAmount') },
      { type: 'value', name: t('dashboard.orderCount'), position: 'right' },
    ],
    series: [
      {
        name: t('dashboard.salesAmount'),
        type: 'line',
        smooth: true,
        data: trend.map((item) => Number(item.amount)),
        itemStyle: { color: '#67c23a' },
      },
      {
        name: t('dashboard.orderCount'),
        type: 'bar',
        yAxisIndex: 1,
        data: trend.map((item) => item.order_count),
        itemStyle: { color: '#409eff' },
      },
    ],
  })
}

function handleResize() {
  chartInstance?.resize()
}

watch(locale, () => {
  if (chartInstance && trendData.length) {
    renderChart(trendData)
  }
})

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<template>
  <div v-loading="loading" class="page">
    <el-row :gutter="16" class="stat-row">
      <el-col v-for="(card, index) in cards" :key="index" :xs="24" :sm="8">
        <el-card shadow="never" class="stat-card">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-value">{{ card.value }}</div>
        </el-card>
      </el-col>
    </el-row>
    <el-card shadow="never">
      <div ref="chartRef" class="chart-box" />
    </el-card>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-card {
  margin-bottom: 16px;
}

.stat-label {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.stat-value {
  margin-top: 8px;
  font-size: 24px;
  font-weight: 600;
}

.chart-box {
  width: 100%;
  height: 400px;
}
</style>
