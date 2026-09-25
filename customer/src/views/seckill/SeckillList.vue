<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showToast } from 'vant'
import { getAddresses } from '@/api/address'
import { getSeckillActivities, getSeckillProducts, seckillBuy } from '@/api/promotion'
import { usePromoCountdown } from '@/composables/usePromoCountdown'
import { requireLogin } from '@/stores/loginGate'
import { formatSeckillPhase } from '@/utils/promotionFormat'
import { formatPrice, resolveImageUrl } from '@/utils/product'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const activities = ref([])
const products = ref([])
const loading = ref(true)
const buyingId = ref(null)
const showAddressPicker = ref(false)
const addresses = ref([])
const pendingBuyItem = ref(null)

const selectedActivityId = computed(() => {
  const raw = route.query.activity_id
  return raw ? Number(raw) : null
})

const showProducts = computed(() => Boolean(selectedActivityId.value))

const selectedActivity = computed(() =>
  activities.value.find((item) => item.id === selectedActivityId.value),
)

const pageTitle = computed(() => {
  if (showProducts.value && selectedActivity.value) {
    return selectedActivity.value.name
  }
  return t('seckill.title')
})

const activeEndTime = computed(() => {
  if (showProducts.value && products.value.length) {
    return products.value[0].end_time
  }
  return null
})

const { countdownText } = usePromoCountdown(activeEndTime)

function formatActivityTime(item) {
  const start = item.start_time?.slice(0, 16).replace('T', ' ')
  const end = item.end_time?.slice(0, 16).replace('T', ' ')
  return `${start} ~ ${end}`
}

async function fetchActivities() {
  const res = await getSeckillActivities()
  activities.value = res.data || []
}

async function fetchProducts() {
  if (!selectedActivityId.value) {
    products.value = []
    return
  }
  const res = await getSeckillProducts({ activity_id: selectedActivityId.value })
  products.value = res.data || []
}

async function loadPage() {
  loading.value = true
  try {
    if (showProducts.value) {
      await Promise.all([fetchActivities(), fetchProducts()])
    } else {
      await fetchActivities()
      products.value = []
    }
  } catch {
    activities.value = []
    products.value = []
  } finally {
    loading.value = false
  }
}

function openActivity(activity) {
  router.push({ name: route.name, query: { activity_id: activity.id } })
}

function handleNavBack() {
  if (showProducts.value) {
    if (window.history.state?.back) {
      router.back()
      return
    }
    router.replace({ name: 'Seckill' })
    return
  }
  if (window.history.state?.back) {
    router.back()
    return
  }
  router.push({ name: 'Home' })
}

async function ensureAddresses() {
  const res = await getAddresses()
  addresses.value = res.data || []
  return addresses.value
}

async function handleBuy(item) {
  try {
    await requireLogin({ redirect: route.fullPath })
  } catch {
    return
  }

  pendingBuyItem.value = item
  const list = await ensureAddresses()
  if (!list.length) {
    showToast(t('checkout.addAddressFirst'))
    router.push({ name: 'AddressManage', query: { redirect: route.fullPath } })
    return
  }
  if (list.length === 1) {
    await submitBuy(list[0].id)
    return
  }
  showAddressPicker.value = true
}

async function submitBuy(addressId) {
  const item = pendingBuyItem.value
  if (!item) return

  buyingId.value = `${item.activity_id}-${item.product_id}`
  showAddressPicker.value = false
  try {
    const res = await seckillBuy(item.activity_id, {
      address_id: addressId,
      quantity: 1,
    })
    showToast(t('seckill.buySuccess'))
    await fetchProducts()
    router.push({ name: 'OrderDetail', params: { id: res.data.id } })
  } catch {
    // handled by interceptor
  } finally {
    buyingId.value = null
    pendingBuyItem.value = null
  }
}

watch(
  () => route.query.activity_id,
  () => loadPage(),
)

onMounted(loadPage)
</script>

<template>
  <div class="seckill-page">
    <van-nav-bar
      :title="pageTitle"
      left-arrow
      fixed
      placeholder
      @click-left="handleNavBack"
    />

    <van-loading v-if="loading" class="page-loading" vertical>{{ t('common.loading') }}</van-loading>

    <template v-else-if="showProducts">
      <section v-if="selectedActivity" class="activity-banner">
        <div class="activity-banner__title">{{ selectedActivity.name }}</div>
        <div class="activity-banner__meta">
          <van-tag type="danger" plain>{{ formatSeckillPhase(selectedActivity.phase, t) }}</van-tag>
          <span v-if="countdownText !== '00:00:00'" class="countdown">
            {{ t('seckill.endIn') }} {{ countdownText }}
          </span>
        </div>
      </section>

      <van-empty v-if="!products.length" :description="t('seckill.emptyProducts')" />

      <div v-else class="product-list">
        <div
          v-for="item in products"
          :key="`${item.activity_id}-${item.product_id}`"
          class="product-card"
        >
          <img :src="resolveImageUrl(item.image)" class="product-card__img" alt="" />
          <div class="product-card__body">
            <div class="product-card__name">{{ item.product_name }}</div>
            <div class="product-card__price">
              <span class="seckill-price">{{ formatPrice(item.seckill_price) }}</span>
              <span class="origin-price">{{ formatPrice(item.original_price) }}</span>
            </div>
            <div class="progress-row">
              <van-progress
                :percentage="item.sold_percent || 0"
                stroke-width="8"
                color="#ee0a24"
                track-color="#ffe1e1"
                :show-pivot="false"
              />
              <span class="progress-text">
                {{ t('seckill.soldPercent', { percent: item.sold_percent || 0 }) }}
              </span>
            </div>
            <div class="product-card__meta">
              <span>{{ t('seckill.stockLeft', { count: item.remaining_stock ?? item.seckill_stock }) }}</span>
              <span v-if="countdownText !== '00:00:00'">{{ t('seckill.endIn') }} {{ countdownText }}</span>
            </div>
            <van-button
              type="danger"
              size="small"
              block
              round
              :loading="buyingId === `${item.activity_id}-${item.product_id}`"
              @click="handleBuy(item)"
            >
              {{ t('seckill.buyNow') }}
            </van-button>
          </div>
        </div>
      </div>
    </template>

    <template v-else>
      <van-empty v-if="!activities.length" :description="t('seckill.empty')" />

      <div v-else class="activity-list">
        <div
          v-for="item in activities"
          :key="item.id"
          class="activity-card"
          @click="openActivity(item)"
        >
          <img
            v-if="item.product?.image"
            :src="resolveImageUrl(item.product.image)"
            class="activity-card__img"
            alt=""
          />
          <div class="activity-card__body">
            <div class="activity-card__head">
              <div class="activity-card__name">{{ item.name }}</div>
              <van-tag
                :type="item.phase === 'ongoing' ? 'danger' : 'default'"
                plain
              >
                {{ formatSeckillPhase(item.phase, t) }}
              </van-tag>
            </div>
            <div class="activity-card__time">{{ formatActivityTime(item) }}</div>
            <div v-if="item.product" class="activity-card__price">
              <span class="seckill-price">{{ formatPrice(item.seckill_price) }}</span>
              <span class="origin-price">{{ formatPrice(item.product.price) }}</span>
            </div>
            <div v-if="item.phase === 'ongoing'" class="activity-card__progress">
              {{ t('seckill.soldPercent', { percent: item.sold_percent || 0 }) }}
            </div>
          </div>
          <van-icon name="arrow" class="activity-card__arrow" />
        </div>
      </div>
    </template>

    <van-action-sheet v-model:show="showAddressPicker" :title="t('checkout.chooseAddress')">
      <div class="address-list">
        <div
          v-for="addr in addresses"
          :key="addr.id"
          class="address-item"
          @click="submitBuy(addr.id)"
        >
          <div class="address-item__name">{{ addr.name }} {{ addr.phone }}</div>
          <div class="address-item__detail">
            {{ addr.province }} {{ addr.city }} {{ addr.district }} {{ addr.detail }}
          </div>
        </div>
      </div>
    </van-action-sheet>
  </div>
</template>

<style scoped>
.seckill-page {
  min-height: 100vh;
  background: #f5f6fa;
  padding-bottom: 16px;
}

.page-loading {
  padding: 60px 0;
  display: flex;
  justify-content: center;
}

.activity-banner {
  margin: 12px;
  padding: 14px;
  background: linear-gradient(135deg, #fff5f5 0%, #fff 100%);
  border-radius: 8px;
}

.activity-banner__title {
  font-size: 16px;
  font-weight: 700;
}

.activity-banner__meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  font-size: 13px;
  color: #ee0a24;
}

.activity-list,
.product-list {
  padding: 12px;
}

.activity-card,
.product-card {
  display: flex;
  gap: 12px;
  margin-bottom: 10px;
  padding: 12px;
  background: #fff;
  border-radius: 8px;
}

.activity-card {
  align-items: center;
  cursor: pointer;
}

.activity-card__img,
.product-card__img {
  width: 88px;
  height: 88px;
  border-radius: 8px;
  object-fit: cover;
  background: #f0f2f5;
  flex-shrink: 0;
}

.activity-card__body,
.product-card__body {
  flex: 1;
  min-width: 0;
}

.activity-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.activity-card__name,
.product-card__name {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.4;
}

.activity-card__time {
  margin-top: 6px;
  font-size: 12px;
  color: #969799;
}

.activity-card__price,
.product-card__price {
  margin-top: 8px;
}

.seckill-price {
  color: #ee0a24;
  font-size: 18px;
  font-weight: 700;
}

.origin-price {
  margin-left: 8px;
  color: #969799;
  font-size: 12px;
  text-decoration: line-through;
}

.activity-card__progress {
  margin-top: 6px;
  font-size: 12px;
  color: #ee0a24;
}

.activity-card__arrow {
  color: #c8c9cc;
}

.progress-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 0;
}

.progress-row :deep(.van-progress) {
  flex: 1;
}

.progress-text {
  font-size: 12px;
  color: #ee0a24;
  white-space: nowrap;
}

.product-card__meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 12px;
  color: #969799;
}

.address-list {
  padding: 0 16px 24px;
}

.address-item {
  padding: 14px 0;
  border-bottom: 1px solid #f0f0f0;
}

.address-item__name {
  font-weight: 600;
}

.address-item__detail {
  margin-top: 6px;
  font-size: 13px;
  color: #646566;
  line-height: 1.5;
}
</style>
