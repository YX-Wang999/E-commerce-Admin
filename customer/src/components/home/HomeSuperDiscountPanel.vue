<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getSuperDiscountActive } from '@/api/promotion'

const router = useRouter()
const { t } = useI18n()

const loading = ref(true)
const superDiscount = ref(null)

const amountText = computed(() => {
  const amount = superDiscount.value?.amount
  if (amount == null || amount === '') return ''
  return Number(amount).toFixed(Number(amount) % 1 === 0 ? 0 : 2)
})

const promoLines = computed(() => {
  const text = superDiscount.value?.promo_text || ''
  if (!text) return []
  return text.split(/\s+/).filter(Boolean)
})

async function fetchData() {
  loading.value = true
  try {
    const res = await getSuperDiscountActive().catch(() => ({ data: null }))
    superDiscount.value = res.data || null
  } finally {
    loading.value = false
  }
}

function claimSuperDiscount() {
  const link = superDiscount.value?.link_url
  if (link) {
    if (link.startsWith('http')) {
      window.location.href = link
      return
    }
    router.push(link)
    return
  }
  router.push({ name: 'CouponCenter' })
}

onMounted(fetchData)
</script>

<template>
  <div class="super-panel">
    <div class="super-header">
      <span class="super-header__name">{{ t('home.superDiscountTitle') }}</span>
      <span class="super-header__tip">{{ t('home.superDiscountDefaultText') }}</span>
    </div>

    <van-skeleton v-if="loading" class="super-card" :row="3" title />

    <template v-else>
      <div v-if="superDiscount" class="super-card" @click="claimSuperDiscount">
        <div class="super-card__head">
          <span class="super-card__icon" aria-hidden="true">📣</span>
          <span class="super-card__title">{{ superDiscount.title || t('home.superDiscountTitle') }}</span>
        </div>
        <p v-for="(line, index) in promoLines" :key="`${line}-${index}`" class="super-card__line">
          {{ line }}
        </p>
        <p v-if="!promoLines.length" class="super-card__line">{{ t('home.superDiscountDefaultText') }}</p>
        <div class="super-card__action">
          <span v-if="amountText" class="super-card__amount"><em>{{ amountText }}</em>￥</span>
          <span class="super-card__btn">{{ superDiscount.button_text || t('home.claimNow') }}</span>
        </div>
      </div>

      <div v-else class="super-card super-card--empty">
        <p>{{ t('home.superDiscountEmpty') }}</p>
        <van-button size="small" round type="primary" @click="router.push({ name: 'CouponCenter' })">
          {{ t('home.goCouponCenter') }}
        </van-button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.super-panel {
  padding: 8px 12px 16px;
}

.super-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 10px;
  padding: 10px 12px;
  background: #fff;
  border-radius: 8px;
}

.super-header__name {
  font-size: 16px;
  font-weight: 700;
  color: #d46b08;
}

.super-header__tip {
  font-size: 12px;
  color: #969799;
}

.super-card {
  padding: 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, #fff7e6 0%, #ffe7ba 100%);
  cursor: pointer;
}

.super-card--empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  cursor: default;
  color: #969799;
  font-size: 14px;
}

.super-card__head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.super-card__icon {
  font-size: 18px;
  line-height: 1;
}

.super-card__title {
  font-size: 16px;
  font-weight: 700;
  color: #d46b08;
}

.super-card__line {
  margin: 0 0 4px;
  font-size: 13px;
  color: #ad6800;
  line-height: 1.5;
}

.super-card__action {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 12px;
}

.super-card__amount {
  font-size: 13px;
  color: #d4380d;
  font-weight: 600;
}

.super-card__amount em {
  font-style: normal;
  font-size: 22px;
  font-weight: 800;
}

.super-card__btn {
  padding: 6px 14px;
  border-radius: 999px;
  background: linear-gradient(90deg, #fa541c, #fa8c16);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
}
</style>
