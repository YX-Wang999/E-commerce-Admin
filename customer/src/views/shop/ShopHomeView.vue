<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import ProductListSection from '@/components/product/ProductListSection.vue'
import ShopSuggestionPanel from '@/components/shop/ShopSuggestionPanel.vue'
import { getProducts } from '@/api/product'
import { getTenant } from '@/api/tenant'
import { resolveImageUrl } from '@/utils/product'
import { requireLogin } from '@/stores/loginGate'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const tenant = ref(null)
const products = ref([])
const loading = ref(true)
const productsLoading = ref(true)
const loadError = ref(false)
const page = ref(1)
const finished = ref(false)
const loadingMore = ref(false)

const tenantId = computed(() => Number(route.params.id))

async function fetchTenant() {
  loading.value = true
  loadError.value = false
  try {
    const res = await getTenant(tenantId.value)
    tenant.value = res.data
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

async function fetchProducts(reset = false) {
  if (reset) {
    page.value = 1
    finished.value = false
    products.value = []
  }
  if (finished.value) return

  const isFirst = page.value === 1
  if (isFirst) {
    productsLoading.value = true
  } else {
    loadingMore.value = true
  }

  try {
    const res = await getProducts({
      tenant_id: tenantId.value,
      page: page.value,
      page_size: 12,
      status: 'on_sale',
    })
    const { results = [], count = 0 } = res.data || {}
    products.value = isFirst ? results : [...products.value, ...results]
    finished.value = products.value.length >= count || results.length < 12
    if (!finished.value) page.value += 1
  } finally {
    productsLoading.value = false
    loadingMore.value = false
  }
}

function goProduct(product) {
  router.push({ name: 'ProductDetail', params: { id: product.id } })
}

async function handleContactShop() {
  try {
    await requireLogin({ redirect: route.fullPath })
    router.push({ name: 'Chat', query: { tenant_id: String(tenantId.value) } })
  } catch {
    // cancelled
  }
}

onMounted(async () => {
  await fetchTenant()
  if (!loadError.value) {
    await fetchProducts(true)
  }
})
</script>

<template>
  <div class="shop-page">
    <van-nav-bar
      :title="tenant?.name || t('shop.title')"
      left-arrow
      fixed
      placeholder
      @click-left="router.back()"
    />

    <van-loading v-if="loading" class="page-loading" vertical>{{ t('common.loading') }}</van-loading>

    <van-empty v-else-if="loadError" :description="t('shop.loadFailed')">
      <van-button round type="primary" size="small" @click="fetchTenant">
        {{ t('common.retry') }}
      </van-button>
    </van-empty>

    <template v-else-if="tenant">
      <van-notice-bar
        v-if="tenant.closure_state === 'closed' || tenant.status === 'closed'"
        color="#fff"
        background="#969799"
        :text="t('shop.closedBanner')"
      />
      <van-notice-bar
        v-else-if="tenant.closure_state === 'closing'"
        color="#fff"
        background="#ed6a0c"
        :text="tenant.closure_notice_end_at ? t('shop.closingBanner', { date: String(tenant.closure_notice_end_at).slice(0, 10) }) : t('shop.closingBannerSoon')"
      />

      <div class="shop-hero">
        <van-image class="shop-logo" :src="resolveImageUrl(tenant.logo)" fit="cover" round>
          <template #error>
            <div class="logo-fallback">{{ tenant.name?.charAt(0) || '店' }}</div>
          </template>
        </van-image>
        <div class="shop-meta">
          <h1 class="shop-name">{{ tenant.name }}</h1>
          <div class="shop-stats">
            <span>{{ t('shop.rating', { score: tenant.rating ?? '5.0' }) }}</span>
            <span>{{ t('shop.soldCount', { count: tenant.sold_count ?? 0 }) }}</span>
            <span>{{ t('shop.productCount', { count: tenant.product_count ?? 0 }) }}</span>
          </div>
          <p v-if="tenant.intro" class="shop-intro">{{ tenant.intro }}</p>
        </div>
      </div>

      <div class="shop-actions-grid">
        <div class="action-card contact-card">
          <div class="action-title">{{ t('shop.contactSupport') }}</div>
          <p class="action-desc">{{ t('shop.contactSupportDesc') }}</p>
          <van-button type="primary" block round icon="service-o" @click="handleContactShop">
            {{ t('shop.contactSupport') }}
          </van-button>
        </div>
        <ShopSuggestionPanel :tenant-id="tenantId" :redirect-path="route.fullPath" />
      </div>

      <section class="products-section">
        <h2 class="section-title">{{ t('shop.allProducts') }}</h2>
        <ProductListSection
          :products="products"
          :loading="productsLoading"
          :loading-more="loadingMore"
          :finished="finished"
          :error="false"
          :columns="4"
          compact
          show-shop-name
          @load-more="fetchProducts(false)"
          @retry="fetchProducts(true)"
          @select="goProduct"
        />
      </section>
    </template>
  </div>
</template>

<style scoped>
.shop-page {
  min-height: 100vh;
  background: #f5f6fa;
  padding-bottom: 24px;
}

.page-loading {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.shop-hero {
  display: flex;
  gap: 14px;
  margin: 12px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
}

.shop-logo {
  width: 72px;
  height: 72px;
  flex-shrink: 0;
  border: 1px solid #f0f0f0;
}

.logo-fallback {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: #ecf5ff;
  color: #1989fa;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 700;
}

.shop-meta {
  min-width: 0;
  flex: 1;
}

.shop-name {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #323233;
}

.shop-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 8px;
  font-size: 12px;
  color: #969799;
}

.shop-intro {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: #646566;
}

.shop-actions-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 0 12px 12px;
}

.action-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px;
}

.action-title {
  font-size: 15px;
  font-weight: 600;
  color: #323233;
}

.action-desc {
  margin: 8px 0 12px;
  font-size: 12px;
  line-height: 1.5;
  color: #969799;
  min-height: 36px;
}

.products-section {
  margin: 0 12px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
}

.section-title {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 700;
  color: #323233;
}

@media (max-width: 640px) {
  .shop-actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>
