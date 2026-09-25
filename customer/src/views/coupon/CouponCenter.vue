<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showToast } from 'vant'
import { getMyCoupons, getPublishCoupons, receiveCoupon } from '@/api/promotion'
import {
  formatCouponThreshold,
  formatCouponValidity,
  formatCouponValue,
} from '@/utils/promotionFormat'

const router = useRouter()
const { t } = useI18n()

const activeTab = ref('unused')
const coupons = ref([])
const publishList = ref([])
const loading = ref(true)
const receivingId = ref(null)

const statusLabelMap = {
  unused: 'coupon.statusUnused',
  used: 'coupon.statusUsed',
  expired: 'coupon.statusExpired',
}

function couponStatusLabel(status) {
  return t(statusLabelMap[status] || 'coupon.statusUnused')
}

async function fetchCoupons() {
  loading.value = true
  try {
    const res = await getMyCoupons({ status: activeTab.value })
    coupons.value = res.data || []
  } finally {
    loading.value = false
  }
}

async function fetchPublish() {
  try {
    const res = await getPublishCoupons()
    publishList.value = res.data || []
  } catch {
    publishList.value = []
  }
}

async function handleReceive(couponId) {
  receivingId.value = couponId
  try {
    await receiveCoupon(couponId)
    showToast(t('coupon.receiveSuccess'))
    await Promise.all([fetchCoupons(), fetchPublish()])
  } catch {
    // handled
  } finally {
    receivingId.value = null
  }
}

function useCoupon() {
  router.push({ name: 'Cart' })
}

onMounted(async () => {
  await Promise.all([fetchCoupons(), fetchPublish()])
})
</script>

<template>
  <div class="coupon-page">
    <van-nav-bar :title="t('coupon.title')" left-arrow fixed placeholder @click-left="router.back()" />

    <van-tabs v-model:active="activeTab" @change="fetchCoupons">
      <van-tab name="unused" :title="t('coupon.tabUnused')" />
      <van-tab name="used" :title="t('coupon.tabUsed')" />
      <van-tab name="expired" :title="t('coupon.tabExpired')" />
    </van-tabs>

    <van-loading v-if="loading" class="page-loading" vertical>{{ t('common.loading') }}</van-loading>

    <div v-else class="coupon-list">
      <section v-if="activeTab === 'unused' && publishList.length" class="receive-section">
        <div class="section-label">{{ t('coupon.receiveSection') }}</div>
        <div
          v-for="item in publishList"
          :key="`pub-${item.id}`"
          class="coupon-card publish-card"
        >
          <div class="coupon-card__value">{{ formatCouponValue(item) }}</div>
          <div class="coupon-card__main">
            <div class="coupon-card__name">{{ item.name }}</div>
            <div class="coupon-card__meta">{{ formatCouponThreshold(item, t) }}</div>
            <div class="coupon-card__date">{{ formatCouponValidity(item, t) }}</div>
          </div>
          <van-button
            size="small"
            type="danger"
            round
            :disabled="!item.can_receive"
            :loading="receivingId === item.id"
            @click="handleReceive(item.id)"
          >
            {{ item.can_receive ? t('coupon.receive') : t('coupon.received') }}
          </van-button>
        </div>
      </section>

      <van-empty v-if="!coupons.length" :description="t('coupon.empty')" />

      <div v-for="item in coupons" :key="item.id" class="coupon-card">
        <div class="coupon-card__value">{{ formatCouponValue(item.coupon) }}</div>
        <div class="coupon-card__main">
          <div class="coupon-card__name">{{ item.coupon.name }}</div>
          <div class="coupon-card__meta">{{ formatCouponThreshold(item.coupon, t) }}</div>
          <div class="coupon-card__date">
            {{ t('coupon.validUntil', { date: item.expired_at.slice(0, 10) }) }}
          </div>
          <div class="coupon-card__status">{{ couponStatusLabel(item.status) }}</div>
        </div>
        <van-button
          v-if="activeTab === 'unused'"
          size="small"
          type="danger"
          round
          @click="useCoupon"
        >
          {{ t('coupon.useNow') }}
        </van-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.coupon-page {
  min-height: 100vh;
  background: #f5f6fa;
}

.page-loading {
  padding: 60px 0;
  display: flex;
  justify-content: center;
}

.coupon-list {
  padding: 12px;
}

.receive-section {
  margin-bottom: 12px;
}

.section-label {
  margin-bottom: 8px;
  font-size: 13px;
  color: #969799;
}

.coupon-card {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
  padding: 14px;
  background: #fff;
  border-radius: 8px;
  border-left: 4px solid #ee0a24;
}

.publish-card {
  background: linear-gradient(90deg, #fff7f7 0%, #fff 40%);
}

.coupon-card__value {
  min-width: 64px;
  font-size: 20px;
  font-weight: 700;
  color: #ee0a24;
  text-align: center;
}

.coupon-card__main {
  flex: 1;
  min-width: 0;
}

.coupon-card__name {
  font-size: 15px;
  font-weight: 600;
  color: #323233;
}

.coupon-card__meta,
.coupon-card__date,
.coupon-card__status {
  margin-top: 4px;
  font-size: 12px;
  color: #969799;
}

.coupon-card__status {
  color: #ee0a24;
}
</style>
