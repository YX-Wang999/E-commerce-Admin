<script setup>
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { getProductRank, getSalesReport } from '@/api/report'

const { t, locale } = useI18n()

const loading = ref(false)
const salesChartRef = ref(null)
const rankChartRef = ref(null)
let salesChart = null
let rankChart = null
let salesTrendData = []
let rankData = []

async function loadData() {
  loading.value = true
  try {
    const [salesRes, rankRes] = await Promise.all([
      getSalesReport(),
      getProductRank(),
    ])
    salesTrendData = salesRes.data.trend || []
    rankData = rankRes.data.ranking || []
    await nextTick()
    renderSalesChart(salesTrendData)
    renderRankChart(rankData)
  } finally {
    loading.value = false
  }
}

function renderSalesChart(trend) {
  if (!salesChartRef.value) {
    return
  }
  if (!salesChart) {
    salesChart = echarts.init(salesChartRef.value)
  }
  salesChart.setOption({
    title: { text: t('report.salesTrend7d'), left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    legend: { data: [t('dashboard.orderCount'), t('dashboard.salesAmount')], bottom: 0 },
    grid: { left: 48, right: 24, top: 48, bottom: 48 },
    xAxis: {
      type: 'category',
      data: trend.map((item) => item.date),
    },
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

function renderRankChart(ranking) {
  if (!rankChartRef.value) {
    return
  }
  if (!rankChart) {
    rankChart = echarts.init(rankChartRef.value)
  }
  const names = ranking.map((item) => item.product_name).reverse()
  const values = ranking.map((item) => item.total_qty).reverse()
  rankChart.setOption({
    title: { text: t('report.productRankTop10'), left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    grid: { left: 120, right: 24, top: 48, bottom: 24 },
    xAxis: { type: 'value' },
    yAxis: {
      type: 'category',
      data: names,
      axisLabel: { width: 100, overflow: 'truncate' },
    },
    series: [
      {
        type: 'bar',
        data: values,
        itemStyle: { color: '#e6a23c' },
      },
    ],
  })
}

function handleResize() {
  salesChart?.resize()
  rankChart?.resize()
}

watch(locale, () => {
  if (salesChart && salesTrendData.length) {
    renderSalesChart(salesTrendData)
  }
  if (rankChart && rankData.length) {
    renderRankChart(rankData)
  }
})

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  salesChart?.dispose()
  rankChart?.dispose()
})
</script>

<template>
  <div v-loading="loading" class="report-page">
    <el-row :gutter="16">
      <el-col :span="14">
        <el-card shadow="never">
          <div ref="salesChartRef" class="chart-box" />
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card shadow="never">
          <div ref="rankChartRef" class="chart-box" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.report-page {
  min-height: 400px;
}
.chart-box {
  width: 100%;
  height: 360px;
}
</style>
