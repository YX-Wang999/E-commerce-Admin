<script setup>
import { computed, onMounted, ref } from 'vue'
import { useMediaQuery } from '@vueuse/core'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showToast } from 'vant'
import SubsidyTag from '@shared/components/SubsidyTag.vue'
import ProductGallery from '@/components/product/ProductGallery.vue'
import ProductReviewSection from '@/components/review/ProductReviewSection.vue'
import ProductListSection from '@/components/product/ProductListSection.vue'
import ProductPromoTags from '@/components/product/ProductPromoTags.vue'
import { getAddresses } from '@/api/address'
import { getProduct, getProducts, getProductsByCategory } from '@/api/product'
import { calculateSubsidy, getSubsidyEligibility } from '@/api/subsidy'
import { getGroupBuyActivities, groupBuyJoin } from '@/api/promotion'
import { useCartStore } from '@/stores/cart'
import { requireLogin } from '@/stores/loginGate'
import { formatPrice, resolveProductImages, resolveImageUrl } from '@/utils/product'
import { pushRecentProduct } from '@/utils/recentBrowse'
import { toastError } from '@/utils/feedback'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const cartStore = useCartStore()
const loading = ref(true)
const error = ref(false)
const product = ref(null)
const quantity = ref(1)
const adding = ref(false)
const buying = ref(false)
const groupBuyActivity = ref(null)
const subsidyInfo = ref(null)
const subsidyEligibility = ref(null)
const showPolicy = ref(false)
const joiningGroup = ref(false)
const showAddressPicker = ref(false)
const addresses = ref([])
const pendingGroupOrderId = ref(null)
const relatedProducts = ref([])
const relatedLoading = ref(false)
const relatedLoadingMore = ref(false)
const relatedFinished = ref(false)
const relatedPage = ref(1)

const isDesktop = useMediaQuery('(min-width: 769px)')
const recommendColumns = computed(() => (isDesktop.value ? 4 : 2))
const recommendTitle = computed(() =>
  isDesktop.value ? t('product.moreRecommend') : t('product.relatedRecommend'),
)

const productImages = computed(() => resolveProductImages(product.value))

const groupBuyProgress = computed(() => {
  if (!groupBuyActivity.value) return 0
  return groupBuyActivity.value.progress_percent || 0
})

const groupBuyNeedMore = computed(() => {
  if (!groupBuyActivity.value) return 0
  return groupBuyActivity.value.need_more || 0
})

const ratingScore = computed(() => product.value?.tenant?.rating ?? '5.0')
const ratingCount = computed(() => product.value?.tenant?.rating_count ?? 0)

const soldCount = computed(() => product.value?.tenant?.sold_count ?? null)

const earnPointsHint = computed(() => {
  if (!product.value) return ''
  const price = Number(subsidyInfo.value?.final_price ?? product.value.price ?? 0)
  if (!price) return ''
  const points = Math.min(Math.floor(price * 0.1), 500)
  if (points <= 0) return ''
  const yuan = (points / 10).toFixed(2)
  return t('product.earnPointsHint', { points, yuan })
})

const shopClosureState = computed(() => product.value?.tenant?.closure_state || 'active')
const shopClosed = computed(() => shopClosureState.value === 'closed' || product.value?.tenant?.status === 'closed')
const shopClosing = computed(() => shopClosureState.value === 'closing')
const shopPurchaseBlocked = computed(() => shopClosed.value || shopClosing.value)

const closureNoticeText = computed(() => {
  if (shopClosed.value) return t('shop.closedBanner')
  if (shopClosing.value) {
    const endAt = product.value?.tenant?.closure_notice_end_at
    return endAt ? t('shop.closingBanner', { date: String(endAt).slice(0, 10) }) : t('shop.closingBannerSoon')
  }
  return ''
})

const specOptions = computed(() => {
  const options = []
  if (product.value?.category_name) {
    options.push({ key: 'category', label: product.value.category_name })
  }
  if (product.value?.brand_name) {
    options.push({ key: 'brand', label: product.value.brand_name })
  }
  return options
})

function clampQuantity() {
  const max = Math.max(1, Number(product.value?.stock) || 1)
  quantity.value = Math.min(Math.max(1, quantity.value), max)
}

async function handleAddToCart() {
  if (!product.value) return
  if (shopPurchaseBlocked.value) {
    toastError(closureNoticeText.value || t('shop.closedBanner'))
    return
  }
  clampQuantity()
  adding.value = true
  try {
    await cartStore.addItem(product.value.id, quantity.value, product.value)
    showToast(t('product.addToCartHint'))
  } finally {
    adding.value = false
  }
}

async function handleBuyNow() {
  if (!product.value) return
  if (shopPurchaseBlocked.value) {
    toastError(closureNoticeText.value || t('shop.closedBanner'))
    return
  }
  clampQuantity()
  buying.value = true
  try {
    await requireLogin({ redirect: '/checkout' })
    await cartStore.addItem(product.value.id, quantity.value, product.value)
    router.push({ name: 'Checkout' })
  } catch {
    // cancelled login
  } finally {
    buying.value = false
  }
}

async function handleContactShop() {
  const tenantId = product.value?.tenant?.id ?? product.value?.tenant
  if (!tenantId) {
    showToast(t('product.platformProductNoShop'))
    return
  }
  try {
    await requireLogin({ redirect: route.fullPath })
    router.push({ name: 'Chat', query: { tenant_id: String(tenantId) } })
  } catch {
    // cancelled
  }
}

async function handleComplainShop() {
  const tenantId = product.value?.tenant?.id ?? product.value?.tenant
  if (!tenantId) {
    showToast(t('product.platformProductNoShop'))
    return
  }
  try {
    await requireLogin({ redirect: route.fullPath })
    router.push({
      name: 'Chat',
      query: { tenant_id: String(tenantId), action: 'complaint' },
    })
  } catch {
    // cancelled
  }
}

function goShopHome() {
  const tenantId = product.value?.tenant?.id ?? product.value?.tenant
  if (tenantId) {
    router.push({ name: 'ShopHome', params: { id: tenantId } })
  }
}

const shopName = computed(() =>
  product.value?.tenant?.name || product.value?.tenant_name || t('product.shopFallback'),
)

const shopFollowers = computed(() => product.value?.tenant?.follower_count ?? 0)

async function fetchRelatedProducts(reset = true) {
  if (reset) {
    relatedPage.value = 1
    relatedFinished.value = false
    relatedProducts.value = []
  }
  if (relatedFinished.value && !reset) return

  const loadingRef = reset ? relatedLoading : relatedLoadingMore
  loadingRef.value = true
  try {
    const rawCategory = product.value?.category
    const categoryId = typeof rawCategory === 'object' ? rawCategory?.id : rawCategory
    const params = {
      page: relatedPage.value,
      page_size: isDesktop.value ? 12 : 8,
      status: 'on_sale',
    }
    const res = categoryId
      ? await getProductsByCategory(categoryId, params)
      : await getProducts(params)
    const list = (res.data?.results || res.data || []).filter(
      (item) => item.id !== product.value?.id,
    )
    if (reset) {
      relatedProducts.value = list
    } else {
      const seen = new Set(relatedProducts.value.map((item) => item.id))
      relatedProducts.value.push(...list.filter((item) => !seen.has(item.id)))
    }
    const total = res.data?.count
    if (total != null) {
      relatedFinished.value = relatedProducts.value.length >= total - 1 || list.length === 0
    } else {
      relatedFinished.value = list.length < params.page_size
    }
    if (!relatedFinished.value) {
      relatedPage.value += 1
    }
  } catch {
    if (reset) relatedProducts.value = []
    relatedFinished.value = true
  } finally {
    loadingRef.value = false
  }
}

function loadMoreRelated() {
  if (relatedLoading.value || relatedLoadingMore.value || relatedFinished.value) return
  fetchRelatedProducts(false)
}

function goRelatedProduct(item) {
  router.push({ name: 'ProductDetail', params: { id: item.id } })
}

async function fetchGroupBuy() {
  try {
    const res = await getGroupBuyActivities({ product_id: route.params.id })
    groupBuyActivity.value = (res.data || [])[0] || null
  } catch {
    groupBuyActivity.value = null
  }
}

async function ensureAddresses() {
  const res = await getAddresses()
  addresses.value = res.data || []
  return addresses.value
}

async function handleJoinGroup(groupOrderId = null) {
  if (!groupBuyActivity.value) return

  try {
    await requireLogin({ redirect: route.fullPath })
  } catch {
    return
  }

  pendingGroupOrderId.value = groupOrderId
  const list = await ensureAddresses()
  if (!list.length) {
    showToast(t('checkout.addAddressFirst'))
    router.push({ name: 'AddressManage', query: { redirect: route.fullPath } })
    return
  }
  if (list.length === 1) {
    await submitGroupBuy(list[0].id)
    return
  }
  showAddressPicker.value = true
}

async function submitGroupBuy(addressId) {
  if (!groupBuyActivity.value) return

  joiningGroup.value = true
  showAddressPicker.value = false
  try {
    const payload = {
      address_id: addressId,
      quantity: quantity.value,
    }
    if (pendingGroupOrderId.value) {
      payload.group_order_id = pendingGroupOrderId.value
    }
    const res = await groupBuyJoin(groupBuyActivity.value.id, payload)
    showToast(t('groupbuy.joinSuccess'))
    router.push({ name: 'OrderDetail', params: { id: res.data.id } })
  } catch {
    // handled
  } finally {
    joiningGroup.value = false
    pendingGroupOrderId.value = null
  }
}

async function fetchSubsidy() {
  try {
    const [calcRes, eligRes] = await Promise.all([
      calculateSubsidy({ product_id: route.params.id, quantity: quantity.value }),
      getSubsidyEligibility({ product_id: route.params.id }),
    ])
    subsidyEligibility.value = eligRes.data || null
    subsidyInfo.value = calcRes.data?.is_subsidy ? calcRes.data : null
  } catch {
    subsidyInfo.value = null
    subsidyEligibility.value = null
  }
}

async function fetchDetail() {
  loading.value = true
  error.value = false
  try {
    const res = await getProduct(route.params.id)
    product.value = res.data
    pushRecentProduct(res.data)
    quantity.value = 1
    await Promise.all([fetchGroupBuy(), fetchSubsidy(), fetchRelatedProducts()])
  } catch {
    error.value = true
    toastError(t('product.loadFailed'))
  } finally {
    loading.value = false
  }
}

onMounted(fetchDetail)
</script>

<template>
  <div class="detail-page">
    <van-nav-bar
      :title="t('product.detailTitle')"
      left-arrow
      fixed
      placeholder
      @click-left="router.back()"
    />

    <div v-if="loading" class="detail-skeleton">
      <div class="product-detail">
        <div class="product-detail__gallery">
          <van-skeleton-image class="gallery-skeleton" />
        </div>
        <div class="product-detail__info">
          <van-skeleton title :row="5" />
        </div>
      </div>
    </div>

    <div v-else-if="error" class="state-box">
      <p>{{ t('common.loadFailed') }}</p>
      <van-button size="small" type="primary" plain @click="fetchDetail">
        {{ t('common.clickRetry') }}
      </van-button>
    </div>

    <template v-else-if="product">
      <div class="product-detail">
        <div class="product-detail__gallery">
          <ProductGallery :images="productImages" :product-name="product.name" />
        </div>

        <div class="product-detail__info">
          <div class="info-card">
            <h1 class="product-title">{{ product.name }}</h1>

            <div class="product-meta">
              <span class="meta-rating">{{ t('shop.rating', { score: ratingScore }) }}</span>
              <span v-if="soldCount != null" class="meta-sold">
                {{ t('shop.soldCount', { count: soldCount }) }}
              </span>
              <span class="meta-stock">{{ t('product.stock', { count: product.stock }) }}</span>
            </div>

            <ProductPromoTags v-if="product.promo_tags?.length" :tags="product.promo_tags" />

            <div class="price-row">
              <SubsidyTag v-if="subsidyInfo" />
              <span v-if="subsidyInfo" class="price-origin">{{ formatPrice(product.price) }}</span>
              <span class="price-current">
                {{ formatPrice(subsidyInfo ? subsidyInfo.final_price : product.price) }}
              </span>
            </div>
            <div v-if="earnPointsHint" class="earn-points-hint">{{ earnPointsHint }}</div>

            <div v-if="subsidyInfo" class="subsidy-panel">
              <div class="subsidy-off">
                {{ t('subsidy.subsidyOff', { amount: subsidyInfo.subsidy_amount }) }}
              </div>
              <div class="subsidy-formula">{{ subsidyInfo.formula }}</div>
              <div v-if="subsidyInfo.government_subsidy" class="gov-tag">政府补贴已抵扣</div>
              <div v-if="subsidyEligibility && !subsidyEligibility.eligible" class="eligibility-warn">
                <p v-for="(msg, idx) in subsidyEligibility.messages" :key="idx">{{ msg }}</p>
              </div>
              <button type="button" class="subsidy-policy-link" @click="showPolicy = true">
                {{ t('subsidy.viewPolicy') }}
              </button>
            </div>

            <div v-if="specOptions.length" class="spec-section">
              <div class="section-label">{{ t('product.specLabel') }}</div>
              <div class="spec-options">
                <span
                  v-for="item in specOptions"
                  :key="item.key"
                  class="spec-option active"
                >
                  {{ item.label }}
                </span>
              </div>
            </div>

            <div class="quantity-section">
              <div class="section-label">{{ t('product.quantity') }}</div>
              <van-stepper
                v-model="quantity"
                integer
                :min="1"
                :max="Math.max(1, product.stock || 1)"
              />
            </div>

            <div v-if="closureNoticeText" class="closure-notice">
              <van-notice-bar
                color="#fff"
                :background="shopClosed ? '#969799' : '#ed6a0c'"
                :text="closureNoticeText"
              />
            </div>

            <div class="action-row">
              <van-button
                class="action-btn action-btn--buy"
                type="primary"
                round
                :loading="buying"
                :disabled="shopPurchaseBlocked"
                @click="handleBuyNow"
              >
                {{ t('product.buyNow') }}
              </van-button>
              <van-button
                class="action-btn action-btn--cart"
                type="warning"
                round
                plain
                :loading="adding"
                :disabled="shopPurchaseBlocked"
                @click="handleAddToCart"
              >
                {{ t('product.addToCart') }}
              </van-button>
            </div>
          </div>
        </div>
      </div>

      <van-dialog v-model:show="showPolicy" :title="subsidyInfo?.policy_name || t('subsidy.policyTitle')">
        <div class="policy-content">{{ subsidyInfo?.policy_description }}</div>
      </van-dialog>

      <section v-if="groupBuyActivity" class="detail-section groupbuy-card">
        <div class="groupbuy-head">
          <span class="groupbuy-tag">{{ t('groupbuy.title') }}</span>
          <span class="groupbuy-price">{{ formatPrice(groupBuyActivity.group_price) }}</span>
          <span class="groupbuy-origin">{{ formatPrice(product.price) }}</span>
        </div>
        <div class="groupbuy-progress">
          <van-progress
            :percentage="groupBuyProgress"
            stroke-width="8"
            color="#ee0a24"
            track-color="#ffe1e1"
            :show-pivot="false"
          />
          <div class="groupbuy-progress__text">
            {{ t('groupbuy.groupSize', { count: groupBuyActivity.group_size }) }}
            ·
            {{ t('groupbuy.needMore', { count: groupBuyNeedMore }) }}
          </div>
        </div>
        <div class="groupbuy-actions">
          <van-button
            v-if="groupBuyActivity.open_group_order_id"
            type="danger"
            round
            block
            plain
            :loading="joiningGroup"
            @click="handleJoinGroup(groupBuyActivity.open_group_order_id)"
          >
            {{ t('groupbuy.joinGroup') }}
          </van-button>
          <van-button
            type="danger"
            round
            block
            :loading="joiningGroup"
            @click="handleJoinGroup()"
          >
            {{ t('groupbuy.startGroup') }}
          </van-button>
        </div>
      </section>

      <div v-if="product.tenant" class="detail-section shop-card">
        <div class="shop-head" @click="goShopHome">
          <van-image class="shop-logo" :src="resolveImageUrl(product.tenant.logo)" fit="cover" round>
            <template #error>
              <div class="shop-logo-fallback">{{ shopName.charAt(0) }}</div>
            </template>
          </van-image>
          <div class="shop-main">
            <div class="shop-title">🏪 {{ shopName }}</div>
            <div class="shop-stats">
              <span class="shop-rating-line">
                {{ t('shop.rating', { score: product.tenant.rating ?? '5.0' }) }}
                <template v-if="product.tenant.rating_count">
                  ({{ t('shop.ratingCount', { count: product.tenant.rating_count }) }})
                </template>
                <van-tag v-if="product.tenant.rating_label" type="primary" plain size="medium" class="rating-tag">
                  {{ t(`shop.ratingLabels.${product.tenant.rating_label}`) }}
                </van-tag>
              </span>
              <span v-if="product.tenant.sold_count != null">
                {{ t('shop.soldCount', { count: product.tenant.sold_count }) }}
              </span>
              <span v-if="shopFollowers > 0">
                {{ t('shop.followerCount', { count: shopFollowers }) }}
              </span>
            </div>
            <div v-if="product.tenant.quality_score" class="shop-dimensions">
              <div class="dimension-row">
                <span>{{ t('shop.qualityScore') }}</span>
                <span>{{ product.tenant.quality_score }}</span>
              </div>
              <div class="dimension-row">
                <span>{{ t('shop.serviceScore') }}</span>
                <span>{{ product.tenant.service_score }}</span>
              </div>
              <div class="dimension-row">
                <span>{{ t('shop.logisticsScore') }}</span>
                <span>{{ product.tenant.logistics_score }}</span>
              </div>
            </div>
            <p v-if="product.tenant.intro" class="shop-intro">{{ product.tenant.intro }}</p>
          </div>
          <van-icon name="arrow" class="shop-arrow" />
        </div>
        <div class="shop-actions" @click.stop>
          <van-button size="small" type="primary" round @click="goShopHome">
            {{ t('product.enterShop') }}
          </van-button>
          <van-button size="small" type="primary" plain round @click="handleContactShop">
            {{ t('product.contactShop') }}
          </van-button>
          <van-button size="small" type="danger" plain round @click="handleComplainShop">
            {{ t('product.complainShop') }}
          </van-button>
        </div>
      </div>

      <div v-if="product.description" class="detail-section desc-card">
        <div class="desc-title">{{ t('product.description') }}</div>
        <div class="desc">{{ product.description }}</div>
      </div>

      <ProductReviewSection v-if="product?.id" :product-id="product.id" />

      <section v-if="relatedProducts.length || relatedLoading" class="detail-section recommend-section">
        <div class="recommend-title">{{ recommendTitle }}</div>
        <ProductListSection
          :products="relatedProducts"
          :loading="relatedLoading"
          :loading-more="relatedLoadingMore"
          :finished="relatedFinished"
          :columns="recommendColumns"
          compact
          show-shop-name
          show-sales
          @select="goRelatedProduct"
          @load-more="loadMoreRelated"
        />
      </section>
    </template>

    <van-action-sheet v-model:show="showAddressPicker" :title="t('checkout.chooseAddress')">
      <div class="address-list">
        <div
          v-for="addr in addresses"
          :key="addr.id"
          class="address-item"
          @click="submitGroupBuy(addr.id)"
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
.detail-page {
  min-height: 100vh;
  background: #f5f6fa;
}

.product-detail {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
  background: #fff;
}

.product-detail__gallery,
.product-detail__info {
  width: 100%;
}

.info-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.product-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  line-height: 1.4;
  color: #323233;
}

.product-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 13px;
  color: #969799;
}

.meta-rating {
  color: #ff976a;
}

.price-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 12px 0;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
}

.earn-points-hint {
  margin: -4px 0 8px;
  font-size: 13px;
  color: #ff6034;
}

.price-current {
  font-size: 32px;
  color: #ee0a24;
  font-weight: 700;
  line-height: 1.2;
}

.price-origin {
  color: #999;
  font-size: 14px;
  text-decoration: line-through;
}

.subsidy-panel {
  margin-top: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fff8e6;
}

.subsidy-off {
  color: #07c160;
  font-size: 14px;
  font-weight: 600;
}

.subsidy-formula {
  margin-top: 4px;
  color: #666;
  font-size: 12px;
}

.gov-tag {
  margin-top: 6px;
  font-size: 12px;
  color: #07c160;
  font-weight: 600;
}

.eligibility-warn {
  margin-top: 8px;
  padding: 8px;
  background: #fff7e6;
  border-radius: 6px;
  font-size: 12px;
  color: #d46b08;
}

.eligibility-warn p {
  margin: 0;
}

.subsidy-policy-link {
  margin-top: 6px;
  padding: 0;
  border: none;
  background: none;
  color: #1989fa;
  font-size: 12px;
  cursor: pointer;
}

.policy-content {
  padding: 8px 4px 16px;
  line-height: 1.6;
  color: #666;
  white-space: pre-wrap;
}

.section-label {
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 600;
  color: #323233;
}

.spec-options {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.spec-option {
  padding: 8px 16px;
  border: 1px solid #dcdee0;
  border-radius: 999px;
  font-size: 13px;
  color: #646566;
  background: #fff;
}

.spec-option.active {
  border-color: #1989fa;
  color: #1989fa;
  background: #ecf5ff;
}

.quantity-section :deep(.van-stepper) {
  justify-content: flex-start;
}

.action-row {
  display: flex;
  gap: 12px;
  margin-top: 4px;
}

.action-btn {
  flex: 1;
  height: 46px;
  font-size: 15px;
  font-weight: 600;
}

.action-btn--buy {
  background: #1989fa;
  border-color: #1989fa;
}

.action-btn--cart {
  color: #ff976a;
  border-color: #ff976a;
}

.detail-section {
  margin: 12px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
}

.detail-skeleton .product-detail {
  padding: 12px;
}

.gallery-skeleton,
.gallery-skeleton :deep(.van-skeleton-image) {
  width: 100%;
  height: clamp(280px, 45vh, 400px);
}

.state-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 16px;
  color: #969799;
}

.desc-title {
  margin-bottom: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #323233;
}

.desc {
  font-size: 14px;
  color: #646566;
  line-height: 1.6;
  white-space: pre-wrap;
}

.shop-card {
  cursor: pointer;
}

.shop-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.shop-logo {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
}

.shop-logo-fallback {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #ecf5ff;
  color: #1989fa;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.shop-main {
  flex: 1;
  min-width: 0;
}

.shop-title {
  font-size: 15px;
  font-weight: 600;
}

.shop-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 6px;
  font-size: 12px;
  color: #969799;
}

.shop-rating-line {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.rating-tag {
  margin-left: 2px;
}

.shop-dimensions {
  margin-top: 8px;
  display: grid;
  gap: 4px;
  font-size: 12px;
  color: #646566;
}

.dimension-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.shop-intro {
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 1.5;
  color: #646566;
}

.shop-arrow {
  color: #c8c9cc;
  margin-top: 4px;
}

.shop-actions {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}

.groupbuy-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
}

.groupbuy-tag {
  padding: 2px 8px;
  border-radius: 4px;
  background: #ffe8e8;
  color: #ee0a24;
  font-size: 12px;
  font-weight: 600;
}

.groupbuy-price {
  font-size: 22px;
  font-weight: 700;
  color: #ee0a24;
}

.groupbuy-origin {
  font-size: 13px;
  color: #969799;
  text-decoration: line-through;
}

.groupbuy-progress {
  margin-top: 12px;
}

.groupbuy-progress__text {
  margin-top: 6px;
  font-size: 12px;
  color: #646566;
}

.groupbuy-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
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

.recommend-title {
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 700;
  color: #323233;
}

.shop-head {
  cursor: pointer;
}

@media (min-width: 769px) {
  .product-detail {
    flex-direction: row;
    align-items: flex-start;
    gap: 40px;
    max-width: 1200px;
    margin: 0 auto;
    padding: 24px;
    border-radius: 12px;
  }

  .product-detail__gallery {
    flex: 0 0 400px;
    max-width: 400px;
    overflow: visible;
    position: relative;
    z-index: 2;
  }

  .product-detail__info {
    flex: 1;
    min-width: 0;
  }

  .detail-section {
    max-width: 1200px;
    margin-left: auto;
    margin-right: auto;
  }

  .recommend-section :deep(.product-list) {
    --cols: 4;
  }

  .recommend-section :deep(.van-list__finished-text) {
    display: block;
  }
}
</style>
