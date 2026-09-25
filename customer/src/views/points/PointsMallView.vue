<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showToast } from 'vant'
import { getAddresses } from '@/api/address'
import { exchangePointsMallItem, getPointsMallItems } from '@/api/pointsMall'
import { resolveImageUrl } from '@/utils/product'
import { resolveErrorMessage, toastSuccess } from '@/utils/feedback'

const router = useRouter()
const { t } = useI18n()

const loading = ref(false)
const profile = ref(null)
const items = ref([])
const activeSort = ref('default')
const activeCategory = ref('all')
const exchangeVisible = ref(false)
const exchangeItem = ref(null)
const quantity = ref(1)
const submitting = ref(false)
const addresses = ref([])
const selectedAddressId = ref(null)
const nowTick = ref(Date.now())
const fetchedAt = ref(Date.now())
let tickTimer = null

const sortTabs = computed(() => [
  { key: 'default', label: t('pointsMall.tabAll') },
  { key: 'ending', label: t('pointsMall.tabEnding') },
  { key: 'hot', label: t('pointsMall.tabHot') },
  { key: 'new', label: t('pointsMall.tabNew') },
])

const categoryTabs = computed(() => [
  { key: 'all', label: t('pointsMall.tabAll') },
  { key: 'physical', label: t('pointsMall.tabPhysical') },
  { key: 'coupon', label: t('pointsMall.tabCoupon') },
  { key: 'benefit', label: t('pointsMall.tabBenefit') },
  { key: 'lottery', label: t('pointsMall.tabLottery') },
])

const selectedAddress = computed(() => addresses.value.find((a) => a.id === selectedAddressId.value) || null)

function formatEndsIn(seconds) {
  if (seconds == null || seconds <= 0) return ''
  void nowTick.value
  const elapsed = Math.floor((Date.now() - fetchedAt.value) / 1000)
  const total = Math.max(0, seconds - elapsed)
  const days = Math.floor(total / 86400)
  const hours = Math.floor((total % 86400) / 3600)
  const minutes = Math.floor((total % 3600) / 60)
  return t('pointsMall.endsIn', { days, hours, minutes })
}

async function fetchItems() {
  loading.value = true
  try {
    const params = {
      page_size: 50,
      sort: activeSort.value === 'default' ? undefined : activeSort.value,
    }
    if (activeCategory.value !== 'all') {
      params.category = activeCategory.value
    }
    const res = await getPointsMallItems(params)
    items.value = res.data?.results || []
    profile.value = res.data?.profile || profile.value
    fetchedAt.value = Date.now()
  } catch (error) {
    showToast(resolveErrorMessage(error, 'pointsMall.loadFailed'))
  } finally {
    loading.value = false
  }
}

async function openExchange(item) {
  exchangeItem.value = item
  quantity.value = 1
  exchangeVisible.value = true
  if (item.requires_address) {
    try {
      const res = await getAddresses()
      addresses.value = res.data?.results || res.data || []
      selectedAddressId.value = addresses.value.find((a) => a.is_default)?.id || addresses.value[0]?.id || null
    } catch {
      addresses.value = []
    }
  }
}

async function submitExchange() {
  if (!exchangeItem.value) return
  submitting.value = true
  try {
    const payload = { quantity: quantity.value }
    if (exchangeItem.value.requires_address) {
      if (!selectedAddress.value) {
        showToast(t('pointsMall.addressRequired'))
        submitting.value = false
        return
      }
      payload.address = {
        name: selectedAddress.value.name,
        phone: selectedAddress.value.phone,
        province: selectedAddress.value.province,
        city: selectedAddress.value.city,
        district: selectedAddress.value.district,
        detail: selectedAddress.value.detail,
      }
    }
    const res = await exchangePointsMallItem(exchangeItem.value.id, payload)
    toastSuccess(res.message || t('pointsMall.exchangeSuccess'))
    exchangeVisible.value = false
    await fetchItems()
  } catch (error) {
    showToast(resolveErrorMessage(error, 'pointsMall.exchangeFailed'))
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchItems()
  tickTimer = window.setInterval(() => {
    nowTick.value = Date.now()
  }, 60000)
})

onUnmounted(() => {
  if (tickTimer) window.clearInterval(tickTimer)
})

watch([activeSort, activeCategory], fetchItems)
</script>

<template>
  <div class="points-mall-page">
    <van-nav-bar :title="t('pointsMall.title')" left-arrow @click-left="router.back()" />

    <div v-if="profile" class="balance-bar">
      {{ t('pointsMall.myPoints', { count: profile.balance }) }}
      <span v-if="profile.balance_yuan_display" class="yuan">{{ profile.balance_yuan_display }}</span>
    </div>

    <div class="quick-nav">
      <button type="button" class="nav-item" @click="router.push({ name: 'PointsMallOrders' })">
        <span>🎁</span><small>{{ t('pointsMall.navOrders') }}</small>
      </button>
      <button type="button" class="nav-item" @click="router.push({ name: 'PointsCenter' })">
        <span>💳</span><small>{{ t('pointsMall.navLedger') }}</small>
      </button>
    </div>

    <van-tabs v-model:active="activeSort" shrink sticky offset-top="46">
      <van-tab v-for="tab in sortTabs" :key="tab.key" :name="tab.key" :title="tab.label" />
    </van-tabs>

    <div class="category-row">
      <button
        v-for="tab in categoryTabs"
        :key="tab.key"
        type="button"
        class="category-chip"
        :class="{ active: activeCategory === tab.key }"
        @click="activeCategory = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <van-loading v-if="loading" class="page-loading" size="24px">{{ t('common.loading') }}</van-loading>
    <van-empty v-else-if="!items.length" :description="t('pointsMall.empty')" />

    <div v-else class="grid">
      <article v-for="item in items" :key="item.id" class="card" @click="openExchange(item)">
        <div class="img-wrap">
          <img v-if="item.image" :src="resolveImageUrl(item.image)" alt="" />
          <div v-else class="img-fallback">{{ item.name.charAt(0) }}</div>
          <van-tag v-if="item.is_hot" type="danger" class="tag tag-hot">{{ t('pointsMall.hot') }}</van-tag>
          <van-tag v-else-if="item.is_new" type="primary" class="tag tag-new">{{ t('pointsMall.newTag') }}</van-tag>
        </div>
        <div class="name">{{ item.name }}</div>
        <div class="points">{{ t('pointsMall.pointsCost', { count: item.points_required }) }}</div>
        <div v-if="item.ends_in_seconds" class="countdown">{{ formatEndsIn(item.ends_in_seconds) }}</div>
        <div class="meta">
          <span v-if="activeSort === 'hot' || item.is_hot">🔥 </span>
          {{ t('pointsMall.exchanged', { count: item.exchanged_count }) }}
        </div>
      </article>
    </div>

    <van-popup v-model:show="exchangeVisible" round position="bottom" :style="{ maxHeight: '85vh' }">
      <div v-if="exchangeItem" class="sheet">
        <div class="sheet-title">{{ exchangeItem.name }}</div>
        <img v-if="exchangeItem.image" :src="resolveImageUrl(exchangeItem.image)" class="sheet-img" alt="" />
        <div v-if="exchangeItem.ends_in_seconds" class="sheet-row countdown">
          {{ formatEndsIn(exchangeItem.ends_in_seconds) }}
        </div>
        <div class="sheet-row">{{ t('pointsMall.needPoints', { count: exchangeItem.points_required * quantity }) }}</div>
        <div class="sheet-row">{{ t('pointsMall.stock', { count: exchangeItem.stock }) }}</div>
        <div class="sheet-row">{{ t('pointsMall.limit', { count: exchangeItem.per_user_limit }) }}</div>
        <p class="desc">{{ exchangeItem.description }}</p>
        <div class="qty-row">
          <span>{{ t('pointsMall.quantity') }}</span>
          <van-stepper v-model="quantity" :min="1" :max="Math.min(exchangeItem.stock, exchangeItem.per_user_limit)" />
        </div>
        <div v-if="exchangeItem.requires_address" class="address-block">
          <div class="sheet-row">{{ t('pointsMall.selectAddress') }}</div>
          <van-radio-group v-model="selectedAddressId">
            <van-cell-group inset>
              <van-cell
                v-for="addr in addresses"
                :key="addr.id"
                clickable
                @click="selectedAddressId = addr.id"
              >
                <template #title>{{ addr.name }} {{ addr.phone }}</template>
                <template #label>{{ addr.province }}{{ addr.city }}{{ addr.district }}{{ addr.detail }}</template>
                <template #right-icon><van-radio :name="addr.id" /></template>
              </van-cell>
            </van-cell-group>
          </van-radio-group>
        </div>
        <van-button type="primary" block round :loading="submitting" @click="submitExchange">
          {{ t('pointsMall.confirmExchange') }}
        </van-button>
      </div>
    </van-popup>
  </div>
</template>

<style scoped>
.points-mall-page { min-height: 100vh; background: #f7f8fa; padding-bottom: 24px; }
.balance-bar { margin: 12px; padding: 14px 16px; background: linear-gradient(135deg, #ff6034, #ee0a24); color: #fff; border-radius: 12px; font-size: 15px; }
.yuan { margin-left: 8px; opacity: 0.9; font-size: 13px; }
.quick-nav { display: flex; gap: 10px; margin: 0 12px 8px; }
.nav-item { flex: 1; background: #fff; border: none; border-radius: 10px; padding: 12px 8px; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.category-row { display: flex; gap: 8px; overflow-x: auto; padding: 8px 12px 0; -webkit-overflow-scrolling: touch; }
.category-chip { flex-shrink: 0; border: 1px solid #ebedf0; background: #fff; color: #646566; border-radius: 999px; padding: 4px 12px; font-size: 12px; }
.category-chip.active { border-color: #ee0a24; color: #ee0a24; background: #fff1f0; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; padding: 12px; }
.card { background: #fff; border-radius: 10px; overflow: hidden; padding-bottom: 10px; }
.img-wrap { position: relative; aspect-ratio: 1; background: #f2f3f5; }
.img-wrap img { width: 100%; height: 100%; object-fit: cover; }
.img-fallback { display: flex; align-items: center; justify-content: center; height: 100%; font-size: 28px; color: #969799; }
.tag { position: absolute; top: 8px; left: 8px; }
.tag-new { left: auto; right: 8px; }
.name { padding: 8px 10px 0; font-size: 14px; font-weight: 600; }
.points { padding: 4px 10px 0; color: #ee0a24; font-size: 13px; }
.countdown { padding: 2px 10px 0; color: #ff6034; font-size: 12px; }
.meta { padding: 2px 10px 0; color: #969799; font-size: 12px; }
.page-loading { display: flex; justify-content: center; padding: 40px 0; }
.sheet { padding: 16px; }
.sheet-title { font-size: 18px; font-weight: 700; margin-bottom: 10px; }
.sheet-img { width: 100%; max-height: 180px; object-fit: contain; border-radius: 8px; background: #f7f8fa; }
.sheet-row { margin-top: 8px; font-size: 14px; color: #323233; }
.desc { margin: 10px 0; font-size: 13px; color: #646566; line-height: 1.5; }
.qty-row { display: flex; align-items: center; justify-content: space-between; margin: 14px 0; }
.address-block { margin-bottom: 12px; }
</style>
