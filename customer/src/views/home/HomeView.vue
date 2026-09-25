<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useMediaQuery } from '@vueuse/core'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getBanners } from '@/api/product'
import HomeMobileHeader from '@/components/home/HomeMobileHeader.vue'
import HomeHeroGrid from '@/components/home/HomeHeroGrid.vue'
import HomePromoStrip from '@/components/home/HomePromoStrip.vue'
import HomeCategoryGrid from '@/components/home/HomeCategoryGrid.vue'
import HomeSeckillSection from '@/components/home/HomeSeckillSection.vue'
import HomeSubsidyPanel from '@/components/home/HomeSubsidyPanel.vue'
import HomeBillionSubsidyPanel from '@/components/home/HomeBillionSubsidyPanel.vue'
import HomeSuperDiscountPanel from '@/components/home/HomeSuperDiscountPanel.vue'
import HomeSeckillChannelPanel from '@/components/home/HomeSeckillChannelPanel.vue'
import HomeNewProductsPanel from '@/components/home/HomeNewProductsPanel.vue'
import FeaturedShops from '@/components/shop/FeaturedShops.vue'
import ProductListSection from '@/components/product/ProductListSection.vue'
import { useProductList } from '@/composables/useProductList'
import { useChannelSwipe } from '@/composables/useChannelSwipe'
import { HOME_SWIPE_CHANNELS, homeChannelIndex } from '@/constants/homeChannels'
import { resolveImageUrl } from '@/utils/product'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()

const banners = ref([])
const bannerLoading = ref(true)
const activeChannel = ref('recommend')

const BANNER_COLORS = ['#e4393c', '#6366f1', '#0ea5e9', '#8b5cf6']

const defaultBanners = computed(() => [
  { id: 'b1', title: t('home.defaultBanners.b1Title'), content: t('home.defaultBanners.b1Content') },
  { id: 'b2', title: t('home.defaultBanners.b2Title'), content: t('home.defaultBanners.b2Content') },
  { id: 'b3', title: t('home.defaultBanners.b3Title'), content: t('home.defaultBanners.b3Content') },
])

const {
  products,
  loading,
  loadingMore,
  finished,
  error,
  load,
  loadMore,
  retry,
} = useProductList()

const isWide = useMediaQuery('(min-width: 992px)')
const swipeChannels = HOME_SWIPE_CHANNELS
const activeChannelIndex = computed(() => homeChannelIndex(activeChannel.value))

const channelTrackStyle = computed(() => ({
  transform: `translate3d(-${activeChannelIndex.value * 100}%, 0, 0)`,
}))

function bannerStyle(index) {
  const color = BANNER_COLORS[index % BANNER_COLORS.length]
  return { background: `linear-gradient(135deg, ${color} 0%, #1e293b 100%)` }
}

function goProduct(product) {
  router.push({ name: 'ProductDetail', params: { id: product.id } })
}

function onBannerClick(banner) {
  if (banner.link) {
    router.push(banner.link)
  }
}

async function fetchBanners() {
  bannerLoading.value = true
  try {
    const res = await getBanners()
    const list = Array.isArray(res.data) ? res.data : []
    banners.value = list.length ? list : defaultBanners.value
  } catch {
    banners.value = defaultBanners.value
  } finally {
    bannerLoading.value = false
  }
}

onMounted(async () => {
  applyRouteChannel()
  await Promise.all([fetchBanners(), load(true)])
})

function goSubsidyPage() {
  router.push({ name: 'Subsidy' })
}

function switchToSubsidyChannel() {
  if (isWide.value) {
    goSubsidyPage()
    return
  }
  activeChannel.value = 'subsidy'
  scrollToTop()
}

function switchToBillionSubsidyChannel() {
  if (isWide.value) {
    router.push({ name: 'BillionSubsidyChannel' })
    return
  }
  activeChannel.value = 'billionSubsidy'
  scrollToTop()
}

function switchToSuperDiscountChannel() {
  if (isWide.value) {
    router.push({ name: 'SuperDiscountChannel' })
    return
  }
  activeChannel.value = 'superDiscount'
  scrollToTop()
}

function switchToSeckillChannel() {
  if (isWide.value) {
    router.push({ name: 'SeckillChannel' })
    return
  }
  activeChannel.value = 'seckill'
  scrollToTop()
}

function scrollToTop() {
  const main = document.querySelector('.main-content--mobile-tab')
  if (main) {
    main.scrollTo({ top: 0, behavior: 'smooth' })
  } else {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

function handleChannelSelect(key) {
  activeChannel.value = key
  if (route.name === 'Home') {
    const nextQuery = key === 'recommend' ? {} : { channel: key }
    if ((route.query.channel || '') !== (nextQuery.channel || '')) {
      router.replace({ name: 'Home', query: nextQuery })
    }
  }
  scrollToTop()
}

function applyRouteChannel() {
  const channel = route.query.channel
  if (typeof channel === 'string' && homeChannelIndex(channel) >= 0) {
    activeChannel.value = channel
  }
}

watch(
  () => route.query.channel,
  () => {
    applyRouteChannel()
    scrollToTop()
  },
)

const showPcNewArrival = computed(() => route.query.channel === 'newArrival')

const { onTouchStart, onTouchEnd, onTouchCancel } = useChannelSwipe({
  channels: swipeChannels,
  activeChannel,
  onChange(key) {
    handleChannelSelect(key)
  },
})
</script>

<template>
  <div class="home-page" :class="{ 'home-page--mobile-channel': !isWide }">
    <HomeMobileHeader
      v-if="!isWide"
      v-model:active-channel="activeChannel"
      @select-channel="handleChannelSelect"
    />

    <div class="home-container">
      <template v-if="isWide">
        <HomeHeroGrid
          :banners="banners"
          :banner-loading="bannerLoading"
          :products="products"
          @banner-click="onBannerClick"
          @expand-subsidy="goSubsidyPage"
        />

        <FeaturedShops />

        <HomeNewProductsPanel v-if="showPcNewArrival" />

        <section v-else class="recommend-section pc-recommend">
          <div class="section-tabs">
            <span class="tab active">{{ t('home.tabRecommend') }}</span>
            <span class="tab">{{ t('home.tabHot') }}</span>
            <span class="tab">{{ t('home.tabNew') }}</span>
          </div>

          <ProductListSection
            :products="products"
            :loading="loading"
            :loading-more="loadingMore"
            :finished="finished"
            :error="error"
            :columns="6"
            compact
            show-shop-name
            @load-more="loadMore"
            @retry="retry"
            @select="goProduct"
          />
        </section>
      </template>

      <template v-else>
        <div
          class="mobile-channel-stage"
          @touchstart.passive="onTouchStart"
          @touchend="onTouchEnd"
          @touchcancel="onTouchCancel"
        >
          <div class="mobile-channel-track" :style="channelTrackStyle">
            <section
              v-for="tab in swipeChannels"
              :key="tab.key"
              class="mobile-channel-pane"
              :aria-hidden="activeChannel !== tab.key"
            >
              <template v-if="tab.key === 'recommend'">
                <section class="banner-section mobile-banner">
                  <van-swipe
                    v-if="!bannerLoading && banners.length"
                    class="banner-swipe"
                    indicator-color="#fff"
                    :autoplay="3000"
                  >
                    <van-swipe-item v-for="(banner, index) in banners" :key="banner.id">
                      <div
                        class="banner-slide"
                        :style="banner.image ? {} : bannerStyle(index)"
                        @click="onBannerClick(banner)"
                      >
                        <img
                          v-if="banner.image"
                          :src="resolveImageUrl(banner.image)"
                          class="banner-image"
                          alt=""
                        />
                        <div v-else class="banner-text">
                          <div class="banner-title">{{ banner.title }}</div>
                          <div v-if="banner.content" class="banner-desc">{{ banner.content }}</div>
                        </div>
                      </div>
                    </van-swipe-item>
                  </van-swipe>
                  <van-skeleton v-else class="banner-skeleton" :row="0" title />
                </section>

                <HomeCategoryGrid />
                <HomeSeckillSection />
                <HomePromoStrip
                  @open-billion="switchToBillionSubsidyChannel"
                  @open-super="switchToSuperDiscountChannel"
                  @open-seckill="switchToSeckillChannel"
                />

                <section class="recommend-section mobile-recommend">
                  <div class="section-title">{{ t('home.tabRecommend') }}</div>
                  <ProductListSection
                    :products="products"
                    :loading="loading"
                    :loading-more="loadingMore"
                    :finished="finished"
                    :error="error"
                    :columns="2"
                    compact
                    show-sales
                    show-shop-name
                    @load-more="loadMore"
                    @retry="retry"
                    @select="goProduct"
                  />
                </section>
              </template>

              <template v-else-if="tab.key === 'billionSubsidy'">
                <HomeBillionSubsidyPanel />
              </template>

              <template v-else-if="tab.key === 'superDiscount'">
                <HomeSuperDiscountPanel />
              </template>

              <template v-else-if="tab.key === 'seckill'">
                <HomeSeckillChannelPanel />
              </template>

              <template v-else-if="tab.key === 'subsidy'">
                <HomeSubsidyPanel embedded />
              </template>

              <template v-else-if="tab.key === 'newArrival'">
                <HomeNewProductsPanel v-if="activeChannel === 'newArrival'" />
              </template>

              <template v-else-if="['liveStream', 'freeShipping'].includes(tab.key)">
                <div class="channel-placeholder">
                  <van-icon name="smile-o" size="48" color="#dcdee0" />
                  <p>{{ t(`home.${tab.key}`) }}</p>
                  <p class="channel-placeholder__sub">{{ t('home.channelDeveloping') }}</p>
                </div>
              </template>

              <template v-else>
                <div class="channel-placeholder">
                  <van-icon name="smile-o" size="48" color="#dcdee0" />
                  <p>{{ t('home.channelDeveloping') }}</p>
                </div>
              </template>
            </section>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.home-page {
  background: #f5f5f5;
}

.home-page--mobile-channel {
  min-height: auto;
}

.home-container {
  max-width: 1190px;
  margin: 0 auto;
  padding: 8px 8px 24px;
}

.mobile-channel-stage {
  overflow: hidden;
  width: 100%;
  touch-action: pan-y;
}

.mobile-channel-track {
  display: flex;
  width: 100%;
  transition: transform 0.38s cubic-bezier(0.32, 0.72, 0, 1);
  will-change: transform;
}

.mobile-channel-pane {
  flex: 0 0 100%;
  width: 100%;
  min-width: 100%;
}

.channel-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin: 24px 8px;
  padding: 32px 16px;
  background: #fff;
  border-radius: 12px;
  color: #969799;
  font-size: 14px;
}

.channel-placeholder p {
  margin: 0;
}

.channel-placeholder__sub {
  font-size: 12px;
  color: #c8c9cc;
}

.mobile-banner {
  margin: 8px 4px 0;
}

.banner-swipe,
.banner-skeleton {
  border-radius: 10px;
  overflow: hidden;
}

.banner-slide {
  height: 120px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.banner-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.banner-text {
  height: 100%;
  padding: 14px 16px;
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: center;
  box-sizing: border-box;
}

.banner-title {
  font-size: 16px;
  font-weight: 700;
}

.banner-desc {
  margin-top: 4px;
  font-size: 12px;
  opacity: 0.92;
}

.pc-recommend {
  margin-top: 10px;
  background: #fff;
  border-radius: 10px;
  padding: 16px;
}

.mobile-recommend {
  margin: 12px 4px 0;
  padding: 14px 10px 16px;
  background: #fff;
  border-radius: 12px;
}

.section-tabs {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.tab {
  font-size: 16px;
  color: #666;
  cursor: default;
}

.tab.active {
  color: #e1251b;
  font-weight: 700;
  position: relative;
}

.tab.active::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -13px;
  height: 2px;
  background: #e1251b;
}

.section-title {
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 700;
  color: #333;
}

@media (max-width: 768px) {
  .pc-recommend :deep(.product-list) {
    --cols: 3 !important;
  }
}

@media (max-width: 480px) {
  .pc-recommend :deep(.product-list) {
    --cols: 2 !important;
  }
}
</style>
