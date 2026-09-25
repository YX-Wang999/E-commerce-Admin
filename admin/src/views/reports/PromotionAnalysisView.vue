<script setup>
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { getPromotionAnalysis } from '@/api/report'

const { t, locale } = useI18n()
const loading = ref(false)
const chartRef = ref(null)
let chartInstance = null
let chartPayload = null

async function loadData() {
  loading.value = true
  try {
    const res = await getPromotionAnalysis()
    chartPayload = res.data || {}
    await nextTick()
    renderChart(chartPayload)
  } finally {
    loading.value = false
  }
}

function renderChart(data) {
  if (!chartRef.value) {
    return
  }
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  const categories = [t('report.seckill'), t('report.groupBuy'), t('report.coupon')]
  const values = [
    data.totals?.seckill ?? 0,
    data.totals?.groupbuy ?? 0,
    data.totals?.coupon ?? 0,
  ]
  chartInstance.setOption({
    title: { text: t('report.promotionOverview'), left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 24, top: 48, bottom: 32 },
    xAxis: { type: 'category', data: categories },
    yAxis: { type: 'value', name: t('report.activityCount') },
    series: [{
      type: 'bar',
      data: values,
      itemStyle: {
        color(params) {
          const colors = ['#f56c6c', '#409eff', '#e6a23c']
          return colors[params.dataIndex] || '#909399'
        },
      },
    }],
  })
}

function handleResize() {
  chartInstance?.resize()
}

watch(locale, () => {
  if (chartInstance && chartPayload) {
    renderChart(chartPayload)
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
  height: 400px;
}
</style>
