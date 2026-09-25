<script setup>
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { getSalesReport } from '@/api/report'

const { t, locale } = useI18n()
const loading = ref(false)
const chartRef = ref(null)
let chartInstance = null
let trendData = []

async function loadData() {
  loading.value = true
  try {
    const res = await getSalesReport()
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
    title: { text: t('report.salesTrend7d'), left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    legend: { data: [t('dashboard.orderCount'), t('dashboard.salesAmount')], bottom: 0 },
    grid: { left: 48, right: 48, top: 48, bottom: 48 },
    xAxis: { type: 'category', data: trend.map((item) => item.date) },
    yAxis: [
      { type: 'value', name: t('dashboard.orderCount') },
      { type: 'value', name: t('dashboard.salesAmount'), position: 'right' },
    ],
    series: [
      {
        name: t('dashboard.orderCount'),
        type: 'bar',
        data: trend.map((item) => item.order_count),
        itemStyle: { color: '#409eff' },
      },
      {
        name: t('dashboard.salesAmount'),
        type: 'line',
        yAxisIndex: 1,
        data: trend.map((item) => Number(item.amount)),
        itemStyle: { color: '#67c23a' },
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
  <el-card v-loading="loading" shadow="never">
    <div ref="chartRef" class="chart-box" />
  </el-card>
</template>

<style scoped>
.chart-box {
  width: 100%;
  height: 420px;
}
</style>
