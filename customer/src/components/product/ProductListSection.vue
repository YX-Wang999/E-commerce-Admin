<script setup>
import { computed, unref } from 'vue'
import { useI18n } from 'vue-i18n'
import ProductCard from '@/components/product/ProductCard.vue'

const props = defineProps({
  products: {
    type: Array,
    default: () => [],
  },
  loading: Boolean,
  loadingMore: Boolean,
  finished: Boolean,
  error: Boolean,
  columns: {
    type: Number,
    default: 2,
  },
  compact: Boolean,
  dense: Boolean,
  showShopName: Boolean,
  showSales: Boolean,
  emptyDescription: {
    type: String,
    default: '',
  },
  scroller: {
    type: [Object, Element, Function],
    default: undefined,
  },
})

defineEmits(['load-more', 'retry', 'select'])

const { t } = useI18n()

const resolvedScroller = computed(() => {
  const target = props.scroller
  if (typeof target === 'function') {
    return target()
  }
  return unref(target)
})
</script>

<template>
  <div class="product-section">
    <div v-if="loading" class="product-list" :style="{ '--cols': columns }">
      <div v-for="i in columns * 2" :key="i" class="skeleton-card" :class="{ compact }">
        <div class="skeleton-image-wrap">
          <van-skeleton-image />
        </div>
        <van-skeleton :row="compact ? 1 : 2" />
      </div>
    </div>

    <div v-else-if="error" class="state-box">
      <p>{{ t('common.loadFailedRetry') }}</p>
      <van-button size="small" type="primary" plain @click="$emit('retry')">
        {{ t('common.retry') }}
      </van-button>
    </div>

    <van-empty
      v-else-if="!products.length"
      :description="emptyDescription || t('product.noProducts')"
    />

    <van-list
      v-else
      :loading="loadingMore"
      :finished="finished"
      :immediate-check="false"
      :finished-text="t('product.noMore')"
      :scroller="resolvedScroller"
      @load="$emit('load-more')"
    >
      <div class="product-list" :style="{ '--cols': columns }">
        <ProductCard
          v-for="item in products"
          :key="item.id"
          :product="item"
          :show-subsidy="item.is_subsidy"
          :compact="compact"
          :dense="dense"
          :show-shop-name="showShopName"
          :show-sales="showSales"
          @click="$emit('select', $event)"
        />
      </div>
    </van-list>
  </div>
</template>

<style scoped>
.product-section {
  padding: 0;
  overscroll-behavior: contain;
}
.product-list {
  display: grid;
  grid-template-columns: repeat(var(--cols, 2), minmax(0, 1fr));
  gap: 10px;
}
.skeleton-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  padding: 8px;
}
.skeleton-image-wrap {
  position: relative;
  width: 100%;
  padding-bottom: 100%;
  margin-bottom: 8px;
  background: #f0f2f5;
  overflow: hidden;
}
.skeleton-image-wrap :deep(.van-skeleton-image) {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
.skeleton-card.compact {
  padding: 6px;
}
.state-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px 16px;
  color: #969799;
}
</style>
