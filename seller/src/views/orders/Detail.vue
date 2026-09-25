<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getExpressCompanies, getOrderDetail, shipOrder, cancelReviewOrder, cancelOrder } from '@/api/orders'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()
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
const order = ref(null)
const expressCompanies = ref([])
const expressCompaniesLoading = ref(true)

const shipForm = reactive({
  express_code: '',
  logistics_no: '',
})

const reviewForm = reactive({
  remark: '',
})

const merchantCancelForm = reactive({
  reason: '',
})

const statusMap = computed(() => ({
  pending: t('order.statusPending'),
  paid: t('order.statusPaid'),
  shipped: t('order.statusShipped'),
  completed: t('order.statusCompleted'),
  cancelled: t('order.statusCancelled'),
  refunding: t('order.statusRefunding'),
}))

const shipRules = computed(() => ({
  express_code: [{ required: true, message: t('seller.expressRequired'), trigger: 'change' }],
  logistics_no: [{ required: true, message: t('seller.trackingNumber'), trigger: 'blur' }],
}))

const orderId = computed(() => route.params.id)
const canShip = computed(() => order.value?.status === 'paid' && order.value?.cancel_status !== 'pending')
const isCanceling = computed(() => order.value?.status === 'paid' && order.value?.cancel_status === 'pending')
const canMerchantCancel = computed(() => order.value?.status === 'paid' && order.value?.cancel_status !== 'pending')

const merchantCancelRules = computed(() => ({
  reason: [{ required: true, message: t('seller.merchantCancelReason'), trigger: 'blur' }],
}))

async function fetchDetail() {
  loading.value = true
  try {
    const res = await getOrderDetail(orderId.value)
    order.value = res.data
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

function openShip() {
  const defaultCode = authStore.tenant?.config?.default_express_code
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
    const res = await shipOrder(orderId.value, {
      express_code: shipForm.express_code,
      tracking_number: shipForm.logistics_no,
    })
    order.value = res.data
    ElMessage.success(t('seller.shipSuccess'))
    shipVisible.value = false
  } finally {
    shipSubmitting.value = false
  }
}

async function submitCancelReview(approve) {
  reviewSubmitting.value = true
  try {
    const res = await cancelReviewOrder(orderId.value, {
      approve,
      remark: reviewForm.remark,
    })
    order.value = res.data
    ElMessage.success(t('seller.cancelReviewSuccess'))
    reviewVisible.value = false
  } finally {
    reviewSubmitting.value = false
  }
}

async function submitMerchantCancel() {
  await merchantCancelFormRef.value?.validate()
  merchantCancelSubmitting.value = true
  try {
    const res = await cancelOrder(orderId.value, { reason: merchantCancelForm.reason })
    order.value = res.data
    ElMessage.success(t('seller.merchantCancelSuccess'))
    merchantCancelVisible.value = false
  } finally {
    merchantCancelSubmitting.value = false
  }
}

function itemSubtotal(item) {
  return (Number(item.unit_price) * Number(item.quantity)).toFixed(2)
}

onMounted(async () => {
  await Promise.all([fetchDetail(), loadExpressCompanies()])
})
</script>

<template>
  <div v-loading="loading" class="page-card">
    <div class="page-header">
      <h2>{{ t('seller.orderDetail') }}</h2>
      <div class="header-actions">
        <el-button v-if="isCanceling" type="warning" @click="reviewVisible = true">{{ t('seller.cancelReview') }}</el-button>
        <el-button v-if="canShip" type="success" :disabled="expressCompaniesLoading" @click="openShip">{{ t('seller.shipOrder') }}</el-button>
        <el-button v-if="canMerchantCancel" type="danger" plain @click="merchantCancelVisible = true">
          {{ t('seller.merchantCancel') }}
        </el-button>
        <el-button @click="router.back()">{{ t('seller.back') }}</el-button>
      </div>
    </div>

    <el-empty v-if="!order && !loading" :description="t('seller.orderNotFound')" />

    <template v-else-if="order">
      <el-descriptions :column="2" border>
        <el-descriptions-item :label="t('order.orderNo')">{{ order.order_no }}</el-descriptions-item>
        <el-descriptions-item :label="t('seller.status')">{{ statusMap[order.status] || order.status }}</el-descriptions-item>
        <el-descriptions-item :label="t('seller.customer')">
          {{ order.customer_name || order.customer?.nickname || order.customer?.phone || '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('seller.amount')">¥{{ order.total_amount }}</el-descriptions-item>
        <el-descriptions-item :label="t('seller.orderTime')">
          {{ order.created_at ? String(order.created_at).replace('T', ' ').slice(0, 19) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('seller.shippingAddress')">{{ order.address || '-' }}</el-descriptions-item>
        <el-descriptions-item v-if="order.cancel_reason" :label="t('seller.cancelReason')">
          {{ order.cancel_reason }}
        </el-descriptions-item>
        <el-descriptions-item v-if="order.cancel_detail" :label="t('seller.cancelDetail')">
          {{ order.cancel_detail }}
        </el-descriptions-item>
        <el-descriptions-item v-if="order.logistics_no" :label="t('seller.trackingNumber')">
          {{ order.logistics_no }}
        </el-descriptions-item>
      </el-descriptions>

      <h3 class="section-title">{{ t('seller.items') }}</h3>
      <el-table :data="order.items || []" stripe>
        <el-table-column prop="product_name" :label="t('seller.productLabel')" min-width="180" />
        <el-table-column prop="quantity" :label="t('seller.quantity')" width="80" />
        <el-table-column prop="unit_price" :label="t('seller.unitPrice')" width="100" />
        <el-table-column :label="t('seller.subtotal')" width="100">
          <template #default="{ row }">{{ itemSubtotal(row) }}</template>
        </el-table-column>
      </el-table>
    </template>

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
      <el-descriptions :column="1" border>
        <el-descriptions-item :label="t('order.orderNo')">{{ order?.order_no }}</el-descriptions-item>
        <el-descriptions-item :label="t('seller.cancelReason')">{{ order?.cancel_reason || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="t('seller.cancelDetail')">{{ order?.cancel_detail || '-' }}</el-descriptions-item>
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
.header-actions {
  display: flex;
  gap: 8px;
}

.section-title {
  margin: 24px 0 12px;
  font-size: 16px;
}

.review-form {
  margin-top: 16px;
}
</style>
