<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { approveRefund, getRefundList, rejectRefund } from '@/api/order'
import TableActionMenu from '@/components/TableActionMenu.vue'
import { ACTION_COLUMN } from '@/config/table'
import { useOrderBadgeStore } from '@/stores/orderBadge'

const { t } = useI18n()
const orderBadgeStore = useOrderBadgeStore()

const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ status: '' })

const STATUS_MAP = computed(() => ({
  pending: { label: t('order.statusAuditPending'), type: 'warning' },
  approved: { label: t('order.statusApproved'), type: 'success' },
  rejected: { label: t('order.statusRejected'), type: 'danger' },
}))

const pendingRefundCount = computed(() => orderBadgeStore.pendingRefundCount)

const showPendingAlert = computed(() => pendingRefundCount.value > 0)

function viewPendingRefunds() {
  filters.status = 'pending'
  pagination.page = 1
  fetchList()
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getRefundList({
      page: pagination.page,
      page_size: pagination.pageSize,
      status: filters.status || undefined,
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

async function handleApprove(row) {
  await ElMessageBox.confirm(
    t('order.approveConfirm', { orderNo: row.order_no }),
    t('order.auditConfirm'),
    { type: 'warning' },
  )
  await approveRefund(row.id)
  ElMessage.success(t('order.approveSuccess'))
  await fetchList()
  orderBadgeStore.refresh()
}

async function handleReject(row) {
  await ElMessageBox.confirm(
    t('order.rejectConfirm', { orderNo: row.order_no }),
    t('order.auditConfirm'),
    { type: 'warning' },
  )
  await rejectRefund(row.id)
  ElMessage.success(t('order.rejectSuccess'))
  await fetchList()
  orderBadgeStore.refresh()
}

onMounted(async () => {
  await orderBadgeStore.refresh()
  fetchList()
})
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <span>{{ t('order.refundTitle') }}</span>
    </template>

    <el-alert
      v-if="showPendingAlert"
      type="warning"
      :closable="false"
      show-icon
      class="pending-alert"
    >
      <template #title>
        {{ t('order.pendingRefundAlert', { count: pendingRefundCount }) }}
      </template>
      <el-button type="warning" link @click="viewPendingRefunds">
        {{ t('order.viewPendingRefund') }} →
      </el-button>
    </el-alert>

    <el-form :inline="true" class="filter-form">
      <el-form-item :label="t('common.status')">
        <el-select
          v-model="filters.status"
          :placeholder="t('common.all')"
          clearable
          style="width: 120px"
        >
          <el-option :label="t('order.statusAuditPending')" value="pending" />
          <el-option :label="t('order.statusApproved')" value="approved" />
          <el-option :label="t('order.statusRejected')" value="rejected" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">{{ t('common.search') }}</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="order_no" :label="t('order.orderNo')" min-width="160" />
      <el-table-column
        prop="reason"
        :label="t('order.refundReason')"
        min-width="180"
        show-overflow-tooltip
      />
      <el-table-column prop="amount" :label="t('order.refundAmount')" width="110" />
      <el-table-column :label="t('common.status')" width="100">
        <template #default="{ row }">
          <el-tag :type="STATUS_MAP[row.status]?.type || 'info'" size="small">
            {{ STATUS_MAP[row.status]?.label || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" :label="t('order.applyTime')" width="170" class-name="col-hide-md" />
      <el-table-column
        :label="t('common.actions')"
        :min-width="ACTION_COLUMN.order"
        class-name="col-actions"
        fixed="right"
      >
        <template #default="{ row }">
          <TableActionMenu
            v-if="row.status === 'pending'"
            :actions="[
              { label: t('order.approve'), type: 'success', onClick: () => handleApprove(row) },
              { label: t('order.reject'), type: 'danger', onClick: () => handleReject(row), danger: true },
            ]"
          />
          <span v-else>-</span>
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
</template>

<style scoped>
.pending-alert {
  margin-bottom: 16px;
}
.filter-form {
  margin-bottom: 16px;
}
.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
