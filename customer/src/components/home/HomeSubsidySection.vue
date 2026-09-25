<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import SubsidyTag from '@shared/components/SubsidyTag.vue'
import { getSubsidyProducts } from '@/api/subsidy'
import { formatPrice, resolveImageUrl } from '@/utils/product'

const props = defineProps({
  /** 展开完整列表（首页内嵌，不跳转新页） */
  expanded: {
    type: Boolean,
    default: false,
  },
  /** 独立国补页：隐藏收起按钮 */
  standalone: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['expand', 'collapse'])

const router = useRouter()
const { t } = useI18n()

const loading = ref(true)
const products = ref([])

const previewItems = computed(() => products.value.slice(0, 5))

async function fetchSubsidy() {
  loading.value = true
  try {
    const res = await getSubsidyProducts({ page: 1, page_size: 50 })
    products.value = res.data?.results || []
  } catch {
    products.value = []
  } finally {
    loading.value = false
  }
}

function goMore() {
  if (props.expanded) return
  emit('expand')
}

function goProduct(item) {
  router.push({ name: 'ProductDetail', params: { id: item.product_id } })
}

onMounted(fetchSubsidy)
</script>

<template>
  <section v-if="standalone || loading || products.length" class="subsidy-section card-block">
    <div class="section-head">
      <div class="section-title">
        <span class="title-icon">🏛️</span>
        <span class="title-text">{{ t('subsidy.zoneTitle') }}</span>
        <span class="title-badge">{{ t('subsidy.zoneBadge') }}</span>
      </div>
      <button v-if="!expanded && !standalone" type="button" class="more-link" @click="goMore">
        {{ t('home.viewMore') }}
        <van-icon name="arrow" size="12" />
      </button>
      <button v-else-if="expanded && !standalone" type="button" class="more-link" @click="emit('collapse')">
        {{ t('subsidy.collapse') }}
        <van-icon name="arrow-up" size="12" />
      </button>
    </div>

    <p class="section-desc">{{ t('subsidy.zoneDesc') }}</p>

    <van-skeleton v-if="loading" :row="2" title />

    <template v-else-if="!expanded && !standalone">
      <div class="scroll-row">
        <article
          v-for="item in previewItems"
          :key="item.id"
          class="preview-card"
          @click="goProduct(item)"
        >
          <div class="preview-img-wrap">
            <img :src="resolveImageUrl(item.image)" class="preview-img" alt="" />
            <SubsidyTag class="preview-tag" />
          </div>
          <div class="final-price">{{ formatPrice(item.final_price) }}</div>
          <div class="origin-price">{{ formatPrice(item.price) }}</div>
          <div class="subsidy-off">{{ t('subsidy.subsidyOff', { amount: item.subsidy_amount }) }}</div>
        </article>
      </div>
    </template>

    <div v-else class="product-list">
      <van-empty v-if="!products.length" :description="t('subsidy.emptyProducts')" />
      <article
        v-for="item in products"
        :key="item.id"
        class="product-card"
        @click="goProduct(item)"
      >
        <div class="product-card__img-wrap">
          <img :src="resolveImageUrl(item.image)" class="product-card__img" alt="" />
          <SubsidyTag class="product-card__tag" />
        </div>
        <div class="product-card__body">
          <div class="product-card__name">{{ item.name }}</div>
          <div class="product-card__price">
            <span class="final">{{ formatPrice(item.final_price) }}</span>
            <span class="origin">{{ formatPrice(item.price) }}</span>
          </div>
          <div class="product-card__subsidy">
            {{ t('subsidy.subsidyOff', { amount: item.subsidy_amount }) }}
          </div>
          <van-button type="primary" size="small" block round color="#f5a623">
            {{ t('subsidy.buyNow') }}
          </van-button>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.card-block {
  margin: 12px 12px 0;
  padding: 12px;
  background: #fff;
  border-radius: 12px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.title-icon {
  font-size: 18px;
}

.title-text {
  font-size: 16px;
  font-weight: 700;
  color: #f5a623;
}

.title-badge {
  padding: 1px 6px;
  border-radius: 4px;
  background: linear-gradient(135deg, #f5a623, #f7c948);
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  white-space: nowrap;
}

.section-desc {
  margin: 6px 0 10px;
  font-size: 12px;
  color: #969799;
}

.more-link {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  border: none;
  background: transparent;
  font-size: 12px;
  color: #999;
  cursor: pointer;
  flex-shrink: 0;
}

.scroll-row {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 4px;
  -webkit-overflow-scrolling: touch;
}

.scroll-row::-webkit-scrollbar {
  display: none;
}

.preview-card {
  flex: 0 0 100px;
  cursor: pointer;
}

.preview-img-wrap {
  position: relative;
  width: 100px;
  height: 100px;
}

.preview-img {
  width: 100%;
  height: 100%;
  border-radius: 8px;
  object-fit: cover;
  background: #f5f5f5;
}

.preview-tag {
  position: absolute;
  left: 4px;
  top: 4px;
  transform: scale(0.85);
  transform-origin: left top;
}

.final-price {
  margin-top: 6px;
  font-size: 14px;
  font-weight: 700;
  color: #e4393c;
}

.origin-price {
  font-size: 11px;
  color: #999;
  text-decoration: line-through;
}

.subsidy-off {
  margin-top: 2px;
  font-size: 10px;
  color: #07c160;
  font-weight: 600;
}

.product-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.product-card {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  cursor: pointer;
}

.product-card__img-wrap {
  position: relative;
  flex-shrink: 0;
}

.product-card__img {
  width: 88px;
  height: 88px;
  border-radius: 8px;
  object-fit: cover;
  background: #f0f2f5;
}

.product-card__tag {
  position: absolute;
  left: 4px;
  top: 4px;
  transform: scale(0.85);
  transform-origin: left top;
}

.product-card__body {
  flex: 1;
  min-width: 0;
}

.product-card__name {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-card__price {
  margin-top: 8px;
}

.product-card__price .final {
  color: #e4393c;
  font-size: 18px;
  font-weight: 700;
}

.product-card__price .origin {
  margin-left: 8px;
  color: #969799;
  font-size: 12px;
  text-decoration: line-through;
}

.product-card__subsidy {
  margin: 6px 0 8px;
  font-size: 12px;
  color: #07c160;
  font-weight: 600;
}

@media (min-width: 992px) {
  .card-block {
    margin-left: 0;
    margin-right: 0;
  }
}
</style>
