<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showToast } from 'vant'
import { getPointsMallOrders } from '@/api/pointsMall'
import { resolveErrorMessage } from '@/utils/feedback'

const router = useRouter()
const { t } = useI18n()
const loading = ref(false)
const orders = ref([])

const statusOptions = computed(() => ({
  pending: t('pointsMall.statusPending'),
  processing: t('pointsMall.statusProcessing'),
  shipped: t('pointsMall.statusShipped'),
  completed: t('pointsMall.statusCompleted'),
  cancelled: t('pointsMall.statusCancelled'),
}))

function statusLabel(status) {
  return statusOptions.value[status] || status
}

async function fetchOrders() {
  loading.value = true
  try {
    const res = await getPointsMallOrders({ page_size: 50 })
    orders.value = res.data?.results || []
  } catch (error) {
    showToast(resolveErrorMessage(error, 'pointsMall.loadFailed'))
  } finally {
    loading.value = false
  }
}

onMounted(fetchOrders)
</script>

<template>
  <div class="orders-page">
    <van-nav-bar :title="t('pointsMall.ordersTitle')" left-arrow @click-left="router.back()" />
    <van-loading v-if="loading" class="page-loading" size="24px">{{ t('common.loading') }}</van-loading>
    <van-empty v-else-if="!orders.length" :description="t('pointsMall.ordersEmpty')" />
    <van-cell-group v-else inset class="list">
      <van-cell v-for="order in orders" :key="order.id" :title="order.item_name">
        <template #value>
          <div class="value-col">
            <van-tag plain type="primary">{{ statusLabel(order.status) }}</van-tag>
            <span class="points">-{{ order.points_spent }}</span>
          </div>
        </template>
        <template #label>
          <div>{{ order.order_no }}</div>
          <div v-if="order.coupon_code" class="coupon">{{ t('pointsMall.couponCode') }}：{{ order.coupon_code }}</div>
          <div v-if="order.logistics_no" class="logistics">{{ order.logistics_company }} {{ order.logistics_no }}</div>
        </template>
      </van-cell>
    </van-cell-group>
  </div>
</template>

<style scoped>
.orders-page { min-height: 100vh; background: #f7f8fa; }
.page-loading { display: flex; justify-content: center; padding: 40px 0; }
.list { margin-top: 12px; }
.value-col { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.points { color: #ee0a24; font-size: 13px; }
.coupon, .logistics { margin-top: 4px; font-size: 12px; color: #646566; }
</style>
