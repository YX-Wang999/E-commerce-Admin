<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getOrderList, shipOrder, updateOrder } from '@/api/order'
import { getExpressCompanies } from '@/api/logistics'
import LogisticsTracePanel from '@/components/orders/LogisticsTracePanel.vue'
import { ACTION_COLUMN } from '@/config/table'

const { t } = useI18n()

const loading = ref(false)
const shipVisible = ref(false)
const trackVisible = ref(false)
const shipFormRef = ref(null)
const tableData = ref([])
const expressCompanies = ref([])
const trackOrder = ref(null)
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ keyword: '', status: 'paid' })

const shipForm = reactive({
  orderId: null,
  orderNo: '',
  orderStatus: '',
  express_code: '',
  logistics_no: '',
})

const shipRules = computed(() => ({
  express_code: [{ required: true, message: t('logistics.expressRequired'), trigger: 'change' }],
  logistics_no: [{ required: true, message: t('order.logisticsRequired'), trigger: 'blur' }],
}))

const STATUS_MAP = computed(() => ({
  paid: { label: t('order.statusPaid'), type: 'warning' },
  shipped: { label: t('order.statusShipped'), type: 'primary' },
  completed: { label: t('order.statusCompleted'), type: 'success' },
}))

async function fetchList() {
  loading.value = true
  try {
    const res = await getOrderList({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
    })
    tableData.value = res.data.results || []
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

async function loadExpressCompanies() {
  try {
    const res = await getExpressCompanies()
    expressCompanies.value = res.data || []
  } catch {
    expressCompanies.value = []
  }
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

function handleShip(row) {
  shipForm.orderId = row.id
  shipForm.orderNo = row.order_no
  shipForm.orderStatus = row.status
  shipForm.express_code = row.logistics?.express_code || ''
  shipForm.logistics_no = row.logistics?.tracking_number || row.logistics_no || ''
  shipVisible.value = true
}

function handleTrack(row) {
  trackOrder.value = row
  trackVisible.value = true
}

async function submitShip() {
  await shipFormRef.value.validate()
  if (shipForm.orderStatus === 'paid') {
    await shipOrder(shipForm.orderId, {
      express_code: shipForm.express_code,
      tracking_number: shipForm.logistics_no,
    })
  } else {
    await updateOrder(shipForm.orderId, { logistics_no: shipForm.logistics_no })
  }
  ElMessage.success(t('order.shipSuccess'))
  shipVisible.value = false
  fetchList()
}

onMounted(async () => {
  await loadExpressCompanies()
  fetchList()
})
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>{{ t('order.logisticsTitle') }}</span>
      </div>
    </template>

    <el-form :inline="true" :model="filters" class="filter-form">
      <el-form-item :label="t('order.orderNo')">
        <el-input v-model="filters.keyword" clearable :placeholder="t('order.orderNo')" />
      </el-form-item>
      <el-form-item :label="t('common.status')">
        <el-select v-model="filters.status" clearable :placeholder="t('common.all')" style="width: 140px">
          <el-option :label="t('order.statusPaid')" value="paid" />
          <el-option :label="t('order.statusShipped')" value="shipped" />
          <el-option :label="t('order.statusCompleted')" value="completed" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">{{ t('common.search') }}</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="tableData" border>
      <el-table-column prop="order_no" :label="t('order.orderNo')" min-width="160" />
      <el-table-column :label="t('common.status')" width="110">
        <template #default="{ row }">
          <el-tag :type="STATUS_MAP[row.status]?.type || 'info'">
            {{ STATUS_MAP[row.status]?.label || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('logistics.expressCompany')" width="120">
        <template #default="{ row }">
          {{ row.logistics?.express_company || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="logistics_no" :label="t('order.logisticsNo')" min-width="160">
        <template #default="{ row }">
          {{ row.logistics?.tracking_number || row.logistics_no || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="address" :label="t('order.address')" min-width="200" show-overflow-tooltip />
      <el-table-column prop="total_amount" :label="t('order.totalAmount')" width="120" />
      <el-table-column prop="created_at" :label="t('order.createdAt')" width="180" class-name="col-hide-md" />
      <el-table-column
        :label="t('common.actions')"
        :min-width="ACTION_COLUMN.order"
        class-name="col-actions"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'paid'"
            link
            type="primary"
            @click="handleShip(row)"
          >
            {{ t('order.ship') }}
          </el-button>
          <el-button
            v-else-if="row.status === 'shipped'"
            link
            type="warning"
            @click="handleShip(row)"
          >
            {{ t('order.updateLogistics') }}
          </el-button>
          <el-button
            v-if="['shipped', 'completed'].includes(row.status)"
            link
            type="primary"
            @click="handleTrack(row)"
          >
            {{ t('logistics.viewTrack') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="fetchList"
      />
    </div>
  </el-card>

  <el-dialog v-model="shipVisible" :title="t('order.shipTitle')" width="480px">
    <el-form ref="shipFormRef" :model="shipForm" :rules="shipRules" label-width="100px">
      <el-form-item :label="t('order.orderNo')">
        <el-input v-model="shipForm.orderNo" disabled />
      </el-form-item>
      <el-form-item v-if="shipForm.orderStatus === 'paid'" :label="t('logistics.expressCompany')" prop="express_code">
        <el-select v-model="shipForm.express_code" :placeholder="t('logistics.expressRequired')" filterable style="width: 100%">
          <el-option v-for="item in expressCompanies" :key="item.code" :label="item.name" :value="item.code" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('order.logisticsNo')" prop="logistics_no">
        <el-input v-model="shipForm.logistics_no" :placeholder="t('order.logisticsPlaceholder')" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="shipVisible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" @click="submitShip">{{ t('common.confirm') }}</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="trackVisible" :title="t('logistics.trackTitle')" width="640px">
    <LogisticsTracePanel
      v-if="trackOrder"
      :order-id="trackOrder.id"
      :logistics="trackOrder.logistics"
    />
  </el-dialog>
</template>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.filter-form {
  margin-bottom: 16px;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>

