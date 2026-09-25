<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatMoney } from '@/utils/money'

const props = defineProps({
  product: {
    type: Object,
    required: true,
  },
  shopName: {
    type: String,
    default: '',
  },
  imageUrl: {
    type: String,
    default: '',
  },
})

const { t } = useI18n()

const promoTags = computed(() => {
  if (Array.isArray(props.product?.promo_tags) && props.product.promo_tags.length) {
    return props.product.promo_tags.slice(0, 3)
  }
  return []
})

const shopRating = computed(() => {
  const rating = props.product?.tenant_rating ?? props.product?.tenant?.rating
  if (rating != null && rating !== '') return Number(rating).toFixed(1)
  if (!props.product?.tenant && !props.product?.tenant_name) return '4.9'
  return null
})

const displayPrice = computed(() => formatMoney(props.product?.price))
</script>

<template>
  <div class="mall-preview">
    <p class="mall-preview__tip">{{ t('seller.mallPreviewTip') }}</p>
    <div class="product-card">
      <div class="product-image-wrap">
        <img v-if="imageUrl" :src="imageUrl" class="product-image" alt="" />
        <div v-else class="image-fallback">-</div>
      </div>
      <div class="product-info">
        <div class="product-name">{{ product.name || t('seller.productName') }}</div>
        <div v-if="shopName" class="shop-row">
          <span class="shop-row__name">{{ shopName }}</span>
          <span v-if="shopRating" class="shop-row__rating">★ {{ shopRating }}</span>
        </div>
        <div v-if="promoTags.length" class="promo-tags">
          <span
            v-for="tag in promoTags"
            :key="tag.code"
            class="promo-tag"
            :style="{ background: tag.color, color: tag.text_color || '#fff' }"
          >
            <span v-if="tag.icon" class="promo-tag__icon">{{ tag.icon }}</span>
            {{ tag.name }}
          </span>
        </div>
        <div class="product-price">{{ displayPrice }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mall-preview__tip {
  margin: 0 0 12px;
  color: #909399;
  font-size: 13px;
}

.product-card {
  width: 100%;
  max-width: 220px;
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #f0f0f0;
}

.product-image-wrap {
  position: relative;
  width: 100%;
  padding-bottom: 100%;
  background: #f0f2f5;
  overflow: hidden;
}

.product-image,
.image-fallback {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 12px;
}

.product-info {
  padding: 8px 10px 10px;
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

.promo-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.promo-tag {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  max-width: 100%;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 10px;
  line-height: 1.5;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.promo-tag__icon {
  font-size: 10px;
  line-height: 1;
}

.product-price {
  margin-top: 8px;
  font-size: 18px;
  font-weight: 800;
  color: #e4393c;
  line-height: 1.2;
}
</style>
