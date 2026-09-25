<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Box,
  ChatDotRound,
  CircleCheck,
  Comment,
  Warning,
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useAuthStore } from '@/stores/auth'
import { useRoleLabel } from '@/composables/useRoleLabel'
import { translateDashboardCard } from '@/i18n'
import { formatDashboardCardValue } from '@/utils/money'
import { getDashboardSummary, getDashboardTodos, getSalesReport } from '@/api/report'
import { getAnnouncementLatest } from '@/api/announcement'

const { t, locale } = useI18n()
const authStore = useAuthStore()
const router = useRouter()
const { roleLabels } = useRoleLabel()
const loading = ref(false)
const summary = ref({ cards: [], roles: [] })
const todos = ref({ visible: [] })
const latestAnnouncements = ref([])
const chartRef = ref(null)
let chartInstance = null

const TODO_META = {
  pending_orders: {
    icon: Box,
    colorClass: 'todo-blue',
    unitKey: 'todoUnitOrder',
    actionKey: 'todoActionProcess',
    route: { path: '/orders/list', query: { status: 'paid' } },
  },
  pending_refunds: {
    icon: ChatDotRound,
    colorClass: 'todo-orange',
    unitKey: 'todoUnitOrder',
    actionKey: 'todoActionProcess',
    route: { path: '/orders/refund' },
  },
  low_stock_products: {
    icon: Warning,
    colorClass: 'todo-red',
    unitKey: 'todoUnitProduct',
    actionKey: 'todoActionView',
    route: { path: '/products/list' },
  },
  pending_promotions: {
    icon: CircleCheck,
    colorClass: 'todo-purple',
    unitKey: 'todoUnitActivity',
    actionKey: 'todoActionReview',
    route: { path: '/promotions/seckill', query: { status: 'reviewing' } },
  },
  pending_reviews: {
    icon: Comment,
    colorClass: 'todo-teal',
    unitKey: 'todoUnitReview',
    actionKey: 'todoActionProcess',
    route: { path: '/customers/feedback', query: { status: 'pending' } },
  },
  pending_tenant_appeals: {
    icon: ChatDotRound,
    colorClass: 'todo-orange',
    unitKey: 'todoUnitReview',
    actionKey: 'todoActionProcess',
    route: { path: '/tenants/appeals', query: { status: 'pending' } },
  },
}

const showChart = computed(() => {
  const roles = summary.value.roles || []
  return roles.includes('data_analyst') || roles.includes('super_admin') || roles.includes('ops_manager')
})

const roleText = computed(() => roleLabels(authStore.user?.roles))

const visibleTodoItems = computed(() => {
  const visible = todos.value.visible || []
  return visible.map((key) => ({
    key,
    count: todos.value[key] ?? 0,
    ...TODO_META[key],
  }))
})

const hasTodoSection = computed(() => {
  const roles = summary.value.roles || []
  return (todos.value.visible || []).length > 0 || roles.includes('data_analyst')
})

const showDataAnalystMessage = computed(() => {
  const roles = summary.value.roles || []
  return roles.includes('data_analyst') && visibleTodoItems.value.length === 0
})

const todoEmptyText = computed(() => {
  const roles = summary.value.roles || []
  if (roles.includes('data_analyst') && visibleTodoItems.value.length === 0) {
    return t('dashboard.todoDataReady')
  }
  return t('dashboard.todoEmpty')
})

const allTodosClear = computed(() =>
  visibleTodoItems.value.length > 0 && visibleTodoItems.value.every((item) => item.count === 0),
)

function getCardLabel(card) {
  return translateDashboardCard(card.key, card.label)
}

function goAnnouncements() {
  router.push('/announcements')
}

function priorityTagType(priority) {
  if (priority === 'urgent') return 'danger'
  if (priority === 'important') return 'warning'
  return 'info'
}

function goTodo(item) {
  if (item.route) {
    router.push(item.route)
  }
}

function goFirstTodo() {
  const first = visibleTodoItems.value.find((item) => item.count > 0) || visibleTodoItems.value[0]
  if (first) {
    goTodo(first)
  }
}

async function fetchSummary() {
  loading.value = true
  try {
    const [summaryRes, todosRes, announcementRes] = await Promise.all([
      getDashboardSummary(),
      getDashboardTodos(),
      getAnnouncementLatest({ limit: 5 }).catch(() => ({ data: [] })),
    ])
    summary.value = summaryRes.data || { cards: [], roles: [] }
    todos.value = todosRes.data || { visible: [] }
    latestAnnouncements.value = announcementRes.data || []
    if (showChart.value) {
      await loadChart()
    }
  } finally {
    loading.value = false
  }
}

async function loadChart() {
  const salesRes = await getSalesReport()
  await nextTick()
  if (!chartRef.value) {
    return
  }
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  const trend = salesRes.data.trend || []
  chartInstance.setOption({
    title: { text: t('dashboard.salesTrend'), left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    legend: { data: [t('dashboard.orderCount'), t('dashboard.salesAmount')], bottom: 0 },
    grid: { left: 48, right: 24, top: 48, bottom: 48 },
    xAxis: { type: 'category', data: trend.map((item) => item.date) },
    yAxis: [
      { type: 'value', name: t('dashboard.orderCount') },
      { type: 'value', name: t('dashboard.salesAmount'), position: 'right' },
    ],
    series: [
      {
        name: t('dashboard.orderCount'),
        type: 'line',
        smooth: true,
        data: trend.map((item) => item.order_count),
        itemStyle: { color: '#409eff' },
      },
      {
        name: t('dashboard.salesAmount'),
        type: 'line',
        smooth: true,
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
  if (showChart.value && chartInstance) {
    loadChart()
  }
})

onMounted(() => {
  fetchSummary()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<template>
  <div v-loading="loading" class="dashboard">
    <el-row :gutter="16">
      <el-col :xs="24" :md="latestAnnouncements.length ? 16 : 24">
        <el-card shadow="never" class="welcome-card">
          <div class="welcome-header">
            <div>
              <h2>{{ t('dashboard.welcome', { name: authStore.user?.nickname || authStore.user?.username }) }}</h2>
              <p class="role-text">
                {{ t('dashboard.currentRole', { roles: roleText }) }}
              </p>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col v-if="latestAnnouncements.length" :xs="24" :md="8">
        <el-card shadow="never" class="announcement-card">
          <template #header>
            <div class="announcement-header">
              <span>{{ t('announcement.latestTitle') }}</span>
              <el-button link type="primary" @click="goAnnouncements">{{ t('announcement.viewAll') }}</el-button>
            </div>
          </template>
          <div class="announcement-list">
            <div
              v-for="item in latestAnnouncements"
              :key="item.id"
              class="announcement-item"
              @click="goAnnouncements"
            >
              <div class="announcement-item-title">
                <el-tag v-if="item.is_pinned" type="success" size="small">{{ t('announcement.pinned') }}</el-tag>
                <el-tag :type="priorityTagType(item.priority)" size="small">
                  {{ item.priority_label }}
                </el-tag>
                <span>{{ item.title }}</span>
              </div>
              <div class="announcement-item-time">{{ item.published_at }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row v-if="summary.cards.length" :gutter="16" class="stat-row">
      <el-col
        v-for="card in summary.cards"
        :key="card.key"
        :xs="12"
        :sm="12"
        :md="6"
        :lg="6"
      >
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">{{ getCardLabel(card) }}</div>
          <div class="stat-value">{{ formatDashboardCardValue(card) }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row v-if="hasTodoSection" :gutter="16" class="todo-row">
      <el-col :span="24">
        <el-card shadow="never" class="todo-panel">
          <template #header>
            <div class="todo-panel-header">
              <span>{{ t('dashboard.todos') }}</span>
              <el-button
                v-if="visibleTodoItems.some((item) => item.count > 0)"
                link
                type="primary"
                @click="goFirstTodo"
              >
                {{ t('dashboard.viewAllTodos') }} →
              </el-button>
            </div>
          </template>

          <div v-if="showDataAnalystMessage || allTodosClear" class="todo-empty">
            ✅ {{ todoEmptyText }}
          </div>
          <el-row v-else :gutter="16">
            <el-col
              v-for="item in visibleTodoItems"
              :key="item.key"
              :xs="24"
              :sm="12"
              :md="6"
            >
              <div
                class="todo-card"
                :class="item.colorClass"
                @click="goTodo(item)"
              >
                <div class="todo-card-icon">
                  <el-icon :size="28"><component :is="item.icon" /></el-icon>
                </div>
                <div class="todo-card-body">
                  <div class="todo-card-count">
                    {{ item.count }}
                    <span class="todo-card-unit">{{ t(`dashboard.${item.unitKey}`) }}</span>
                  </div>
                  <div class="todo-card-label">{{ t(`dashboard.todoItems.${item.key}`) }}</div>
                  <div class="todo-card-action">{{ t(`dashboard.${item.actionKey}`) }} →</div>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <el-row v-if="showChart" :gutter="16">
      <el-col :span="24">
        <el-card shadow="never">
          <div ref="chartRef" class="chart-box" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.welcome-card h2 {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
}
.role-text {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
.stat-row {
  margin-top: 0;
}
.stat-card {
  text-align: center;
}
.stat-label {
  color: var(--el-text-color-secondary);
  font-size: 14px;
  margin-bottom: 8px;
}
.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--el-color-primary);
}
.todo-row {
  margin-top: 0;
}
.todo-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.todo-empty {
  padding: 24px;
  text-align: center;
  color: var(--el-text-color-secondary);
  font-size: 15px;
}
.todo-card {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  margin-bottom: 16px;
  min-height: 110px;
}
.todo-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.todo-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.65);
}
.todo-card-count {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}
.todo-card-unit {
  margin-left: 4px;
  font-size: 14px;
  font-weight: 400;
}
.todo-card-label {
  margin-top: 4px;
  font-size: 14px;
  font-weight: 500;
}
.todo-card-action {
  margin-top: 8px;
  font-size: 13px;
  opacity: 0.85;
}
.todo-blue {
  background: linear-gradient(135deg, #ecf5ff, #d9ecff);
  color: #409eff;
}
.todo-orange {
  background: linear-gradient(135deg, #fdf6ec, #faecd8);
  color: #e6a23c;
}
.todo-red {
  background: linear-gradient(135deg, #fef0f0, #fde2e2);
  color: #f56c6c;
}
.todo-purple {
  background: linear-gradient(135deg, #f4ecff, #e9d8fd);
  color: #9b59b6;
}
.todo-teal {
  background: linear-gradient(135deg, #e8f8f5, #d1f2eb);
  color: #1abc9c;
}
.chart-box {
  width: 100%;
  height: 320px;
}

.announcement-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.announcement-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.announcement-item {
  cursor: pointer;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.announcement-item:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.announcement-item-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  line-height: 1.4;
}

.announcement-item-time {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.announcement-card {
  height: 100%;
}
@media (max-width: 575px) {
  .welcome-card h2 {
    font-size: 17px;
  }

  .stat-value {
    font-size: 20px;
  }

  .todo-card-count {
    font-size: 22px;
  }

  .chart-box {
    height: 260px;
  }
}
</style>
