<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showToast } from 'vant'
import OrderCountdownTag from '@/components/order/OrderCountdownTag.vue'
import OrderCancelDialog from '@/components/order/OrderCancelDialog.vue'
import { cancelOrder, getOrders } from '@/api/order'
import { formatPrice } from '@/utils/product'
import { resolveErrorMessage, toastSuccess } from '@/utils/feedback'
import { canDirectCancelOrder } from '@/utils/order'
import { requireLogin } from '@/stores/loginGate'
import { isLoggedIn } from '@/utils/auth'
import { useOrderSummaryStore } from '@/stores/orderSummary'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const orderSummaryStore = useOrderSummaryStore()

const loading = ref(true)
const loadError = ref('')
const orders = ref([])
const cancelVisible = ref(false)
const cancelling = ref(false)
const cancelTarget = ref(null)

const statusFilter = computed(() => route.query.status?.toString() || '')

const displayOrders = computed(() => orders.value)

const statusMap = {
  pending: 'checkout.statusPending',
  paid: 'checkout.statusPaid',
  shipped: 'checkout.statusShipped',
  completed: 'checkout.statusCompleted',
  cancelled: 'checkout.statusCancelled',
  pending_review: 'profile.orderPendingReview',
}

async function fetchOrders() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await getOrders({
      page: 1,
      page_size: 50,
      status: statusFilter.value || undefined,
    })
    orders.value = res.data?.results || res.data || []
  } catch (error) {
    orders.value = []
    loadError.value = resolveErrorMessage(error, 'order.loadFailed')
    if (!isLoggedIn()) {
      try {
        await requireLogin({ redirect: '/orders' })
        await fetchOrders()
      } catch {
        // cancelled
      }
    }
  } finally {
    loading.value = false
  }
}

function goDetail(order) {
  router.push(`/order/${order.id}`)
}

function openCancelDialog(order, event) {
  event?.stopPropagation()
  cancelTarget.value = order
  cancelVisible.value = true
}

async function handleCancelConfirm(payload) {
  if (!cancelTarget.value?.id || cancelling.value) return
  cancelling.value = true
  try {
    const res = await cancelOrder(cancelTarget.value.id, payload)
    toastSuccess(res.message || t('order.cancelSuccess'))
    cancelVisible.value = false
    cancelTarget.value = null
    await fetchOrders()
    if (isLoggedIn()) {
      await orderSummaryStore.refresh()
    }
  } catch (error) {
    showToast(resolveErrorMessage(error, 'order.cancelFailed'))
  } finally {
    cancelling.value = false
  }
}

function goComplaint(order, event) {
  event?.stopPropagation()
  router.push({ name: 'ComplaintCreate', query: { order_id: order.id } })
}

function canComplainOrder(order) {
  return ['paid', 'shipped', 'completed', 'refunding'].includes(order.status)
    && (order.tenant || order.tenant_id)
}

function orderStatusLabel(order) {
  if (order.status === 'paid' && order.cancel_status === 'pending') {
    return t('order.statusCanceling')
  }
  return t(statusMap[order.status] || 'checkout.statusPending')
}

function orderShopName(item) {
  if (!item) return t('order.platformShop')
  if (item.tenant_name) return item.tenant_name
  if (item.tenant?.name) return item.tenant.name
  return t('order.platformShop')
}

onMounted(async () => {
  await fetchOrders()
  if (isLoggedIn()) {
    orderSummaryStore.refresh()
  }
})

watch(() => route.query.status, fetchOrders)
</script>

<template>
  <div class="order-list-page">
    <van-nav-bar
      :title="t('order.listTitle')"
      left-arrow
      fixed
      placeholder
      @click-left="router.back()"
    />

    <van-loading v-if="loading" class="page-loading" vertical>
      {{ t('common.loading') }}
    </van-loading>

    <van-empty v-else-if="loadError" class="page-empty" :description="loadError">
      <van-button round type="primary" size="small" @click="fetchOrders">
        {{ t('common.retry') }}
      </van-button>
    </van-empty>

    <van-empty v-else-if="!displayOrders.length" :description="t('order.empty')" />

    <div v-else class="order-list">
      <div
        v-for="order in displayOrders"
        :key="order.id"
        class="order-card"
        @click="goDetail(order)"
      >
        <div class="order-head">
          <span class="order-no">{{ t('checkout.orderNo', { no: order.order_no }) }}</span>
          <span class="status-text">{{ orderStatusLabel(order) }}</span>
        </div>
        <OrderCountdownTag :expires-at="order.expires_at" :status="order.status" />
        <div v-if="order.status === 'paid' && order.cancel_status === 'pending'" class="cancel-hint">
          {{ t('order.cancelingHint') }}
        </div>
        <div v-if="order.status === 'cancelled' && order.cancel_reason" class="cancel-hint muted">
          {{ t('order.cancelReason') }}：{{ order.cancel_reason }}
        </div>
        <div class="order-shop">
          <span class="shop-label">{{ t('order.shop') }}：</span>
          <span>{{ orderShopName(order) }}</span>
        </div>
        <div class="order-meta">
          <span>{{ t('checkout.payAmount') }}</span>
          <span class="amount">{{ formatPrice(order.total_amount) }}</span>
        </div>
        <div class="order-time">{{ order.created_at?.replace('T', ' ').slice(0, 19) }}</div>
        <div v-if="canDirectCancelOrder(order) || canComplainOrder(order)" class="order-actions">
          <van-button
            v-if="canDirectCancelOrder(order)"
            size="mini"
            type="default"
            plain
            class="action-btn"
            @click="openCancelDialog(order, $event)"
          >
            {{ t('order.cancelOrder') }}
          </van-button>
          <van-button
            v-if="canComplainOrder(order)"
            size="mini"
            type="warning"
            plain
            class="action-btn"
            @click="goComplaint(order, $event)"
          >
            {{ t('complaint.complainOrder') }}
          </van-button>
        </div>
      </div>
    </div>

    <OrderCancelDialog
      v-model:show="cancelVisible"
      :order="cancelTarget"
      mode="cancel"
      :loading="cancelling"
      @confirm="handleCancelConfirm"
    />
  </div>
</template>

<style scoped>
.order-list-page {
  min-height: 100vh;
  background: #f5f6fa;
  padding-bottom: 24px;
}

.page-loading {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.page-empty {
  padding: 80px 16px;
}

.order-list {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.order-card {
  background: #fff;
  border-radius: 8px;
  padding: 14px;
  cursor: pointer;
}

.order-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.order-no {
  font-size: 13px;
  color: #646566;
}

.status-text {
  font-size: 14px;
  font-weight: 600;
  color: #ee0a24;
}

.order-shop {
  margin-top: 8px;
  font-size: 13px;
  color: #646566;
}

.shop-label {
  color: #969799;
}

.order-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 14px;
}

.amount {
  color: #323233;
  font-weight: 600;
}

.order-time {
  margin-top: 6px;
  font-size: 12px;
  color: #969799;
}

.cancel-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #ed6a0c;
}

.cancel-hint.muted {
  color: #969799;
}

.order-actions {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.action-btn {
  min-width: 72px;
}
</style>
