<script setup>
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { getProductRank } from '@/api/report'

const { t, locale } = useI18n()
const loading = ref(false)
const chartRef = ref(null)
let chartInstance = null
let rankData = []

async function loadData() {
  loading.value = true
  try {
    const res = await getProductRank({ limit: 50 })
    rankData = res.data.ranking || []
    await nextTick()
    renderChart(rankData)
  } finally {
    loading.value = false
  }
}

function renderChart(ranking) {
  if (!chartRef.value) {
    return
  }
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  const topItems = ranking.slice(0, 20)
  const names = topItems.map((item) => item.product_name).reverse()
  const values = topItems.map((item) => item.total_qty).reverse()
  chartInstance.setOption({
    title: { text: t('report.productRankTop50'), left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    grid: { left: 140, right: 24, top: 48, bottom: 24 },
    xAxis: { type: 'value' },
    yAxis: {
      type: 'category',
      data: names,
      axisLabel: { width: 120, overflow: 'truncate' },
    },
    series: [{
      type: 'bar',
      data: values,
      itemStyle: { color: '#e6a23c' },
    }],
  })
}

function handleResize() {
  chartInstance?.resize()
}

watch(locale, () => {
  if (chartInstance && rankData.length) {
    renderChart(rankData)
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
  height: 520px;
}
</style>
