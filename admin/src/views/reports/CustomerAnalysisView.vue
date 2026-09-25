<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { getCustomerAnalysis } from '@/api/report'

const { t, locale } = useI18n()
const loading = ref(false)
const summary = ref({})
const chartRef = ref(null)
let chartInstance = null
let growthData = []

const cards = computed(() => [
  { label: t('report.totalCustomers'), value: summary.value.total_customers ?? 0 },
  { label: t('report.customersWithOrders'), value: summary.value.customers_with_orders ?? 0 },
  { label: t('report.repeatCustomers'), value: summary.value.repeat_customers ?? 0 },
  { label: t('report.repeatRate'), value: `${summary.value.repeat_rate ?? 0}%` },
])

async function loadData() {
  loading.value = true
  try {
    const res = await getCustomerAnalysis()
    summary.value = res.data.summary || {}
    growthData = res.data.growth || []
    await nextTick()
    renderChart(growthData)
  } finally {
    loading.value = false
  }
}

function renderChart(growth) {
  if (!chartRef.value) {
    return
  }
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  chartInstance.setOption({
    title: { text: t('report.customerGrowth7d'), left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 24, top: 48, bottom: 32 },
    xAxis: { type: 'category', data: growth.map((item) => item.date) },
    yAxis: { type: 'value', name: t('report.newCustomers') },
    series: [{
      type: 'line',
      smooth: true,
      data: growth.map((item) => item.new_count),
      itemStyle: { color: '#67c23a' },
      areaStyle: { color: 'rgba(103, 194, 58, 0.15)' },
    }],
  })
}

function handleResize() {
  chartInstance?.resize()
}

watch(locale, () => {
  if (chartInstance && growthData.length) {
    renderChart(growthData)
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
      <el-col v-for="(card, index) in cards" :key="index" :xs="12" :sm="6">
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
  height: 360px;
}
</style>
