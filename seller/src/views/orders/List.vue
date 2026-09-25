<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getExpressCompanies, getOrderList, shipOrder, cancelReviewOrder, cancelOrder } from '@/api/orders'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const loading = ref(false)
const shipVisible = ref(false)
const reviewVisible = ref(false)
const merchantCancelVisible = ref(false)
const shipSubmitting = ref(false)
const reviewSubmitting = ref(false)
const merchantCancelSubmitting = ref(false)
const shipFormRef = ref(null)
const merchantCancelFormRef = ref(null)
const tableData = ref([])
const expressCompanies = ref([])
const expressCompaniesLoading = ref(true)
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ keyword: '', status: '' })

const shipForm = reactive({
  orderId: null,
  express_code: '',
  logistics_no: '',
})

const reviewForm = reactive({
  orderId: null,
  orderNo: '',
  customerName: '',
  reason: '',
  detail: '',
  remark: '',
})

const merchantCancelForm = reactive({
  orderId: null,
  reason: '',
})

const statusMap = computed(() => ({
  pending: { label: t('order.statusPending'), type: 'info' },
  paid: { label: t('order.statusPaid'), type: 'primary' },
  shipped: { label: t('order.statusShipped'), type: 'warning' },
  completed: { label: t('order.statusCompleted'), type: 'success' },
  cancelled: { label: t('order.statusCancelled'), type: 'danger' },
  refunding: { label: t('order.statusRefunding'), type: 'danger' },
  canceling: { label: t('seller.statusCanceling'), type: 'warning' },
}))

const merchantCancelRules = computed(() => ({
  reason: [{ required: true, message: t('seller.merchantCancelReason'), trigger: 'blur' }],
}))

function rowStatusKey(row) {
  if (row.status === 'paid' && row.cancel_status === 'pending') return 'canceling'
  return row.status
}

function rowStatusLabel(row) {
  return statusMap.value[rowStatusKey(row)]?.label || row.status
}

function rowStatusType(row) {
  return statusMap.value[rowStatusKey(row)]?.type || 'info'
}

function isCanceling(row) {
  return row.status === 'paid' && row.cancel_status === 'pending'
}

function canShip(row) {
  return row.status === 'paid' && row.cancel_status !== 'pending'
}

function canMerchantCancel(row) {
  return row.status === 'paid' && row.cancel_status !== 'pending'
}

const shipRules = computed(() => ({
  express_code: [{ required: true, message: t('seller.expressRequired'), trigger: 'change' }],
  logistics_no: [{ required: true, message: t('seller.trackingNumber'), trigger: 'blur' }],
}))

const paidCount = computed(() => tableData.value.filter((row) => row.status === 'paid').length)

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
  expressCompaniesLoading.value = true
  try {
    const res = await getExpressCompanies()
    expressCompanies.value = res.data || []
  } catch {
    expressCompanies.value = []
  } finally {
    expressCompaniesLoading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

function handlePageChange(page) {
  pagination.page = page
  fetchList()
}

function openDetail(row) {
  router.push({ name: 'OrderDetail', params: { id: row.id } })
}

function openShip(row) {
  const defaultCode = authStore.tenant?.config?.default_express_code
  shipForm.orderId = row.id
  shipForm.express_code = expressCompanies.value.some((company) => company.code === defaultCode)
    ? defaultCode
    : ''
  shipForm.logistics_no = ''
  shipVisible.value = true
}

async function submitShip() {
  await shipFormRef.value?.validate()
  shipSubmitting.value = true
  try {
    await shipOrder(shipForm.orderId, {
      express_code: shipForm.express_code,
      tracking_number: shipForm.logistics_no,
    })
    ElMessage.success(t('seller.shipSuccess'))
    shipVisible.value = false
    await fetchList()
  } finally {
    shipSubmitting.value = false
  }
}

function openCancelReview(row) {
  reviewForm.orderId = row.id
  reviewForm.orderNo = row.order_no
  reviewForm.customerName = row.customer_name || row.customer?.nickname || row.customer?.phone || '-'
  reviewForm.reason = row.cancel_reason || '-'
  reviewForm.detail = row.cancel_detail || '-'
  reviewForm.remark = ''
  reviewVisible.value = true
}

async function submitCancelReview(approve) {
  reviewSubmitting.value = true
  try {
    await cancelReviewOrder(reviewForm.orderId, {
      approve,
      remark: reviewForm.remark,
    })
    ElMessage.success(t('seller.cancelReviewSuccess'))
    reviewVisible.value = false
    await fetchList()
  } finally {
    reviewSubmitting.value = false
  }
}

function openMerchantCancel(row) {
  merchantCancelForm.orderId = row.id
  merchantCancelForm.reason = ''
  merchantCancelVisible.value = true
}

async function submitMerchantCancel() {
  await merchantCancelFormRef.value?.validate()
  merchantCancelSubmitting.value = true
  try {
    await cancelOrder(merchantCancelForm.orderId, { reason: merchantCancelForm.reason })
    ElMessage.success(t('seller.merchantCancelSuccess'))
    merchantCancelVisible.value = false
    await fetchList()
  } finally {
    merchantCancelSubmitting.value = false
  }
}

function viewPendingShipments() {
  filters.status = 'paid'
  pagination.page = 1
  fetchList()
}

onMounted(async () => {
  if (route.query.status) {
    filters.status = String(route.query.status)
  }
  await loadExpressCompanies()
  fetchList()
})
</script>

<template>
  <div class="page-card">
    <div class="page-header">
      <h2>{{ t('seller.orders') }}</h2>
    </div>

    <el-alert
      v-if="filters.status === 'paid' && pagination.total > 0"
      type="warning"
      show-icon
      :closable="false"
      class="pending-alert"
    >
      <template #title>
        {{ t('seller.pendingShipAlert', { count: pagination.total }) }}
      </template>
    </el-alert>

    <el-form inline @submit.prevent="handleSearch">
      <el-form-item :label="t('seller.keyword')">
        <el-input
          v-model="filters.keyword"
          :placeholder="t('seller.orderKeywordPlaceholder')"
          clearable
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item :label="t('seller.status')">
        <el-select v-model="filters.status" clearable :placeholder="t('seller.all')" style="width: 140px">
          <el-option v-for="(item, key) in statusMap" :key="key" :label="item.label" :value="key" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">{{ t('seller.query') }}</el-button>
        <el-button v-if="paidCount" type="warning" plain @click="viewPendingShipments">
          {{ t('seller.viewPendingShip') }}
        </el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="tableData" stripe>
      <el-table-column prop="order_no" :label="t('order.orderNo')" min-width="160" />
      <el-table-column :label="t('seller.customer')" min-width="120">
        <template #default="{ row }">
          {{ row.customer_name || row.customer?.nickname || row.customer?.phone || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="total_amount" :label="t('seller.amount')" width="100" />
      <el-table-column :label="t('seller.status')" width="100">
        <template #default="{ row }">
          <el-tag :type="rowStatusType(row)" size="small">
            {{ rowStatusLabel(row) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" :label="t('seller.orderTime')" width="170">
        <template #default="{ row }">
          {{ row.created_at ? String(row.created_at).replace('T', ' ').slice(0, 19) : '-' }}
        </template>
      </el-table-column>
      <el-table-column :label="t('seller.actions')" width="220" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="openDetail(row)">{{ t('seller.detail') }}</el-button>
          <el-button v-if="isCanceling(row)" type="warning" link @click="openCancelReview(row)">
            {{ t('seller.cancelReview') }}
          </el-button>
          <el-button v-if="canShip(row)" type="success" link :disabled="expressCompaniesLoading" @click="openShip(row)">
            {{ t('seller.shipOrder') }}
          </el-button>
          <el-button v-if="canMerchantCancel(row)" type="danger" link @click="openMerchantCancel(row)">
            {{ t('seller.merchantCancel') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        :page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>

    <el-dialog v-model="shipVisible" :title="t('seller.shipTitle')" width="480px">
      <el-form ref="shipFormRef" :model="shipForm" :rules="shipRules" label-width="100px">
        <el-form-item :label="t('seller.expressCompany')" prop="express_code">
          <el-select v-model="shipForm.express_code" filterable style="width: 100%">
            <el-option
              v-for="item in expressCompanies"
              :key="item.code"
              :label="item.name"
              :value="item.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('seller.trackingNumber')" prop="logistics_no">
          <el-input v-model="shipForm.logistics_no" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shipVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="shipSubmitting" @click="submitShip">{{ t('seller.shipOrder') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="reviewVisible" :title="t('seller.cancelReviewTitle')" width="520px">
      <el-descriptions :column="1" border class="review-desc">
        <el-descriptions-item :label="t('order.orderNo')">{{ reviewForm.orderNo }}</el-descriptions-item>
        <el-descriptions-item :label="t('seller.customer')">{{ reviewForm.customerName }}</el-descriptions-item>
        <el-descriptions-item :label="t('seller.cancelReason')">{{ reviewForm.reason }}</el-descriptions-item>
        <el-descriptions-item :label="t('seller.cancelDetail')">{{ reviewForm.detail }}</el-descriptions-item>
      </el-descriptions>
      <el-form label-width="90px" class="review-form">
        <el-form-item :label="t('seller.cancelReviewRemark')">
          <el-input v-model="reviewForm.remark" type="textarea" rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="danger" plain :loading="reviewSubmitting" @click="submitCancelReview(false)">
          {{ t('seller.rejectCancel') }}
        </el-button>
        <el-button type="primary" :loading="reviewSubmitting" @click="submitCancelReview(true)">
          {{ t('seller.approveCancel') }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="merchantCancelVisible" :title="t('seller.merchantCancelTitle')" width="460px">
      <el-form ref="merchantCancelFormRef" :model="merchantCancelForm" :rules="merchantCancelRules" label-width="90px">
        <el-form-item :label="t('seller.merchantCancelReason')" prop="reason">
          <el-input v-model="merchantCancelForm.reason" type="textarea" rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="merchantCancelVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="danger" :loading="merchantCancelSubmitting" @click="submitMerchantCancel">
          {{ t('seller.merchantCancel') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.pending-alert {
  margin-bottom: 16px;
}

.review-desc {
  margin-bottom: 16px;
}

.review-form {
  margin-top: 8px;
}

.pager {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
