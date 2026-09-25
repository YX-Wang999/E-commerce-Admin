<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import ProductListSection from '@/components/product/ProductListSection.vue'
import { useSubsidyProductList } from '@/composables/useSubsidyProductList'

defineProps({
  embedded: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['collapse'])

const router = useRouter()
const { t } = useI18n()
const {
  products,
  loading,
  loadingMore,
  finished,
  error,
  load,
  loadMore,
  retry,
} = useSubsidyProductList()

function goProduct(product) {
  router.push({ name: 'ProductDetail', params: { id: product.id } })
}

onMounted(() => load(true))
</script>

<template>
  <div class="subsidy-panel" :class="{ 'subsidy-panel--embedded': embedded }">
    <div class="subsidy-header">
      <span class="subsidy-header__name">{{ t('subsidy.zoneTitle') }}</span>
      <span class="subsidy-header__tip">{{ t('subsidy.zoneDesc') }}</span>
    </div>

    <main class="subsidy-products">
      <ProductListSection
        :products="products"
        :loading="loading"
        :loading-more="loadingMore"
        :finished="finished"
        :error="error"
        :columns="2"
        dense
        show-subsidy
        show-shop-name
        :empty-description="t('subsidy.emptyProducts')"
        @load-more="loadMore"
        @retry="retry"
        @select="goProduct"
      />
    </main>
  </div>
</template>

<style scoped>
.subsidy-panel {
  display: flex;
  flex-direction: column;
  background: #f5f6fa;
}

.subsidy-panel--embedded {
  background: transparent;
}

.subsidy-header {
  flex-shrink: 0;
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin: 8px 12px 0;
  padding: 10px 12px;
  background: #fff;
  border-radius: 8px;
}

.subsidy-header__name {
  font-size: 15px;
  font-weight: 700;
  color: #f5a623;
}

.subsidy-header__tip {
  font-size: 12px;
  color: #969799;
}

.subsidy-products {
  padding: 10px 12px 16px;
}

.subsidy-panel:not(.subsidy-panel--embedded) .subsidy-products {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.subsidy-products :deep(.product-list) {
  gap: 10px;
}
</style>
