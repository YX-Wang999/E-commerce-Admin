<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useMediaQuery } from '@vueuse/core'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import ProductListSection from '@/components/product/ProductListSection.vue'
import { getCategoryFlat, getCategoryTree } from '@/api/product'
import { useCategoryProductList } from '@/composables/useCategoryProductList'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const isWide = useMediaQuery('(min-width: 992px)')

const categories = ref([])
const categoriesLoading = ref(true)
const categoriesError = ref(false)
const activeIndex = ref(0)
const productScroller = ref(null)

const productColumns = computed(() => (isWide.value ? 4 : 2))

const {
  products,
  loading: productsLoading,
  loadingMore,
  finished,
  error: productsError,
  load: loadProducts,
  loadMore,
  retry,
} = useCategoryProductList()

const activeCategory = computed(() => categories.value[activeIndex.value] || null)
const activeCategoryId = computed(() => activeCategory.value?.id ?? null)

function normalizeTopCategories(tree) {
  return [...tree]
    .filter((item) => item.is_active)
    .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
}

function resolveInitialIndex(list) {
  const catId = route.query.catId?.toString()
  if (!catId) return 0
  const index = list.findIndex((item) => String(item.id) === catId)
  return index >= 0 ? index : 0
}

function syncRouteQuery(categoryId) {
  const nextCatId = categoryId ? String(categoryId) : undefined
  if (route.query.catId === nextCatId) return
  router.replace({
    name: 'Category',
    query: nextCatId ? { catId: nextCatId } : {},
  })
}

function resetProductScroll() {
  nextTick(() => {
    if (productScroller.value) {
      productScroller.value.scrollTop = 0
    }
  })
}

function goSearch() {
  router.push({ name: 'Search' })
}

function goProduct(product) {
  router.push({ name: 'ProductDetail', params: { id: product.id } })
}

function onSidebarChange(index) {
  activeIndex.value = index
}

async function fetchCategories() {
  categoriesLoading.value = true
  categoriesError.value = false
  try {
    const res = await getCategoryTree({ active_only: true })
    const list = normalizeTopCategories(res.data || [])
    categories.value = list
    activeIndex.value = resolveInitialIndex(list)
  } catch {
    try {
      const flatRes = await getCategoryFlat()
      const flatList = (flatRes.data || []).filter((item) => !item.parent && item.is_active)
      categories.value = flatList.sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
      activeIndex.value = resolveInitialIndex(categories.value)
    } catch {
      categories.value = []
      categoriesError.value = true
    }
  } finally {
    categoriesLoading.value = false
  }
}

function retryCategories() {
  return fetchCategories()
}

watch(activeCategoryId, (categoryId) => {
  if (!categoryId) return
  syncRouteQuery(categoryId)
  resetProductScroll()
  loadProducts(categoryId, true)
})

watch(
  () => route.query.catId,
  (catId) => {
    if (!categories.value.length || !catId) return
    const index = categories.value.findIndex((item) => String(item.id) === String(catId))
    if (index >= 0 && index !== activeIndex.value) {
      activeIndex.value = index
    }
  },
)

onMounted(fetchCategories)
</script>

<template>
  <div class="category-page">
    <div class="search-bar" @click="goSearch">
      <van-search
        :placeholder="t('search.placeholder')"
        shape="round"
        readonly
      />
    </div>

    <div class="category-body">
      <aside class="category-sidebar">
        <div v-if="categoriesLoading" class="sidebar-skeleton">
          <van-skeleton v-for="i in 8" :key="i" title :row="0" />
        </div>

        <div v-else-if="categoriesError" class="sidebar-state">
          <p>{{ t('common.loadFailedRetry') }}</p>
          <van-button size="mini" type="primary" plain @click="retryCategories">
            {{ t('common.retry') }}
          </van-button>
        </div>

        <van-empty
          v-else-if="!categories.length"
          :description="t('category.noCategories')"
          image-size="64"
        />

        <van-sidebar
          v-else
          v-model="activeIndex"
          @change="onSidebarChange"
        >
          <van-sidebar-item
            v-for="item in categories"
            :key="item.id"
            :title="item.name"
          />
        </van-sidebar>
      </aside>

      <main ref="productScroller" class="category-products">
        <div v-if="activeCategory" class="category-header">
          <span class="category-header__name">{{ activeCategory.name }}</span>
          <span class="category-header__tip">{{ t('category.allProducts') }}</span>
        </div>

        <ProductListSection
          v-if="activeCategoryId"
          :key="activeCategoryId"
          :products="products"
          :loading="productsLoading"
          :loading-more="loadingMore"
          :finished="finished"
          :error="productsError"
          :columns="productColumns"
          dense
          show-shop-name
          :scroller="() => productScroller"
          @load-more="loadMore(activeCategoryId)"
          @retry="retry(activeCategoryId)"
          @select="goProduct"
        />

        <van-empty
          v-else-if="!categoriesLoading && !categoriesError"
          :description="t('category.noCategories')"
        />
      </main>
    </div>
  </div>
</template>

<style scoped>
.category-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 200px);
  min-height: 480px;
  background: #f5f6fa;
  overflow: hidden;
}

.search-bar {
  flex-shrink: 0;
  background: #fff;
  cursor: pointer;
}

.search-bar :deep(.van-search) {
  pointer-events: none;
}

.category-body {
  display: flex;
  flex: 1;
  min-height: 0;
  border-top: 1px solid #ebedf0;
}

.category-sidebar {
  width: 80px;
  flex-shrink: 0;
  overflow-y: auto;
  background: #f7f8fa;
  border-right: 1px solid #ebedf0;
}

.category-sidebar :deep(.van-sidebar) {
  width: 80px;
}

.category-sidebar :deep(.van-sidebar-item) {
  padding: 0;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.category-sidebar :deep(.van-sidebar-item__text) {
  font-size: 13px;
  line-height: 1.25;
  text-align: center;
  word-break: break-all;
  padding: 8px 6px;
}

.category-sidebar :deep(.van-sidebar-item--select) {
  background: #1989fa;
  color: #fff;
}

.category-sidebar :deep(.van-sidebar-item--select::before) {
  background: #fff;
}

.category-products {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: 10px;
}

.category-products :deep(.product-list) {
  gap: 10px;
}

.category-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 10px;
  padding: 8px 10px;
  background: #fff;
  border-radius: 8px;
}

.category-header__name {
  font-size: 15px;
  font-weight: 700;
  color: #323233;
}

.category-header__tip {
  font-size: 12px;
  color: #969799;
}

.sidebar-skeleton {
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sidebar-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px 8px;
  font-size: 12px;
  color: #969799;
  text-align: center;
}

@media (min-width: 992px) {
  .category-page {
    max-width: 1280px;
    margin: 0 auto;
  }
}
</style>
