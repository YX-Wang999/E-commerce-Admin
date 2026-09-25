<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { formatPrice, resolveImageUrl } from '@/utils/product'
import { getProductShopId, getProductShopName, isMerchantProduct } from '@/utils/shop'
import ProductPromoTags from '@/components/product/ProductPromoTags.vue'

const props = defineProps({
  product: {
    type: Object,
    required: true,
  },
  compact: Boolean,
  dense: Boolean,
  showShopName: Boolean,
  showSubsidy: Boolean,
  showSales: Boolean,
})

defineEmits(['click'])

const router = useRouter()
const { t } = useI18n()

const shopName = computed(() => getProductShopName(props.product) || t('product.platformShop'))
const shopRating = computed(() => {
  const rating = props.product.tenant_rating ?? props.product.tenant?.rating
  if (rating != null && rating !== '') return Number(rating).toFixed(1)
  if (!isMerchantProduct(props.product)) return '4.9'
  return null
})

const promoTags = computed(() => {
  if (Array.isArray(props.product.promo_tags) && props.product.promo_tags.length) {
    return props.product.promo_tags
  }
  const legacy = []
  if (props.showSubsidy || props.product.is_subsidy) {
    legacy.push({
      code: 'subsidy',
      name: t('product.tagSubsidy'),
      color: '#FF6B35',
      text_color: '#FFFFFF',
    })
  }
  return legacy
})

function handleShopClick(event) {
  event.stopPropagation()
  const shopId = getProductShopId(props.product)
  if (shopId) {
    router.push({ name: 'ShopHome', params: { id: shopId } })
  }
}
</script>

<template>
  <div
    class="product-card card-interactive"
    :class="{ compact, dense }"
    @click="$emit('click', product)"
  >
    <div class="product-image-wrap">
      <van-image
        :key="product.image"
        class="product-image"
        :src="resolveImageUrl(product.image)"
        fit="cover"
        lazy-load
      >
        <template #loading>
          <van-skeleton-image class="image-skeleton" />
        </template>
        <template #error>
          <div class="image-fallback">{{ t('common.noImage') }}</div>
        </template>
      </van-image>
    </div>

    <div class="product-info">
      <div class="product-name">{{ product.name }}</div>

      <div v-if="showShopName" class="shop-row" @click="handleShopClick">
        <span class="shop-row__name">{{ shopName }}</span>
        <span v-if="shopRating" class="shop-row__rating">★ {{ shopRating }}</span>
      </div>

      <ProductPromoTags :tags="promoTags" />

      <div class="product-price">{{ formatPrice(product.price) }}</div>

      <div v-if="showSales && product.sold_count != null" class="product-sales">
        {{ t('product.soldCount', { count: product.sold_count }) }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.product-card {
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
  border: 1px solid #f0f0f0;
}

.product-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.product-image-wrap {
  position: relative;
  width: 100%;
  padding-bottom: 100%;
  background: #f0f2f5;
  overflow: hidden;
}

.product-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
}

.product-image :deep(.van-image__img),
.product-image :deep(img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-fallback,
.image-skeleton {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
  color: #999;
  font-size: 12px;
}

.product-info {
  padding: 8px 10px 10px;
}

.product-card.dense .product-info {
  padding: 6px 8px 8px;
}

.product-card.compact .product-info {
  padding: 6px 8px;
}

.product-name {
  font-size: 13px;
  color: #333;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 36px;
}

.product-card.dense .product-name,
.product-card.compact .product-name {
  min-height: auto;
  font-size: 12px;
  -webkit-line-clamp: 2;
}

.shop-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-top: 6px;
  font-size: 11px;
  color: #969799;
}

.shop-row__name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.shop-row__rating {
  flex-shrink: 0;
  color: #ff976a;
  font-weight: 600;
}

.product-price {
  margin-top: 8px;
  font-size: 18px;
  font-weight: 800;
  color: #e4393c;
  line-height: 1.2;
}

.product-card.dense .product-price,
.product-card.compact .product-price {
  font-size: 16px;
}

.product-sales {
  margin-top: 4px;
  font-size: 11px;
  color: #999;
}
</style>
