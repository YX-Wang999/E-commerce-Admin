<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import ProductListSection from '@/components/product/ProductListSection.vue'
import { getTenants } from '@/api/tenant'
import { useProductList } from '@/composables/useProductList'
import {
  addSearchHistory,
  clearSearchHistory,
  getSearchHistory,
} from '@/utils/searchHistory'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const keyword = ref('')
const history = ref(getSearchHistory())
const selectedTenantId = ref('all')
const tenants = ref([])

const searchKeyword = computed(() => route.query.keyword?.toString().trim() || '')

const tenantOptions = computed(() => [
  { text: t('shop.allShops'), value: 'all' },
  ...tenants.value.map((item) => ({ text: item.name, value: String(item.id) })),
])

const { products, loading, loadingMore, finished, error, load, loadMore, retry } = useProductList(() => {
  const value = keyword.value.trim()
  const params = {}
  if (value) params.keyword = value
  if (selectedTenantId.value !== 'all') params.tenant_id = selectedTenantId.value
  return params
})

function refreshHistory() {
  history.value = getSearchHistory()
}

function handleSearch(value) {
  const next = (value || keyword.value || '').trim()
  if (next) {
    addSearchHistory(next)
    refreshHistory()
  }
  router.replace({
    name: 'Search',
    query: next ? { keyword: next } : {},
  })
}

function searchFromHistory(item) {
  keyword.value = item
  handleSearch(item)
}

function handleClearHistory() {
  clearSearchHistory()
  refreshHistory()
}

function goProduct(product) {
  router.push({ name: 'ProductDetail', params: { id: product.id } })
}

watch(searchKeyword, (value) => {
  keyword.value = value
  if (value) {
    load(true)
  }
}, { immediate: true })

watch(selectedTenantId, () => {
  if (searchKeyword.value) {
    load(true)
  }
})

async function fetchTenants() {
  try {
    const res = await getTenants({ page_size: 50 })
    tenants.value = res.data?.results || res.data || []
  } catch {
    tenants.value = []
  }
}

fetchTenants()
</script>

<template>
  <div class="search-page">
    <van-search
      v-model="keyword"
      show-action
      :placeholder="t('search.placeholder')"
      shape="round"
      autofocus
      @search="handleSearch"
      @cancel="$router.back()"
    />

    <template v-if="searchKeyword">
      <div v-if="tenantOptions.length > 1" class="tenant-filter">
        <van-dropdown-menu>
          <van-dropdown-item v-model="selectedTenantId" :options="tenantOptions" />
        </van-dropdown-menu>
      </div>

      <div class="search-tip">
        {{ t('search.result', { keyword: searchKeyword }) }}
      </div>

      <ProductListSection
        :products="products"
        :loading="loading"
        :loading-more="loadingMore"
        :finished="finished"
        :error="error"
        :columns="2"
        show-shop-name
        :empty-description="t('search.noResults')"
        @load-more="loadMore"
        @retry="retry"
        @select="goProduct"
      />
    </template>

    <div v-else class="search-history">
      <div v-if="history.length" class="history-header">
        <span class="history-title">{{ t('search.history') }}</span>
        <van-button size="mini" plain type="default" @click="handleClearHistory">
          {{ t('search.clearHistory') }}
        </van-button>
      </div>

      <div v-if="history.length" class="history-tags">
        <van-tag
          v-for="item in history"
          :key="item"
          plain
          type="primary"
          size="medium"
          class="history-tag"
          @click="searchFromHistory(item)"
        >
          {{ item }}
        </van-tag>
      </div>

      <van-empty
        v-else
        :description="t('search.historyEmpty')"
        image-size="80"
      />
    </div>
  </div>
</template>

<style scoped>
.search-page {
  min-height: 100vh;
  background: #f5f6fa;
}

.search-tip {
  padding: 8px 16px 0;
  font-size: 13px;
  color: #969799;
}

.tenant-filter {
  padding: 0 16px;
}

.search-history {
  padding: 12px 16px;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.history-title {
  font-size: 14px;
  font-weight: 600;
  color: #323233;
}

.history-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.history-tag {
  cursor: pointer;
}
</style>
