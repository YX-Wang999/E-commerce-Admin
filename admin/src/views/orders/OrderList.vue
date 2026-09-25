<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { exportOrders, getOrderList, getOrderDetail, shipOrder, forceCancelOrder, reviewCancelOrder, getCancelStats } from '@/api/order'
import { getExpressCompanies } from '@/api/logistics'
import TableActionMenu from '@/components/TableActionMenu.vue'
import LogisticsTracePanel from '@/components/orders/LogisticsTracePanel.vue'
import { ACTION_COLUMN } from '@/config/table'
import { useOrderBadgeStore } from '@/stores/orderBadge'

const { t } = useI18n()
const route = useRoute()
const orderBadgeStore = useOrderBadgeStore()

const loading = ref(false)
const exporting = ref(false)
const detailVisible = ref(false)
const shipVisible = ref(false)
const forceCancelVisible = ref(false)
const reviewVisible = ref(false)
const detailLoading = ref(false)
const forceCancelSubmitting = ref(false)
const reviewSubmitting = ref(false)
const shipFormRef = ref(null)
const forceCancelFormRef = ref(null)
const tableData = ref([])
const currentOrder = ref(null)
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ keyword: '', status: '', dateRange: null })

const shipForm = reactive({
  orderId: null,
  express_code: '',
  logistics_no: '',
})

const forceCancelForm = reactive({
  orderId: null,
  reason: '',
})

const reviewForm = reactive({
  orderId: null,
  orderNo: '',
  customerName: '',
  reason: '',
  detail: '',
  remark: '',
})

const cancelStats = ref(null)

const expressCompanies = ref([])

const shipRules = computed(() => ({
  express_code: [{ required: true, message: t('logistics.expressRequired'), trigger: 'change' }],
  logistics_no: [{ required: true, message: t('order.logisticsRequired'), trigger: 'blur' }],
}))

const forceCancelRules = computed(() => ({
  reason: [{ required: true, message: t('order.forceCancelReasonRequired'), trigger: 'blur' }],
}))

const STATUS_MAP = computed(() => ({
  pending: { label: t('order.statusPending'), type: 'info' },
  paid: { label: t('order.statusPaid'), type: 'primary' },
  shipped: { label: t('order.statusShipped'), type: 'warning' },
  completed: { label: t('order.statusCompleted'), type: 'success' },
  cancelled: { label: t('order.statusCancelled'), type: 'danger' },
  refunding: { label: t('order.statusRefunding'), type: 'danger' },
}))

const STATUS_FLOW = ['pending', 'paid', 'shipped', 'completed']

function canForceCancel(order) {
  if (!order) return false
  return !['cancelled', 'shipped', 'completed'].includes(order.status)
}

function isCanceling(order) {
  return order?.status === 'paid' && order?.cancel_status === 'pending'
}

function canShip(order) {
  return order?.status === 'paid' && order?.cancel_status !== 'pending'
}

function rowStatusKey(row) {
  if (isCanceling(row)) return 'canceling'
  return row.status
}

function rowStatusLabel(row) {
  if (isCanceling(row)) return t('order.statusCanceling')
  return STATUS_MAP.value[row.status]?.label || row.status
}

function rowStatusType(row) {
  if (isCanceling(row)) return 'warning'
  return STATUS_MAP.value[row.status]?.type || 'info'
}

const pendingShipmentCount = computed(() => orderBadgeStore.pendingShipmentCount)
const cancelingCount = computed(() => orderBadgeStore.cancelingCount)

const cancelActionLabels = computed(() => ({
  auto: t('order.cancelActionAuto'),
  user_direct: t('order.cancelActionUserDirect'),
  user_apply: t('order.cancelActionUserApply'),
  merchant_approve: t('order.cancelActionMerchantApprove'),
  merchant_reject: t('order.cancelActionMerchantReject'),
  merchant_cancel: t('order.cancelActionMerchantCancel'),
  platform_cancel: t('order.cancelActionPlatformCancel'),
}))

const showPendingAlert = computed(() => pendingShipmentCount.value > 0)
const showCancelingAlert = computed(() => cancelingCount.value > 0)

function viewPendingShipments() {
  filters.status = 'paid'
  pagination.page = 1
  fetchList()
}

function viewCancelingOrders() {
  filters.status = 'canceling'
  pagination.page = 1
  fetchList()
}

function statusFlowIndex(status) {
  if (status === 'cancelled' || status === 'refunding') return -1
  const index = STATUS_FLOW.indexOf(status)
  return index >= 0 ? index : STATUS_FLOW.length - 1
}

function formatDateTime(value) {
  if (!value) return '-'
  return String(value).replace('T', ' ').slice(0, 19)
}

function buildQueryParams() {
  return {
    keyword: filters.keyword || undefined,
    status: filters.status || undefined,
    start_date: filters.dateRange?.[0],
    end_date: filters.dateRange?.[1],
  }
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getOrderList({
      page: pagination.page,
      page_size: pagination.pageSize,
      ...buildQueryParams(),
    })
    tableData.value = res.data.results || []
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

async function handleExport() {
  if (exporting.value) {
    return
  }
  exporting.value = true
  try {
    const response = await exportOrders(buildQueryParams())
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '')
    link.href = url
    link.download = `orders_${dateStr}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    ElMessage.success(t('common.exportSuccess'))
  } catch {
    ElMessage.error(t('common.exportFailed'))
  } finally {
    exporting.value = false
  }
}

function handleDetail(row) {
  currentOrder.value = row
  detailVisible.value = true
  loadOrderDetail(row.id)
}

async function loadOrderDetail(id) {
  detailLoading.value = true
  try {
    const res = await getOrderDetail(id)
    currentOrder.value = res.data
  } finally {
    detailLoading.value = false
  }
}

async function loadCancelStats() {
  try {
    const res = await getCancelStats()
    cancelStats.value = res.data
  } catch {
    cancelStats.value = null
  }
}

function openForceCancel(order) {
  forceCancelForm.orderId = order.id
  forceCancelForm.reason = ''
  forceCancelVisible.value = true
}

async function submitForceCancel() {
  await forceCancelFormRef.value.validate()
  forceCancelSubmitting.value = true
  try {
    const res = await forceCancelOrder(forceCancelForm.orderId, { reason: forceCancelForm.reason })
    ElMessage.success(t('order.forceCancelSuccess'))
    forceCancelVisible.value = false
    if (detailVisible.value && currentOrder.value?.id === forceCancelForm.orderId) {
      currentOrder.value = res.data
    }
    await Promise.all([fetchList(), loadCancelStats(), orderBadgeStore.refresh()])
  } finally {
    forceCancelSubmitting.value = false
  }
}

function openCancelReview(order) {
  reviewForm.orderId = order.id
  reviewForm.orderNo = order.order_no
  reviewForm.customerName = order.customer_name || '-'
  reviewForm.reason = order.cancel_reason || '-'
  reviewForm.detail = order.cancel_detail || '-'
  reviewForm.remark = ''
  reviewVisible.value = true
}

async function submitCancelReview(approve) {
  reviewSubmitting.value = true
  try {
    const res = await reviewCancelOrder(reviewForm.orderId, {
      approve,
      remark: reviewForm.remark,
    })
    ElMessage.success(t('order.cancelReviewSuccess'))
    reviewVisible.value = false
    if (detailVisible.value && currentOrder.value?.id === reviewForm.orderId) {
      currentOrder.value = res.data
    }
    await Promise.all([fetchList(), loadCancelStats(), orderBadgeStore.refresh()])
  } finally {
    reviewSubmitting.value = false
  }
}

function handleShip(row) {
  shipForm.orderId = row.id
  shipForm.express_code = ''
  shipForm.logistics_no = ''
  shipVisible.value = true
}

async function submitShip() {
  await shipFormRef.value.validate()
  const res = await shipOrder(shipForm.orderId, {
    express_code: shipForm.express_code,
    tracking_number: shipForm.logistics_no,
  })
  ElMessage.success(t('order.shipSuccess'))
  shipVisible.value = false
  if (detailVisible.value && currentOrder.value?.id === shipForm.orderId) {
    currentOrder.value = res.data
  }
  await fetchList()
  orderBadgeStore.refresh()
}

async function loadExpressCompanies() {
  try {
    const res = await getExpressCompanies()
    expressCompanies.value = res.data || []
  } catch {
    expressCompanies.value = []
  }
}

onMounted(async () => {
  if (route.query.status) {
    filters.status = String(route.query.status)
  }
  await Promise.all([orderBadgeStore.refresh(), loadExpressCompanies(), loadCancelStats()])
  fetchList()
})
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>{{ t('order.listTitle') }}</span>
        <div class="header-actions">
          <span v-if="cancelStats" class="cancel-stats">
            {{ t('order.cancelStatsSummary', {
              total: cancelStats.cancelled_total || 0,
              canceling: cancelStats.canceling_count || 0,
            }) }}
          </span>
          <el-button type="success" :loading="exporting" @click="handleExport">
            {{ t('order.exportExcel') }}
          </el-button>
        </div>
      </div>
    </template>

    <el-alert
      v-if="showCancelingAlert"
      type="error"
      :closable="false"
      show-icon
      class="pending-alert"
    >
      <template #title>
        {{ t('order.cancelingAlert', { count: cancelingCount }) }}
      </template>
      <el-button type="danger" link @click="viewCancelingOrders">
        {{ t('order.viewCancelingOrders') }} →
      </el-button>
    </el-alert>

    <el-alert
      v-if="showPendingAlert"
      type="warning"
      :closable="false"
      show-icon
      class="pending-alert"
    >
      <template #title>
        {{ t('order.pendingShipmentAlert', { count: pendingShipmentCount }) }}
      </template>
      <el-button type="warning" link @click="viewPendingShipments">
        {{ t('order.viewPendingShipment') }} →
      </el-button>
    </el-alert>

    <el-form :inline="true" class="filter-form">
      <el-form-item :label="t('order.orderNo')">
        <el-input
          v-model="filters.keyword"
          :placeholder="t('order.orderNo')"
          clearable
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item :label="t('common.status')">
        <el-select
          v-model="filters.status"
          :placeholder="t('common.all')"
          clearable
          style="width: 120px"
        >
          <el-option :label="t('order.statusPending')" value="pending" />
          <el-option :label="t('order.statusPaid')" value="paid" />
          <el-option :label="t('order.statusShipped')" value="shipped" />
          <el-option :label="t('order.statusCompleted')" value="completed" />
          <el-option :label="t('order.statusCancelled')" value="cancelled" />
          <el-option :label="t('order.statusCanceling')" value="canceling" />
          <el-option :label="t('order.statusRefunding')" value="refunding" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('order.orderDate')">
        <el-date-picker
          v-model="filters.dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          style="width: 260px"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">{{ t('common.search') }}</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="order_no" :label="t('order.orderNo')" min-width="160" />
      <el-table-column prop="customer_name" :label="t('order.customer')" width="100" />
      <el-table-column prop="total_amount" :label="t('order.amount')" width="100" />
      <el-table-column :label="t('common.status')" width="100">
        <template #default="{ row }">
          <el-tag :type="rowStatusType(row)" size="small">
            {{ rowStatusLabel(row) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="logistics_no" :label="t('order.logisticsNo')" min-width="140" show-overflow-tooltip class-name="col-hide-md">
        <template #default="{ row }">
          {{ row.logistics?.tracking_number || row.logistics_no || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" :label="t('order.orderTime')" width="170" class-name="col-hide-md" />
      <el-table-column
        prop="paid_at"
        :label="t('order.paidAt')"
        width="170"
        class-name="col-hide-md"
      >
        <template #default="{ row }">
          {{ formatDateTime(row.paid_at) }}
        </template>
      </el-table-column>
      <el-table-column
        :label="t('common.actions')"
        :min-width="ACTION_COLUMN.order"
        class-name="col-actions"
        fixed="right"
      >
        <template #default="{ row }">
          <TableActionMenu
            :actions="[
              { label: t('common.detail'), type: 'primary', onClick: () => handleDetail(row) },
              {
                label: t('order.cancelReview'),
                type: 'warning',
                onClick: () => openCancelReview(row),
                visible: isCanceling(row),
              },
              {
                label: t('order.ship'),
                type: 'success',
                onClick: () => handleShip(row),
                visible: canShip(row),
              },
            ]"
          />
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :total="pagination.total"
      layout="total, prev, pager, next"
      class="pagination"
      @current-change="fetchList"
    />
  </el-card>

  <el-dialog v-model="detailVisible" :title="t('order.detailTitle')" width="640px">
    <div v-loading="detailLoading">
    <el-descriptions v-if="currentOrder" :column="1" border>
      <el-descriptions-item :label="t('order.orderNo')">{{ currentOrder.order_no }}</el-descriptions-item>
      <el-descriptions-item :label="t('order.customer')">{{ currentOrder.customer_name }}</el-descriptions-item>
      <el-descriptions-item :label="t('common.status')">
        <el-tag :type="rowStatusType(currentOrder)" size="small">
          {{ rowStatusLabel(currentOrder) }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item v-if="isCanceling(currentOrder)" :label="t('order.cancelReason')">
        {{ currentOrder.cancel_reason || '-' }}
      </el-descriptions-item>
      <el-descriptions-item v-if="isCanceling(currentOrder)" :label="t('order.cancelDetail')">
        {{ currentOrder.cancel_detail || '-' }}
      </el-descriptions-item>
      <el-descriptions-item :label="t('order.amount')">¥ {{ currentOrder.total_amount }}</el-descriptions-item>
      <el-descriptions-item :label="t('order.address')">{{ currentOrder.address }}</el-descriptions-item>
      <el-descriptions-item :label="t('order.logisticsNo')">
        {{ currentOrder.logistics?.tracking_number || currentOrder.logistics_no || '-' }}
      </el-descriptions-item>
      <el-descriptions-item v-if="currentOrder.logistics" :label="t('logistics.expressCompany')">
        {{ currentOrder.logistics.express_company }}
      </el-descriptions-item>
      <el-descriptions-item :label="t('order.orderTime')">{{ formatDateTime(currentOrder.created_at) }}</el-descriptions-item>
      <el-descriptions-item :label="t('order.paidAt')">{{ formatDateTime(currentOrder.paid_at) }}</el-descriptions-item>
      <el-descriptions-item :label="t('common.remark')">{{ currentOrder.remark || '-' }}</el-descriptions-item>
      <el-descriptions-item v-if="currentOrder.status === 'cancelled'" :label="t('order.cancelReason')">
        {{ currentOrder.cancel_reason || '-' }}
      </el-descriptions-item>
      <el-descriptions-item v-if="currentOrder.cancelled_at" :label="t('order.cancelTime')">
        {{ formatDateTime(currentOrder.cancelled_at) }}
      </el-descriptions-item>
    </el-descriptions>

    <div v-if="currentOrder" class="status-flow">
      <div class="status-flow-title">{{ t('order.statusFlowTitle') }}</div>
      <el-steps
        v-if="currentOrder.status !== 'cancelled' && currentOrder.status !== 'refunding'"
        :active="statusFlowIndex(currentOrder.status)"
        finish-status="success"
        align-center
      >
        <el-step
          v-for="step in STATUS_FLOW"
          :key="step"
          :title="STATUS_MAP[step]?.label"
          :description="step === 'pending'
            ? formatDateTime(currentOrder.created_at)
            : step === 'paid'
              ? formatDateTime(currentOrder.paid_at)
              : step === 'shipped' && currentOrder.status !== 'paid'
                ? (currentOrder.logistics_no || '-')
                : ''"
        />
      </el-steps>
      <el-alert
        v-else
        :title="STATUS_MAP[currentOrder.status]?.label"
        type="error"
        :closable="false"
        show-icon
      />
    </div>
    <el-table
      v-if="currentOrder?.items?.length"
      :data="currentOrder.items"
      border
      size="small"
      class="detail-items"
    >
      <el-table-column prop="product_name" :label="t('product.name')" />
      <el-table-column prop="quantity" :label="t('order.quantity')" width="80" />
      <el-table-column prop="unit_price" :label="t('order.unitPrice')" width="100" />
    </el-table>

    <LogisticsTracePanel
      v-if="currentOrder?.logistics && ['shipped', 'completed'].includes(currentOrder.status)"
      :order-id="currentOrder.id"
      :logistics="currentOrder.logistics"
      class="detail-logistics"
    />

    <div v-if="currentOrder?.cancel_logs?.length" class="cancel-logs">
      <div class="status-flow-title">{{ t('order.cancelLogsTitle') }}</div>
      <el-table :data="currentOrder.cancel_logs" border size="small">
        <el-table-column :label="t('order.cancelLogAction')" width="140">
          <template #default="{ row }">
            {{ cancelActionLabels[row.action] || row.action }}
          </template>
        </el-table-column>
        <el-table-column prop="reason" :label="t('order.cancelReason')" min-width="120" />
        <el-table-column prop="remark" :label="t('order.cancelReviewRemark')" min-width="120" />
        <el-table-column :label="t('order.cancelTime')" width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </div>
    </div>

    <template #footer>
      <el-button @click="detailVisible = false">{{ t('common.close') }}</el-button>
      <el-button
        v-if="isCanceling(currentOrder)"
        type="warning"
        @click="openCancelReview(currentOrder)"
      >
        {{ t('order.cancelReview') }}
      </el-button>
      <el-button
        v-if="canForceCancel(currentOrder) && !isCanceling(currentOrder)"
        type="danger"
        plain
        @click="openForceCancel(currentOrder)"
      >
        {{ t('order.forceCancel') }}
      </el-button>
      <el-button
        v-if="canShip(currentOrder)"
        type="success"
        @click="handleShip(currentOrder)"
      >
        {{ t('order.ship') }}
      </el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="reviewVisible" :title="t('order.cancelReviewTitle')" width="520px" destroy-on-close>
    <el-descriptions v-if="reviewForm.orderId" :column="1" border class="review-desc">
      <el-descriptions-item :label="t('order.orderNo')">{{ reviewForm.orderNo }}</el-descriptions-item>
      <el-descriptions-item :label="t('order.customer')">{{ reviewForm.customerName }}</el-descriptions-item>
      <el-descriptions-item :label="t('order.cancelReason')">{{ reviewForm.reason }}</el-descriptions-item>
      <el-descriptions-item :label="t('order.cancelDetail')">{{ reviewForm.detail }}</el-descriptions-item>
    </el-descriptions>
    <el-form label-width="90px" class="review-form">
      <el-form-item :label="t('order.cancelReviewRemark')">
        <el-input v-model="reviewForm.remark" type="textarea" rows="3" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="reviewVisible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="danger" plain :loading="reviewSubmitting" @click="submitCancelReview(false)">
        {{ t('order.rejectCancel') }}
      </el-button>
      <el-button type="warning" :loading="reviewSubmitting" @click="submitCancelReview(true)">
        {{ t('order.approveCancel') }}
      </el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="forceCancelVisible" :title="t('order.forceCancelTitle')" width="460px" destroy-on-close>
    <el-form ref="forceCancelFormRef" :model="forceCancelForm" :rules="forceCancelRules" label-width="90px">
      <el-form-item :label="t('order.cancelReason')" prop="reason">
        <el-input v-model="forceCancelForm.reason" type="textarea" rows="3" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="forceCancelVisible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="danger" :loading="forceCancelSubmitting" @click="submitForceCancel">
        {{ t('order.forceCancel') }}
      </el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="shipVisible" :title="t('order.shipTitle')" width="460px" destroy-on-close>
    <el-form ref="shipFormRef" :model="shipForm" :rules="shipRules" label-width="90px">
      <el-form-item :label="t('logistics.expressCompany')" prop="express_code">
        <el-select v-model="shipForm.express_code" :placeholder="t('logistics.expressRequired')" filterable style="width: 100%">
          <el-option
            v-for="item in expressCompanies"
            :key="item.code"
            :label="item.name"
            :value="item.code"
          />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('order.logisticsNo')" prop="logistics_no">
        <el-input v-model="shipForm.logistics_no" :placeholder="t('order.logisticsRequired')" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="shipVisible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" @click="submitShip">{{ t('order.confirmShip') }}</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cancel-stats {
  font-size: 13px;
  color: #909399;
}
.filter-form {
  margin-bottom: 16px;
}
.pending-alert {
  margin-bottom: 16px;
}
.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
.detail-items {
  margin-top: 16px;
}
.status-flow {
  margin-top: 20px;
}
.status-flow-title {
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
.detail-logistics {
  margin-top: 16px;
}

.cancel-logs {
  margin-top: 16px;
}

.review-desc {
  margin-bottom: 16px;
}

.review-form {
  margin-top: 8px;
}
</style>
