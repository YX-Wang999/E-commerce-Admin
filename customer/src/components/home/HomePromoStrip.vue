<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getSeckillActivities, getSuperDiscountActive } from '@/api/promotion'
import { usePromoCountdown } from '@/composables/usePromoCountdown'
import { formatPrice } from '@/utils/product'

const emit = defineEmits(['open-billion', 'open-super', 'open-seckill'])

const { t } = useI18n()

const seckillActivity = ref(null)
const superDiscount = ref(null)
const loading = ref(true)

const seckillEndTime = computed(() => seckillActivity.value?.end_time || null)
const { countdownText } = usePromoCountdown(seckillEndTime)

const seckillLabel = computed(() => seckillActivity.value?.name || t('home.flashSale'))
const seckillPriceText = computed(() => {
  const price = seckillActivity.value?.seckill_price
  return price != null && price !== '' ? formatPrice(price) : ''
})

const amountText = computed(() => {
  const amount = superDiscount.value?.amount
  if (amount == null || amount === '') return ''
  return Number(amount).toFixed(Number(amount) % 1 === 0 ? 0 : 2)
})

const promoLines = computed(() => {
  const text = superDiscount.value?.promo_text || ''
  if (!text) return []
  return text.split(/\s+/).filter(Boolean).slice(0, 2)
})

async function fetchData() {
  loading.value = true
  try {
    const [seckillRes, discountRes] = await Promise.all([
      getSeckillActivities().catch(() => ({ data: [] })),
      getSuperDiscountActive().catch(() => ({ data: null })),
    ])
    const activities = seckillRes.data || []
    seckillActivity.value =
      activities.find((item) => item.phase === 'ongoing') || activities[0] || null
    superDiscount.value = discountRes.data || null
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<template>
  <section class="promo-strip card-block">
    <van-skeleton v-if="loading" :row="2" title />

    <div v-else class="strip-grid">
      <button type="button" class="promo-card promo-card--billion" @click="emit('open-billion')">
        <div class="promo-card__title">{{ t('home.billionSubsidy') }}</div>
        <div class="promo-card__desc">{{ t('home.billionSubsidyDesc') }}</div>
      </button>

      <button type="button" class="promo-card promo-card--super" @click="emit('open-super')">
        <div class="promo-card__head">
          <span aria-hidden="true">📣</span>
          <span>{{ superDiscount?.title || t('home.superDiscountTitle') }}</span>
        </div>
        <p v-for="(line, index) in promoLines" :key="`${line}-${index}`" class="promo-card__line">{{ line }}</p>
        <p v-if="!promoLines.length" class="promo-card__line">{{ t('home.superDiscountDefaultText') }}</p>
        <div v-if="amountText" class="promo-card__amount"><em>{{ amountText }}</em>￥</div>
      </button>

      <button type="button" class="promo-card promo-card--seckill" @click="emit('open-seckill')">
        <div class="promo-card__title">{{ seckillLabel }}</div>
        <div v-if="seckillPriceText" class="promo-card__price">{{ seckillPriceText }}</div>
        <div v-if="countdownText && countdownText !== '00:00:00'" class="promo-card__countdown">
          {{ countdownText }}
        </div>
      </button>
    </div>
  </section>
</template>

<style scoped>
.card-block {
  margin: 12px 12px 0;
  padding: 10px;
  background: #fff;
  border-radius: 12px;
}

.strip-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.promo-card {
  min-height: 88px;
  padding: 10px;
  border: none;
  border-radius: 10px;
  text-align: left;
  cursor: pointer;
}

.promo-card--billion {
  background: linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%);
  color: #fff;
}

.promo-card--super {
  background: linear-gradient(135deg, #fff7e6 0%, #ffe7ba 100%);
  color: #ad6800;
}

.promo-card--seckill {
  background: #fff5f5;
  color: #e4393c;
}

.promo-card__title {
  font-size: 13px;
  font-weight: 700;
  line-height: 1.3;
}

.promo-card__desc {
  margin-top: 4px;
  font-size: 11px;
  opacity: 0.92;
  line-height: 1.4;
}

.promo-card__head {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 700;
  color: #d46b08;
}

.promo-card__line {
  margin: 4px 0 0;
  font-size: 11px;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.promo-card__amount {
  margin-top: 6px;
  font-size: 11px;
  font-weight: 600;
  color: #d4380d;
}

.promo-card__amount em {
  font-style: normal;
  font-size: 16px;
  font-weight: 800;
}

.promo-card__price {
  margin-top: 4px;
  font-size: 12px;
  font-weight: 700;
}

.promo-card__countdown {
  margin-top: 4px;
  font-size: 11px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
</style>
