<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import SubsidyTag from '@shared/components/SubsidyTag.vue'
import { getSeckillActivities } from '@/api/promotion'
import { getSubsidyProducts } from '@/api/subsidy'
import { formatPrice, resolveImageUrl } from '@/utils/product'

const props = defineProps({
  banners: {
    type: Array,
    default: () => [],
  },
  bannerLoading: Boolean,
  products: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['banner-click', 'expand-subsidy'])

const router = useRouter()
const { t } = useI18n()

const subsidyProducts = ref([])
const subsidyLoading = ref(true)
const seckillActivities = ref([])
const seckillLoading = ref(true)

const BANNER_COLORS = ['#3b82f6', '#6366f1', '#0ea5e9', '#8b5cf6']

const newItems = computed(() => props.products.slice(0, 2))
const seckillItems = computed(() => {
  const act = seckillActivities.value.find((item) => item.phase === 'ongoing') || seckillActivities.value[0]
  if (!act?.product) return []
  return [{
    id: act.product.id,
    name: act.product.name,
    price: act.seckill_price,
    image: act.product.image,
    activity_id: act.id,
  }]
})
const cheapItems = computed(() => props.products.slice(4, 6))
const subsidyItems = computed(() => subsidyProducts.value.slice(0, 4))
const seckillTag = computed(() => {
  const act = seckillActivities.value.find((item) => item.phase === 'ongoing') || seckillActivities.value[0]
  return act?.name || t('home.flashSaleTag')
})

const liveItems = computed(() => [
  { id: 'live-1', label: t('home.liveTag1'), color: '#ffe8e8' },
  { id: 'live-2', label: t('home.liveTag2'), color: '#e8f4ff' },
])

function bannerStyle(index) {
  const color = BANNER_COLORS[index % BANNER_COLORS.length]
  return { background: `linear-gradient(135deg, ${color} 0%, #1e3a8a 100%)` }
}

function seckillPrice(price) {
  return formatPrice(price)
}

async function fetchSeckillActivities() {
  seckillLoading.value = true
  try {
    const res = await getSeckillActivities()
    seckillActivities.value = res.data || []
  } catch {
    seckillActivities.value = []
  } finally {
    seckillLoading.value = false
  }
}

async function fetchSubsidyProducts() {
  subsidyLoading.value = true
  try {
    const res = await getSubsidyProducts({ page: 1, page_size: 8 })
    subsidyProducts.value = res.data?.results || []
  } catch {
    subsidyProducts.value = []
  } finally {
    subsidyLoading.value = false
  }
}

function goSubsidyZone() {
  router.push({ name: 'Subsidy' })
}

function goSeckillZone() {
  const act = seckillActivities.value.find((item) => item.phase === 'ongoing') || seckillActivities.value[0]
  if (act?.id) {
    router.push({ name: 'Seckill', query: { activity_id: act.id } })
    return
  }
  router.push({ name: 'Seckill' })
}

function goChannel(nameOrChannel) {
  if (nameOrChannel === 'NewProducts' || nameOrChannel === 'newArrival') {
    router.push({ name: 'Home', query: { channel: 'newArrival' } })
    return
  }
  router.push({ name: nameOrChannel })
}

function goSubsidyProduct(item, event) {
  event?.stopPropagation?.()
  router.push({ name: 'ProductDetail', params: { id: item.product_id } })
}

onMounted(() => {
  fetchSubsidyProducts()
  fetchSeckillActivities()
})
</script>

<template>
  <section class="hero-grid">
    <div class="hero-top">
      <div class="hero-banner">
        <van-swipe
          v-if="!bannerLoading && banners.length"
          class="banner-swipe"
          indicator-color="#fff"
          :autoplay="4000"
        >
          <van-swipe-item v-for="(banner, index) in banners" :key="banner.id">
            <div
              class="banner-slide"
              :style="bannerStyle(index)"
              @click="emit('banner-click', banner)"
            >
              <div class="banner-title">{{ banner.title }}</div>
              <div v-if="banner.content" class="banner-desc">{{ banner.content }}</div>
            </div>
          </van-swipe-item>
        </van-swipe>
        <van-skeleton v-else class="banner-skeleton" :row="0" title />
      </div>

      <div
        class="hero-subsidy card-box clickable"
        @click="goSubsidyZone"
      >
        <div class="card-head">
          <div class="card-title">
            {{ t('home.nationalSubsidy') }}
            <span class="card-badge">{{ t('home.superSubsidy') }}</span>
          </div>
          <span class="card-tag">{{ t('home.limitedSubsidy') }}</span>
        </div>
        <div v-if="subsidyItems.length" class="mini-product-row">
          <div
            v-for="item in subsidyItems"
            :key="item.id"
            class="mini-product"
            @click="goSubsidyProduct(item, $event)"
          >
            <div class="mini-image-wrap">
              <van-image
                class="mini-image"
                :src="resolveImageUrl(item.image)"
                fit="cover"
                lazy-load
              />
              <SubsidyTag class="mini-tag" />
            </div>
            <div class="mini-price">{{ formatPrice(item.final_price) }}</div>
            <div class="mini-sub">{{ t('subsidy.subsidyOff', { amount: item.subsidy_amount }) }}</div>
          </div>
        </div>
        <van-skeleton v-else-if="subsidyLoading" :row="2" title />
        <div v-else class="subsidy-empty">{{ t('subsidy.emptyProducts') }}</div>
      </div>
    </div>

    <div class="hero-cards">
      <div class="feature-card card-box clickable" @click="goChannel('newArrival')">
        <div class="card-head compact">
          <span class="card-title">{{ t('home.newArrival') }}</span>
          <span class="card-tag orange">{{ t('home.newArrivalTag') }}</span>
        </div>
        <div class="feature-body split">
          <div class="feature-text">
            <span class="feature-badge">{{ t('home.bigBrandNew') }}</span>
            <ul class="feature-list">
              <li>{{ t('home.newHeavy') }}</li>
              <li>{{ t('home.newTrend') }}</li>
            </ul>
          </div>
          <div v-if="newItems[0]" class="feature-product">
            <van-image
              class="feature-image"
              :src="resolveImageUrl(newItems[0].image)"
              fit="cover"
              lazy-load
            />
            <div class="feature-price">{{ formatPrice(newItems[0].price) }}</div>
          </div>
        </div>
      </div>

      <div class="feature-card card-box clickable" @click="goChannel('LiveChannel')">
        <div class="card-head compact">
          <span class="card-title">{{ t('home.liveStream') }}</span>
          <span class="card-tag orange">{{ t('home.liveStreamTag') }}</span>
        </div>
        <div class="feature-body live-row">
          <div v-for="item in liveItems" :key="item.id" class="live-item">
            <div class="live-thumb" :style="{ background: item.color }">
              <span class="live-dot" />
            </div>
            <div class="live-label">{{ item.label }}</div>
          </div>
        </div>
      </div>

      <div class="feature-card card-box clickable" @click="goSeckillZone">
        <div class="card-head compact">
          <span class="card-title">{{ t('home.flashSale') }}</span>
          <span class="card-tag orange">{{ seckillTag }}</span>
        </div>
        <div class="feature-body duo-row">
          <div
            v-for="item in seckillItems"
            :key="item.id"
            class="duo-product"
          >
            <van-image
              class="duo-image"
              :src="resolveImageUrl(item.image)"
              fit="cover"
              lazy-load
            />
            <div class="duo-price">
              {{ seckillPrice(item.price) }}
              <span>{{ t('home.seckillPrice') }}</span>
            </div>
          </div>
          <van-skeleton v-if="seckillLoading || !seckillItems.length" :row="1" title />
        </div>
      </div>

      <div class="feature-card card-box clickable" @click="goChannel('FreeShippingChannel')">
        <div class="card-head compact">
          <span class="card-title">{{ t('home.freeShipping') }}</span>
          <span class="card-tag orange">{{ t('home.freeShippingTag') }}</span>
        </div>
        <div class="feature-body duo-row">
          <div
            v-for="item in cheapItems"
            :key="item.id"
            class="duo-product"
          >
            <van-image
              class="duo-image"
              :src="resolveImageUrl(item.image)"
              fit="cover"
              lazy-load
            />
            <div class="duo-price plain">{{ formatPrice(item.price) }}</div>
          </div>
          <van-skeleton v-if="!cheapItems.length" :row="1" title />
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hero-top {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  min-height: 0;
}

.card-box {
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
}

.clickable {
  cursor: pointer;
  transition: box-shadow 0.2s;
}

.clickable:active {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.hero-banner,
.banner-swipe,
.banner-skeleton {
  height: 100%;
  min-height: 168px;
  border-radius: 10px;
  overflow: hidden;
}

.banner-slide {
  height: 168px;
  padding: 16px;
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: center;
  cursor: pointer;
  box-sizing: border-box;
}

.banner-title {
  font-size: clamp(16px, 4vw, 22px);
  font-weight: 700;
  line-height: 1.3;
}

.banner-desc {
  margin-top: 6px;
  font-size: 12px;
  opacity: 0.92;
}

.hero-subsidy {
  padding: 10px;
  min-height: 168px;
  box-sizing: border-box;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 8px;
}

.card-head.compact {
  margin-bottom: 10px;
}

.card-title {
  font-size: 15px;
  font-weight: 700;
  color: #1a1a1a;
  white-space: nowrap;
}

.card-badge {
  margin-left: 4px;
  font-size: 13px;
  color: #16a34a;
  font-weight: 700;
}

.card-tag {
  font-size: 11px;
  color: #999;
  white-space: nowrap;
}

.card-tag.orange {
  color: #ea580c;
}

.mini-product-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 6px;
}

.mini-product {
  min-width: 0;
}

.mini-image-wrap {
  position: relative;
}

.mini-image {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 6px;
  overflow: hidden;
  background: #f0f2f5;
}

.mini-tag {
  position: absolute;
  left: 2px;
  top: 2px;
  transform: scale(0.75);
  transform-origin: left top;
}

.mini-image :deep(img),
.mini-image :deep(.van-image__img) {
  object-fit: cover;
}

.mini-price {
  margin-top: 4px;
  font-size: 13px;
  font-weight: 700;
  color: #e1251b;
  text-align: center;
}

.mini-sub {
  font-size: 10px;
  color: #07c160;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.subsidy-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 96px;
  font-size: 12px;
  color: #969799;
}

.hero-cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.feature-card {
  padding: 10px;
  min-height: 130px;
  box-sizing: border-box;
}

.feature-body.split {
  display: grid;
  grid-template-columns: 1fr 72px;
  gap: 6px;
  align-items: center;
}

.feature-badge {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  background: #fee2e2;
  color: #dc2626;
  font-size: 11px;
  font-weight: 600;
}

.feature-list {
  margin: 8px 0 0;
  padding-left: 14px;
  font-size: 11px;
  color: #666;
  line-height: 1.5;
}

.feature-product {
  pointer-events: none;
}

.feature-image {
  width: 72px;
  height: 72px;
  border-radius: 6px;
  overflow: hidden;
  background: #f0f2f5;
}

.feature-price {
  margin-top: 4px;
  font-size: 13px;
  font-weight: 700;
  color: #e1251b;
  text-align: center;
}

.live-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.live-thumb {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.live-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(225, 37, 27, 0.15);
  border: 2px solid #e1251b;
}

.live-label {
  margin-top: 6px;
  font-size: 11px;
  color: #666;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.duo-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.duo-product {
  min-width: 0;
  pointer-events: none;
}

.duo-image {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 6px;
  overflow: hidden;
  background: #f0f2f5;
}

.duo-price {
  margin-top: 4px;
  font-size: 12px;
  font-weight: 700;
  color: #e1251b;
  text-align: center;
  line-height: 1.3;
}

.duo-price span {
  display: block;
  font-size: 10px;
  font-weight: 500;
}

.duo-price.plain span {
  display: none;
}

@media (max-width: 768px) {
  .hero-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .mini-product-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .hero-top {
    grid-template-columns: 1fr;
  }

  .banner-slide,
  .hero-banner,
  .banner-swipe,
  .banner-skeleton,
  .hero-subsidy {
    min-height: 140px;
  }

  .banner-slide {
    height: 140px;
  }
}

@media (max-width: 374px) {
  .card-title {
    font-size: 14px;
  }

  .feature-body.split {
    grid-template-columns: 1fr 64px;
  }

  .feature-image {
    width: 64px;
    height: 64px;
  }
}
</style>
