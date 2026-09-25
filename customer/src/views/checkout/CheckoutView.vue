<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showToast } from 'vant'
import AddressForm from '@/components/address/AddressForm.vue'
import { createAddress, getAddresses } from '@/api/address'
import { createOrder } from '@/api/order'
import { getCheckoutPoints } from '@/api/points'
import { getCheckoutSellerPoints } from '@/api/sellerPoints'
import { getAvailableCoupons } from '@/api/promotion'
import { useCartStore } from '@/stores/cart'
import { maskPhone } from '@/utils/region'
import { formatPrice, resolveImageUrl } from '@/utils/product'

const router = useRouter()
const { t } = useI18n()
const cartStore = useCartStore()

const addresses = ref([])
const selectedAddress = ref(null)
const showAddressPicker = ref(false)
const showAddressForm = ref(false)
const showCouponPicker = ref(false)
const savingAddress = ref(false)
const remark = ref('')
const submitting = ref(false)
const loading = ref(true)

const availableCoupons = ref([])
const selectedCouponId = ref(null)
const usePoints = ref(true)
const pointsInput = ref(0)
const pointsInfo = ref(null)
const useSellerPoints = ref(true)
const sellerPointsInput = ref(0)
const sellerPointsInfo = ref(null)

const checkoutItems = computed(() => cartStore.selectedItems)
const goodsTotal = computed(() => cartStore.selectedTotal)

const selectedCoupon = computed(() =>
  availableCoupons.value.find((item) => item.id === selectedCouponId.value),
)

const couponDiscount = computed(() => {
  if (!selectedCoupon.value?.available) return 0
  return Number(selectedCoupon.value.estimated_discount || 0)
})

const afterCouponTotal = computed(() => Math.max(0, goodsTotal.value - couponDiscount.value))

const checkoutTenantId = computed(() => {
  const item = checkoutItems.value[0]
  return item?.product_detail?.tenant || null
})

const pointsDiscount = computed(() => {
  if (!usePoints.value || !pointsInfo.value) return 0
  const rate = Number(pointsInfo.value.points_per_yuan || 100)
  const maxPoints = Number(pointsInfo.value.max_usable_points || 0)
  const maxAmount = Number(pointsInfo.value.max_deduct_amount || 0)
  const usedPoints = Math.min(Math.max(0, Math.floor(pointsInput.value)), maxPoints)
  const amount = usedPoints / rate
  return Math.min(amount, maxAmount, afterCouponTotal.value)
})

const afterPlatformTotal = computed(() => Math.max(0, afterCouponTotal.value - pointsDiscount.value))

const sellerPointsDiscount = computed(() => {
  if (!useSellerPoints.value || !sellerPointsInfo.value?.enabled) return 0
  const rate = Number(sellerPointsInfo.value.redeem_rate || 100)
  const maxPoints = Number(sellerPointsInfo.value.max_usable_points || 0)
  const maxAmount = Number(sellerPointsInfo.value.max_deduct_amount || 0)
  const usedPoints = Math.min(Math.max(0, Math.floor(sellerPointsInput.value)), maxPoints)
  const amount = usedPoints / rate
  return Math.min(amount, maxAmount, afterPlatformTotal.value)
})

const payAmount = computed(() =>
  Math.max(0, afterPlatformTotal.value - sellerPointsDiscount.value).toFixed(2),
)

const couponPickerColumns = computed(() => [
  { text: t('checkout.noUseCoupon'), value: null },
  ...availableCoupons.value.map((item) => ({
    text: `${item.name} (-${formatPrice(item.estimated_discount)})`,
    value: item.id,
  })),
])

const couponPickerValue = computed(() => [selectedCouponId.value])

const selectedCouponLabel = computed(() => {
  if (!selectedCouponId.value) {
    return t('checkout.noUseCoupon')
  }
  if (!selectedCoupon.value) {
    return t('checkout.selectCouponPlaceholder')
  }
  return `${selectedCoupon.value.name} (-${formatPrice(selectedCoupon.value.estimated_discount)})`
})

const isEmpty = computed(() => checkoutItems.value.length === 0)
const hasAddress = computed(() => Boolean(selectedAddress.value))

function applyMaxPoints() {
  if (!pointsInfo.value) return
  pointsInput.value = Number(pointsInfo.value.max_usable_points || 0)
}

function clampPointsInput() {
  if (!pointsInfo.value) return
  const max = Number(pointsInfo.value.max_usable_points || 0)
  const value = Math.floor(Number(pointsInput.value) || 0)
  pointsInput.value = Math.min(Math.max(0, value), max)
}

async function loadCoupons() {
  try {
    const couponRes = await getAvailableCoupons()
    availableCoupons.value = (couponRes.data || []).filter((item) => item.available)
    if (selectedCouponId.value && !availableCoupons.value.some((item) => item.id === selectedCouponId.value)) {
      selectedCouponId.value = null
    }
  } catch {
    availableCoupons.value = []
    selectedCouponId.value = null
  }
}

function applyMaxSellerPoints() {
  if (!sellerPointsInfo.value) return
  sellerPointsInput.value = Number(sellerPointsInfo.value.max_usable_points || 0)
}

function clampSellerPointsInput() {
  if (!sellerPointsInfo.value) return
  const max = Number(sellerPointsInfo.value.max_usable_points || 0)
  const value = Math.floor(Number(sellerPointsInput.value) || 0)
  sellerPointsInput.value = Math.min(Math.max(0, value), max)
}

async function loadSellerPointsInfo() {
  if (!checkoutTenantId.value) {
    sellerPointsInfo.value = null
    return
  }
  try {
    const res = await getCheckoutSellerPoints({
      tenant_id: checkoutTenantId.value,
      order_amount: afterPlatformTotal.value || afterCouponTotal.value || goodsTotal.value,
    })
    sellerPointsInfo.value = res.data
    if (useSellerPoints.value && sellerPointsInfo.value?.enabled) {
      applyMaxSellerPoints()
    } else {
      clampSellerPointsInput()
    }
  } catch {
    sellerPointsInfo.value = null
  }
}

async function loadPointsInfo() {
  try {
    const pointsRes = await getCheckoutPoints({
      order_amount: afterCouponTotal.value || goodsTotal.value,
    })
    pointsInfo.value = pointsRes.data
    if (usePoints.value) {
      applyMaxPoints()
    } else {
      clampPointsInput()
    }
  } catch {
    pointsInfo.value = null
  }
}

async function loadPromotions() {
  await loadCoupons()
  await loadPointsInfo()
  await loadSellerPointsInfo()
}

function formatAddressLine(addr) {
  if (!addr) return ''
  return `${addr.province} ${addr.city} ${addr.district} ${addr.detail}`
}

async function fetchAddresses() {
  loading.value = true
  try {
    const res = await getAddresses()
    addresses.value = res.data || []
    selectedAddress.value =
      addresses.value.find((item) => item.is_default) || addresses.value[0] || null
  } catch {
    addresses.value = []
    selectedAddress.value = null
  } finally {
    loading.value = false
  }
}

function selectAddress(addr) {
  selectedAddress.value = addr
  showAddressPicker.value = false
}

function openAddressForm() {
  showAddressPicker.value = false
  showAddressForm.value = true
}

function goToAddressManage() {
  showAddressPicker.value = false
  router.push({ name: 'AddressManage' })
}

async function handleCreateAddress(formData) {
  savingAddress.value = true
  try {
    const res = await createAddress(formData)
    showToast(t('address.createSuccess'))
    showAddressForm.value = false
    await fetchAddresses()
    selectedAddress.value = res.data || addresses.value[0] || null
  } finally {
    savingAddress.value = false
  }
}

function onCouponConfirm({ selectedOptions }) {
  selectedCouponId.value = selectedOptions[0]?.value ?? null
  showCouponPicker.value = false
}

function onPointsToggle(checked) {
  usePoints.value = checked
  if (checked) {
    applyMaxPoints()
  } else {
    pointsInput.value = 0
  }
}

function onSellerPointsToggle(checked) {
  useSellerPoints.value = checked
  if (checked) {
    applyMaxSellerPoints()
  } else {
    sellerPointsInput.value = 0
  }
}

async function handleSubmit() {
  if (isEmpty.value) {
    showToast(t('checkout.noSelectedItems'))
    router.push({ name: 'Cart' })
    return
  }
  if (!selectedAddress.value) {
    showToast(t('checkout.addAddressFirst'))
    openAddressForm()
    return
  }

  clampPointsInput()
  clampSellerPointsInput()

  submitting.value = true
  try {
    const payload = {
      address_id: selectedAddress.value.id,
      remark: remark.value.trim(),
      items: checkoutItems.value.map((item) => ({
        cart_item_id: item.id,
        quantity: item.quantity,
      })),
      use_points: usePoints.value,
      use_seller_points: useSellerPoints.value,
    }
    if (selectedCouponId.value) {
      payload.coupon_id = selectedCouponId.value
    }
    if (usePoints.value && pointsInput.value > 0) {
      payload.points_amount = Math.floor(pointsInput.value)
    }
    if (useSellerPoints.value && sellerPointsInput.value > 0) {
      payload.seller_points_amount = Math.floor(sellerPointsInput.value)
    }
    const res = await createOrder(payload)
    await cartStore.fetchCart()
    showToast(t('checkout.submitSuccess'))
    router.replace({ name: 'OrderDetail', params: { id: res.data.id } })
  } catch {
    // handled by interceptor
  } finally {
    submitting.value = false
  }
}

watch(goodsTotal, () => {
  if (!loading.value) {
    loadPromotions()
  }
})

watch(selectedCouponId, () => {
  if (!loading.value) {
    loadPointsInfo().then(loadSellerPointsInfo)
  }
})

watch(pointsInput, () => {
  clampPointsInput()
})

watch(afterPlatformTotal, () => {
  if (!loading.value) {
    loadSellerPointsInfo()
  }
})

watch(sellerPointsInput, () => {
  clampSellerPointsInput()
})

onMounted(async () => {
  await cartStore.fetchCart()
  if (isEmpty.value) {
    loading.value = false
    return
  }
  await fetchAddresses()
  await loadPromotions()
})
</script>

<template>
  <div class="checkout-page">
    <van-nav-bar
      :title="t('checkout.title')"
      left-arrow
      fixed
      placeholder
      @click-left="router.back()"
    />

    <van-loading v-if="loading" class="page-loading" vertical>
      {{ t('common.loading') }}
    </van-loading>

    <div v-else-if="isEmpty" class="empty-state">
      <van-empty :description="t('checkout.noSelectedItems')" />
      <van-button type="primary" round @click="router.push({ name: 'Cart' })">
        {{ t('checkout.backToCart') }}
      </van-button>
    </div>

    <template v-else>
      <section v-if="!hasAddress" class="card address-empty-card">
        <div class="address-empty-banner">
          <van-icon name="location-o" size="24" color="#ee0a24" />
          <div class="address-empty-text">
            <div class="address-empty-title">{{ t('checkout.noAddressTitle') }}</div>
            <div class="address-empty-desc">{{ t('checkout.noAddressDesc') }}</div>
          </div>
        </div>
        <van-button type="danger" block round icon="plus" @click="openAddressForm">
          {{ t('checkout.addAddressNow') }}
        </van-button>
      </section>

      <section v-else class="card address-card" @click="showAddressPicker = true">
        <div class="address-content">
          <div class="address-head">
            <span class="address-name">{{ selectedAddress.name }}</span>
            <span class="address-phone">{{ maskPhone(selectedAddress.phone) }}</span>
            <van-tag v-if="selectedAddress.is_default" type="primary" size="small">
              {{ t('checkout.defaultTag') }}
            </van-tag>
          </div>
          <div class="address-detail">{{ formatAddressLine(selectedAddress) }}</div>
          <div class="address-action">{{ t('checkout.chooseOtherAddress') }}</div>
        </div>
      </section>

      <section class="card">
        <div class="section-title">{{ t('checkout.goodsList') }}</div>
        <div v-for="item in checkoutItems" :key="item.id" class="goods-item">
          <img :src="resolveImageUrl(item.product_detail?.image)" class="goods-image" alt="" />
          <div class="goods-info">
            <div class="goods-name">{{ item.product_detail?.name }}</div>
            <div class="goods-meta">
              <span class="goods-price">{{ formatPrice(item.product_detail?.price) }}</span>
              <span class="goods-qty">x{{ item.quantity }}</span>
            </div>
          </div>
          <div class="goods-subtotal">
            {{ formatPrice(Number(item.product_detail?.price || 0) * item.quantity) }}
          </div>
        </div>
      </section>

      <section class="card promo-card">
        <div class="section-title">{{ t('checkout.coupon') }}</div>
        <van-field
          is-link
          readonly
          :label="t('checkout.selectCoupon')"
          :model-value="selectedCouponLabel"
          :placeholder="t('checkout.selectCouponPlaceholder')"
          @click="showCouponPicker = true"
        />
        <div v-if="!availableCoupons.length" class="promo-empty">{{ t('checkout.noCoupon') }}</div>
      </section>

      <section class="card promo-card">
        <div class="section-title">{{ t('checkout.pointsDeduction') }}</div>
        <template v-if="pointsInfo">
          <div class="points-row">
            <span>{{ t('checkout.pointsBalance', { count: pointsInfo.balance }) }}</span>
            <van-switch :model-value="usePoints" size="20" @update:model-value="onPointsToggle" />
          </div>
          <div v-if="usePoints" class="points-input-row">
            <van-field
              v-model.number="pointsInput"
              type="digit"
              :label="t('checkout.usePoints')"
              :placeholder="t('checkout.pointsPlaceholder')"
            />
            <div class="points-hint">
              {{ t('checkout.pointsDeductHint', { amount: pointsDiscount.toFixed(2) }) }}
            </div>
          </div>
        </template>
        <div v-else class="promo-empty">{{ t('checkout.noPointsDeduction') }}</div>
      </section>

      <section class="card promo-card">
        <div class="section-title">{{ t('checkout.sellerPointsDeduction') }}</div>
        <template v-if="sellerPointsInfo?.enabled">
          <div class="points-row">
            <span>{{
              t('checkout.sellerPointsBalance', {
                name: sellerPointsInfo.points_name,
                count: sellerPointsInfo.balance,
              })
            }}</span>
            <van-switch
              :model-value="useSellerPoints"
              size="20"
              @update:model-value="onSellerPointsToggle"
            />
          </div>
          <div v-if="useSellerPoints" class="points-input-row">
            <van-field
              v-model.number="sellerPointsInput"
              type="digit"
              :label="t('checkout.useSellerPoints')"
              :placeholder="t('checkout.pointsPlaceholder')"
            />
            <div class="points-hint">
              {{ t('checkout.sellerPointsDeductHint', { amount: sellerPointsDiscount.toFixed(2) }) }}
            </div>
          </div>
        </template>
        <div v-else class="promo-empty">{{ t('checkout.noSellerPointsDeduction') }}</div>
      </section>

      <section class="card">
        <van-field
          v-model="remark"
          rows="2"
          autosize
          type="textarea"
          maxlength="200"
          :placeholder="t('checkout.remarkPlaceholder')"
          show-word-limit
        />
      </section>

      <section class="card summary-card">
        <div class="summary-row">
          <span>{{ t('checkout.goodsAmount') }}</span>
          <span>{{ formatPrice(goodsTotal) }}</span>
        </div>
        <div v-if="couponDiscount > 0" class="summary-row discount">
          <span>{{ t('checkout.coupon') }}</span>
          <span>-{{ formatPrice(couponDiscount) }}</span>
        </div>
        <div v-if="pointsDiscount > 0" class="summary-row discount">
          <span>{{ t('checkout.pointsDeduction') }}</span>
          <span>-{{ formatPrice(pointsDiscount) }}</span>
        </div>
        <div v-if="sellerPointsDiscount > 0" class="summary-row discount">
          <span>{{ t('checkout.sellerPointsDeduction') }}</span>
          <span>-{{ formatPrice(sellerPointsDiscount) }}</span>
        </div>
        <div class="summary-row muted">
          <span>{{ t('checkout.shippingFee') }}</span>
          <span>{{ t('checkout.freeShipping') }}</span>
        </div>
        <div class="summary-row pay-row">
          <span>{{ t('checkout.payAmount') }}</span>
          <span class="pay-amount">¥{{ payAmount }}</span>
        </div>
      </section>

      <div class="checkout-footer">
        <div class="footer-total">
          <span>{{ t('checkout.payAmount') }}</span>
          <span class="pay-amount">¥{{ payAmount }}</span>
        </div>
        <van-button type="danger" round :loading="submitting" :disabled="submitting" @click="handleSubmit">
          {{ t('checkout.submitOrder') }}
        </van-button>
      </div>
    </template>

    <van-popup v-model:show="showCouponPicker" position="bottom" round>
      <van-picker
        :title="t('checkout.selectCoupon')"
        :columns="couponPickerColumns"
        :model-value="couponPickerValue"
        @confirm="onCouponConfirm"
        @cancel="showCouponPicker = false"
      />
    </van-popup>

    <van-action-sheet v-model:show="showAddressPicker" :title="t('checkout.chooseAddress')">
      <div class="address-list">
        <div
          v-for="addr in addresses"
          :key="addr.id"
          class="address-item"
          :class="{ active: selectedAddress?.id === addr.id }"
          @click="selectAddress(addr)"
        >
          <div class="address-item-head">
            <span>{{ addr.name }} {{ maskPhone(addr.phone) }}</span>
            <van-tag v-if="addr.is_default" type="primary" size="small">
              {{ t('checkout.defaultTag') }}
            </van-tag>
          </div>
          <div class="address-item-detail">{{ formatAddressLine(addr) }}</div>
        </div>
        <van-button type="primary" block plain icon="plus" @click="openAddressForm">
          {{ t('checkout.addAddressNow') }}
        </van-button>
        <van-button type="default" block plain @click="goToAddressManage">
          {{ t('checkout.manageAddress') }}
        </van-button>
      </div>
    </van-action-sheet>

    <AddressForm v-model="showAddressForm" :saving="savingAddress" @submit="handleCreateAddress" />
  </div>
</template>

<style scoped>
.checkout-page {
  min-height: 100vh;
  background: #f5f6fa;
  padding-bottom: 80px;
}

.page-loading {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 60px 16px;
}

.card {
  margin: 12px;
  padding: 14px;
  background: #fff;
  border-radius: 8px;
}

.section-title {
  margin-bottom: 12px;
  font-size: 15px;
  font-weight: 600;
  color: #323233;
}

.promo-empty {
  margin-top: 4px;
  color: #969799;
  font-size: 13px;
}

.promo-card :deep(.van-field) {
  padding-left: 0;
  padding-right: 0;
}

.points-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.points-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #969799;
}

.summary-row.discount {
  color: #ee0a24;
}

.address-empty-card {
  border: 1px dashed #ee0a24;
  background: #fff7f7;
}

.address-empty-banner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
}

.address-empty-title {
  font-size: 16px;
  font-weight: 600;
}

.address-card {
  cursor: pointer;
}

.address-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.address-name {
  font-size: 16px;
  font-weight: 600;
}

.address-phone {
  font-size: 14px;
  color: #646566;
}

.address-detail {
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.5;
}

.address-action {
  margin-top: 10px;
  font-size: 13px;
  color: #1989fa;
}

.goods-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #f5f5f5;
}

.goods-item:last-child {
  border-bottom: none;
}

.goods-image {
  width: 64px;
  height: 64px;
  border-radius: 4px;
  object-fit: cover;
  background: #f0f2f5;
}

.goods-info {
  flex: 1;
  min-width: 0;
}

.goods-name {
  font-size: 14px;
  line-height: 1.4;
}

.goods-meta {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.goods-price {
  color: #ee0a24;
  font-weight: 600;
}

.goods-qty {
  color: #969799;
  font-size: 13px;
}

.goods-subtotal {
  font-size: 14px;
  font-weight: 600;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  font-size: 14px;
}

.summary-row.muted {
  color: #969799;
}

.pay-row {
  margin-top: 4px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
  font-weight: 600;
}

.pay-amount {
  color: #ee0a24;
  font-size: 18px;
  font-weight: 700;
}

.checkout-footer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #fff;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.06);
  z-index: 10;
}

.footer-total {
  flex: 1;
  font-size: 14px;
}

.checkout-footer .van-button {
  min-width: 120px;
}

.address-list {
  padding: 0 16px 24px;
  max-height: 60vh;
  overflow-y: auto;
}

.address-item {
  padding: 14px 0;
  border-bottom: 1px solid #f0f0f0;
}

.address-item.active {
  background: #f7fbff;
}

.address-item-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.address-item-detail {
  margin-top: 6px;
  font-size: 13px;
  color: #646566;
  line-height: 1.5;
}
</style>
