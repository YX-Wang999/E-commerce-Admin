<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { getOrgChart } from '@/api/org'
import { useRoleLabel } from '@/composables/useRoleLabel'

const { t, locale } = useI18n()
const { roleLabel } = useRoleLabel()

const loading = ref(false)
const chartRef = ref(null)
const rawNodes = ref([])
let chartInstance = null

const ROLE_COLORS = {
  super_admin: '#f56c6c',
  ops_director: '#e6a23c',
  ops_manager: '#409eff',
  ops_staff: '#79bbff',
  dept_manager: '#67c23a',
  cs_staff: '#b88230',
  warehouse_manager: '#909399',
  data_analyst: '#9b59b6',
  employee: '#c0c4cc',
}

const LEGEND_CODES = [
  'super_admin', 'ops_director', 'ops_manager', 'ops_staff',
  'dept_manager', 'cs_staff', 'warehouse_manager', 'data_analyst', 'employee',
]

const LEGEND_I18N_FALLBACK = {
  super_admin: 'login.demoRoles.admin',
  ops_director: 'login.demoRoles.opsDirector',
  ops_manager: 'login.demoRoles.opsManager',
  ops_staff: 'login.demoRoles.opsStaff',
  dept_manager: 'login.demoRoles.deptManager',
  cs_staff: 'login.demoRoles.csStaff',
  warehouse_manager: 'login.demoRoles.warehouse',
  data_analyst: 'login.demoRoles.dataAnalyst',
  employee: 'login.demoRoles.employee',
}

const legendItems = computed(() =>
  LEGEND_CODES.map((code) => ({
    code,
    label: roleLabel(code, t(LEGEND_I18N_FALLBACK[code] || code)),
    color: ROLE_COLORS[code] || '#606266',
  })),
)

function roleColor(role) {
  return ROLE_COLORS[role] || '#606266'
}

function nodeRoleLabel(node) {
  return roleLabel(node.role, node.role_name || node.role || '-')
}

function toEchartsNode(node) {
  const label = node.display_name || node.username
  return {
    name: label,
    display_name: label,
    username: node.username,
    role: node.role,
    role_name: node.role_name,
    department: node.department,
    itemStyle: {
      color: roleColor(node.role),
      borderColor: '#fff',
      borderWidth: 1,
    },
    label: {
      backgroundColor: roleColor(node.role),
      color: '#fff',
      padding: [4, 8],
      borderRadius: 4,
    },
    children: (node.children || []).map(toEchartsNode),
  }
}

function buildChartData(nodes) {
  if (!nodes?.length) {
    return [{
      name: t('org.empty'),
      itemStyle: { color: '#dcdfe6' },
    }]
  }
  if (nodes.length === 1) {
    return [toEchartsNode(nodes[0])]
  }
  return [{
    name: t('org.companyRoot'),
    itemStyle: { color: '#303133' },
    label: { backgroundColor: '#303133', color: '#fff', padding: [4, 8], borderRadius: 4 },
    children: nodes.map(toEchartsNode),
  }]
}

function renderChart() {
  if (!chartRef.value) {
    return
  }
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  const chartData = buildChartData(rawNodes.value)
  chartInstance.setOption({
    tooltip: {
      trigger: 'item',
      formatter(params) {
        const data = params.data || {}
        return [
          `<strong>${data.display_name || data.name || '-'}</strong>`,
          `${t('org.tooltipRole')}：${nodeRoleLabel(data)}`,
          `${t('org.tooltipDepartment')}：${data.department || '-'}`,
          `${t('org.tooltipUsername')}：${data.username || '-'}`,
        ].join('<br/>')
      },
    },
    series: [{
      type: 'tree',
      data: chartData,
      top: '4%',
      left: '8%',
      bottom: '4%',
      right: '22%',
      symbol: 'roundRect',
      symbolSize: [10, 10],
      orient: 'LR',
      expandAndCollapse: true,
      initialTreeDepth: 3,
      animationDuration: 550,
      animationDurationUpdate: 750,
      label: {
        position: 'left',
        verticalAlign: 'middle',
        align: 'right',
        fontSize: 13,
        formatter(params) {
          const data = params.data || {}
          const role = data.role ? nodeRoleLabel(data) : ''
          return role ? `${data.display_name || data.name}\n(${role})` : (data.display_name || data.name)
        },
      },
      leaves: {
        label: {
          position: 'right',
          align: 'left',
        },
      },
      lineStyle: {
        color: '#c0c4cc',
        width: 1.5,
        curveness: 0.5,
      },
    }],
  }, true)
}

function handleResize() {
  chartInstance?.resize()
}

async function fetchChart() {
  loading.value = true
  try {
    const res = await getOrgChart()
    rawNodes.value = res.data?.nodes || []
    await nextTick()
    renderChart()
  } finally {
    loading.value = false
  }
}

watch(locale, () => {
  renderChart()
})

onMounted(async () => {
  await fetchChart()
  window.addEventListener('resize', handleResize, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<template>
  <el-card v-loading="loading" shadow="never" class="org-card">
    <template #header>
      <div class="card-header">
        <span>{{ t('org.title') }}</span>
        <el-button type="primary" link @click="fetchChart">{{ t('org.refresh') }}</el-button>
      </div>
    </template>

    <div class="legend">
      <span v-for="item in legendItems" :key="item.code" class="legend-item">
        <i class="legend-dot" :style="{ backgroundColor: item.color }" />
        {{ item.label }}
      </span>
    </div>

    <div ref="chartRef" class="org-chart" />
  </el-card>
</template>

<style scoped>
.org-card {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 140px);
}

.org-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 20px;
  margin-bottom: 12px;
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.org-chart {
  flex: 1;
  width: 100%;
  min-height: 560px;
}
</style>
