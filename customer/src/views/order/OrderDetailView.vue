<script setup>
import { computed, defineAsyncComponent, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showConfirmDialog, showToast } from 'vant'
import OrderCountdownTag from '@/components/order/OrderCountdownTag.vue'
import OrderCancelDialog from '@/components/order/OrderCancelDialog.vue'
import { getOrder, mockPayOrder, cancelOrder, applyCancelOrder, confirmReceipt } from '@/api/order'
import { EARLY_RECEIPT_CODE } from '@/constants/api'
import { useOrderSummaryStore } from '@/stores/orderSummary'
import { getLogisticsTrack } from '@/api/logistics'
import { isLoggedIn } from '@/utils/auth'
import { useOrderCountdown } from '@/composables/useOrderCountdown'
import { formatPrice } from '@/utils/product'
import { resolveErrorMessage, toastSuccess } from '@/utils/feedback'
import { requireLogin } from '@/stores/loginGate'
import { canDirectCancelOrder } from '@/utils/order'

const LogisticsTraceMap = defineAsyncComponent({
  loader: () => import('@/components/order/LogisticsTraceMap.vue'),
  delay: 0,
})

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const orderSummaryStore = useOrderSummaryStore()

const loading = ref(true)
const loadError = ref('')
const paying = ref(false)
const cancelling = ref(false)
const confirmingReceipt = ref(false)
const cancelVisible = ref(false)
const cancelMode = ref('cancel')
const trackLoading = ref(false)
const order = ref(null)
const logistics = ref(null)
const expiresAt = computed(() => order.value?.expires_at || '')
const { isExpired } = useOrderCountdown(expiresAt)
const canPay = computed(() => order.value?.status === 'pending' && !isExpired.value)
const canDirectCancel = computed(() => canDirectCancelOrder(order.value))
const canApplyCancel = computed(() =>
  order.value?.status === 'paid' && order.value?.cancel_status !== 'pending',
)
const isCanceling = computed(() =>
  order.value?.status === 'paid' && order.value?.cancel_status === 'pending',
)
const isCancelled = computed(() => order.value?.status === 'cancelled')
const showLogistics = computed(() => ['shipped', 'completed'].includes(order.value?.status))
const canComplain = computed(() =>
  ['paid', 'shipped', 'completed', 'refunding'].includes(order.value?.status)
  && (order.value?.tenant || order.value?.tenant_id),
)
const canConfirmReceipt = computed(() => order.value?.status === 'shipped')
const canReview = computed(() => order.value?.status === 'completed')

async function doConfirmReceipt(earlyAcknowledged = false) {
  const res = await confirmReceipt(order.value.id, { early_acknowledged: earlyAcknowledged })
  order.value = res.data
  toastSuccess(res.message || t('order.confirmReceiptSuccess'))
  await orderSummaryStore.refresh()
}

async function submitConfirmReceipt(earlyAcknowledged = false) {
  if (!order.value?.id || confirmingReceipt.value) return
  confirmingReceipt.value = true
  try {
    try {
      await doConfirmReceipt(earlyAcknowledged)
    } catch (error) {
      const payload = error?.response?.data || error
      if (payload?.code === EARLY_RECEIPT_CODE && !earlyAcknowledged) {
        try {
          await showConfirmDialog({
            title: t('order.earlyReceiptTitle'),
            message: payload.message || t('order.earlyReceiptHint'),
            confirmButtonText: t('order.earlyReceiptConfirm'),
            cancelButtonText: t('common.cancel'),
          })
          await doConfirmReceipt(true)
        } catch {
          // user cancelled dialog
        }
        return
      }
      showToast(resolveErrorMessage(error, 'order.confirmReceiptFailed'))
    }
  } finally {
    confirmingReceipt.value = false
  }
}

function handleConfirmReceipt() {
  submitConfirmReceipt(false)
}

function goReview() {
  const item = order.value?.items?.[0]
  if (!item) return
  router.push({
    name: 'ReviewCenter',
    query: {
      tab: 'pending',
      publish: '1',
      order_id: order.value.id,
      product_id: item.product,
      product_name: item.product_name,
      order_no: order.value.order_no,
    },
  })
}

function goComplaint() {
  router.push({ name: 'ComplaintCreate', query: { order_id: order.value.id } })
}

function orderShopName(item) {
  if (!item) return t('order.platformShop')
  if (item.tenant_name) return item.tenant_name
  if (item.tenant?.name) return item.tenant.name
  return t('order.platformShop')
}

const statusMap = {
  pending: 'checkout.statusPending',
  paid: 'checkout.statusPaid',
  shipped: 'checkout.statusShipped',
  completed: 'checkout.statusCompleted',
  cancelled: 'checkout.statusCancelled',
}

function displayStatus(orderData) {
  if (orderData?.status === 'paid' && orderData?.cancel_status === 'pending') {
    return t('order.statusCanceling')
  }
  return t(statusMap[orderData?.status] || 'checkout.statusPending')
}

const logisticsSteps = computed(() => {
  const traces = logistics.value?.traces || []
  return traces.map((item, index) => ({
    text: item.content,
    desc: item.time,
    active: index === 0,
  }))
})

const logisticsActive = computed(() => {
  const status = logistics.value?.status
  const map = {
    pending: 0,
    picked: 1,
    transporting: 2,
    delivering: 3,
    delivered: 4,
    exception: 2,
    returned: 2,
  }
  return map[status] ?? 1
})

async function fetchLogistics() {
  if (!order.value?.id || !showLogistics.value) return
  trackLoading.value = true
  try {
    // Client only reads DB; stage advance happens on admin refresh.
    const res = await getLogisticsTrack(order.value.id, false)
    logistics.value = res.data
    if (import.meta.env.DEV) {
      console.log('[OrderDetail] 物流数据:', logistics.value)
      console.log('[OrderDetail] 轨迹数据:', logistics.value?.traces)
    }
  } catch {
    logistics.value = order.value?.logistics || null
  } finally {
    trackLoading.value = false
  }
}

async function fetchOrder() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await getOrder(route.params.id)
    order.value = res.data
    logistics.value = res.data?.logistics || null
    if (import.meta.env.DEV) {
      console.log('[OrderDetail] 订单物流:', res.data?.logistics)
      console.log('[OrderDetail] 订单轨迹:', res.data?.logistics?.traces)
    }
    if (['shipped', 'completed'].includes(res.data?.status)) {
      await fetchLogistics(false)
    }
  } catch (error) {
    order.value = null
    loadError.value = resolveErrorMessage(error, 'order.loadFailed')
    if (!isLoggedIn()) {
      try {
        await requireLogin({ redirect: route.fullPath })
        await fetchOrder()
      } catch {
        // cancelled login
      }
    }
  } finally {
    loading.value = false
  }
}

async function handleMockPay() {
  if (!order.value?.id || paying.value || !canPay.value) return
  paying.value = true
  try {
    const res = await mockPayOrder(order.value.id)
    order.value = {
      ...order.value,
      status: res.data.status,
      paid_at: res.data.paid_at,
    }
    toastSuccess(res.message || t('checkout.paySuccess'))
    await fetchOrder()
  } catch (error) {
    showToast(resolveErrorMessage(error, 'checkout.payFailed'))
  } finally {
    paying.value = false
  }
}

function openCancelDialog(mode) {
  cancelMode.value = mode
  cancelVisible.value = true
}

async function handleCancelConfirm(payload) {
  if (!order.value?.id || cancelling.value) return
  cancelling.value = true
  try {
    const api = cancelMode.value === 'apply' ? applyCancelOrder : cancelOrder
    const res = await api(order.value.id, payload)
    order.value = res.data
    toastSuccess(res.message || t(cancelMode.value === 'apply' ? 'order.applyCancelSuccess' : 'order.cancelSuccess'))
    cancelVisible.value = false
  } catch (error) {
    showToast(resolveErrorMessage(error, 'order.cancelFailed'))
  } finally {
    cancelling.value = false
  }
}

onMounted(fetchOrder)

watch(isExpired, (expired) => {
  if (expired && order.value?.status === 'pending') {
    fetchOrder()
  }
})
</script>

<template>
  <div class="order-detail-page">
    <van-nav-bar
      :title="t('checkout.orderDetailTitle')"
      left-arrow
      fixed
      placeholder
      @click-left="router.back()"
    />

    <van-loading v-if="loading" class="page-loading" vertical>
      {{ t('common.loading') }}
    </van-loading>

    <van-empty
      v-else-if="loadError"
      class="page-empty"
      :description="loadError"
    >
      <van-button round type="primary" size="small" @click="fetchOrder">
        {{ t('common.retry') }}
      </van-button>
    </van-empty>

    <template v-else-if="order">
      <section class="card status-card">
        <div class="status-text">{{ displayStatus(order) }}</div>
        <div class="order-no">{{ t('checkout.orderNo', { no: order.order_no }) }}</div>
        <div class="shop-line">
          <span class="shop-label">{{ t('order.shop') }}</span>
          <span class="shop-name">{{ orderShopName(order) }}</span>
        </div>
        <OrderCountdownTag :expires-at="order.expires_at" :status="order.status" class="detail-countdown" />
        <div v-if="order.paid_at" class="paid-at">
          {{ t('checkout.paidAt') }}：{{ order.paid_at.replace('T', ' ').slice(0, 19) }}
        </div>
        <van-notice-bar
          v-if="isCanceling"
          color="#ed6a0c"
          background="#fff7e8"
          :text="t('order.cancelingHint')"
          class="cancel-notice"
        />
        <van-notice-bar
          v-else-if="order.cancel_status === 'rejected'"
          color="#ee0a24"
          background="#ffe1e1"
          :text="`${t('order.cancelRejectedHint')}${order.cancel_review_remark ? `：${order.cancel_review_remark}` : ''}`"
          class="cancel-notice"
        />
      </section>

      <section v-if="isCancelled" class="card">
        <div class="section-title">{{ t('order.cancelInfoTitle') }}</div>
        <div class="cancel-info-row">
          <span>{{ t('order.cancelReason') }}</span>
          <span>{{ order.cancel_reason || '-' }}</span>
        </div>
        <div v-if="order.cancel_detail" class="cancel-info-row">
          <span>{{ t('order.cancelDetailLabel') }}</span>
          <span>{{ order.cancel_detail }}</span>
        </div>
        <div class="cancel-info-row">
          <span>{{ t('order.cancelTime') }}</span>
          <span>{{ order.cancelled_at ? order.cancelled_at.replace('T', ' ').slice(0, 19) : '-' }}</span>
        </div>
      </section>

      <section v-if="showLogistics" class="card logistics-card">
        <div class="section-head">
          <div class="section-title">{{ t('checkout.logisticsTitle') }}</div>
          <van-button size="mini" plain type="primary" :loading="trackLoading" @click="fetchLogistics">
            {{ t('checkout.logisticsRefresh') }}
          </van-button>
        </div>
        <div v-if="logistics" class="logistics-summary">
          <div>{{ logistics.express_company }} · {{ logistics.tracking_number }}</div>
          <div class="logistics-status">{{ logistics.status_label || logistics.status }}</div>
        </div>
        <div v-if="logisticsSteps.length" class="logistics-body">
          <div class="trace-timeline">
            <van-steps direction="vertical" :active="logisticsActive">
              <van-step v-for="(step, index) in logisticsSteps" :key="`${step.desc}-${index}`">
                <h4>{{ step.text }}</h4>
                <p>{{ step.desc }}</p>
              </van-step>
            </van-steps>
          </div>
          <LogisticsTraceMap
            :traces="logistics?.traces || []"
            :address="order.address"
          />
        </div>
        <van-empty v-else :description="t('checkout.logisticsTraceEmpty')" />
      </section>

      <section class="card">
        <div class="section-title">{{ t('checkout.addressInfo') }}</div>
        <div class="address-text">{{ order.address }}</div>
      </section>

      <section class="card">
        <div class="section-title">{{ t('checkout.goodsList') }}</div>
        <div v-for="item in order.items" :key="item.id" class="goods-item">
          <div class="goods-name">{{ item.product_name }}</div>
          <div class="goods-meta">
            <span>{{ formatPrice(item.unit_price) }}</span>
            <span>x{{ item.quantity }}</span>
            <span class="subtotal">{{ formatPrice(Number(item.unit_price) * item.quantity) }}</span>
          </div>
        </div>
      </section>

      <section class="card">
        <div class="summary-row">
          <span>{{ t('checkout.payAmount') }}</span>
          <span class="pay-amount">{{ formatPrice(order.total_amount) }}</span>
        </div>
        <div v-if="order.remark" class="remark">{{ t('checkout.remark') }}：{{ order.remark }}</div>
      </section>
    </template>

    <div v-if="canPay" class="pay-bar">
      <van-button type="primary" block round :loading="paying" @click="handleMockPay">
        {{ t('checkout.mockPay') }}
      </van-button>
    </div>
    <div v-else-if="canDirectCancel" class="pay-bar action-bar">
      <van-button type="default" block round plain @click="openCancelDialog('cancel')">
        {{ t('order.cancelOrder') }}
      </van-button>
    </div>
    <div v-else-if="canApplyCancel" class="pay-bar action-bar">
      <van-button type="default" block round plain @click="openCancelDialog('apply')">
        {{ t('order.applyCancel') }}
      </van-button>
      <van-button type="warning" block round plain @click="goComplaint">
        {{ t('complaint.complainOrder') }}
      </van-button>
    </div>
    <div v-else-if="canConfirmReceipt" class="pay-bar action-bar">
      <van-button type="primary" block round :loading="confirmingReceipt" @click="handleConfirmReceipt">
        {{ t('order.confirmReceipt') }}
      </van-button>
      <van-button v-if="canComplain" type="warning" block round plain @click="goComplaint">
        {{ t('complaint.complainOrder') }}
      </van-button>
    </div>
    <div v-else-if="canComplain && !isCanceling && order?.status !== 'shipped'" class="pay-bar">
      <van-button type="warning" block round plain @click="goComplaint">
        {{ t('complaint.complainOrder') }}
      </van-button>
    </div>
    <div v-else-if="canReview" class="pay-bar">
      <van-button type="primary" block round plain @click="goReview">
        {{ t('order.goReview') }}
      </van-button>
    </div>

    <OrderCancelDialog
      v-model:show="cancelVisible"
      :order="order"
      :mode="cancelMode"
      :loading="cancelling"
      @confirm="handleCancelConfirm"
    />
  </div>
</template>

<style scoped>
.order-detail-page {
  min-height: 100vh;
  background: #f5f6fa;
  padding-bottom: 88px;
}

.page-loading {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.page-empty {
  padding: 80px 16px;
}

.card {
  margin: 12px;
  padding: 14px;
  background: #fff;
  border-radius: 8px;
}

.status-card {
  background: linear-gradient(135deg, #ee0a24, #ff6034);
  color: #fff;
}

.status-text {
  font-size: 20px;
  font-weight: 700;
}

.order-no {
  font-size: 13px;
  opacity: 0.9;
}

.shop-line {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 13px;
  opacity: 0.92;
}

.shop-label {
  opacity: 0.85;
}

.shop-name {
  font-weight: 600;
}

.detail-countdown :deep(.countdown-tag) {
  margin-top: 10px;
  color: #fff;
  background: rgba(255, 255, 255, 0.2);
}

.paid-at {
  margin-top: 6px;
  font-size: 12px;
  opacity: 0.85;
}

.section-title {
  margin-bottom: 10px;
  font-size: 15px;
  font-weight: 600;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.section-head .section-title {
  margin-bottom: 0;
}

.logistics-summary {
  margin-bottom: 12px;
  font-size: 14px;
  color: #323233;
}

.logistics-status {
  margin-top: 4px;
  color: #1989fa;
  font-size: 13px;
}

.logistics-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.trace-timeline {
  flex: 1;
  min-width: 0;
}

@media (min-width: 768px) {
  .logistics-body {
    flex-direction: row;
    align-items: flex-start;
  }

  .logistics-body .trace-map {
    flex: 1;
    max-width: 50%;
  }
}

.logistics-card :deep(.van-step__title) {
  font-size: 14px;
  font-weight: 500;
}

.logistics-card :deep(.van-step__message) {
  font-size: 12px;
  color: #969799;
}

.address-text,
.remark {
  font-size: 14px;
  line-height: 1.5;
  color: #646566;
}

.goods-item {
  padding: 10px 0;
  border-bottom: 1px solid #f5f5f5;
}

.goods-item:last-child {
  border-bottom: none;
}

.goods-name {
  font-size: 14px;
  color: #323233;
}

.goods-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 6px;
  font-size: 13px;
  color: #969799;
}

.subtotal {
  margin-left: auto;
  color: #323233;
  font-weight: 600;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  font-size: 15px;
  font-weight: 600;
}

.pay-amount {
  color: #ee0a24;
  font-size: 18px;
}

.remark {
  margin-top: 12px;
}

.pay-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
  background: #fff;
  border-top: 1px solid #eee;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.06);
}

.action-bar {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cancel-notice {
  margin-top: 10px;
  border-radius: 6px;
}

.cancel-info-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  font-size: 14px;
  color: #646566;
  border-bottom: 1px solid #f5f5f5;
}

.cancel-info-row:last-child {
  border-bottom: none;
}

.cancel-info-row span:last-child {
  color: #323233;
  text-align: right;
  flex: 1;
}
</style>
