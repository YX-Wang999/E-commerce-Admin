<script setup>
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const { t } = useI18n()

function goCouponCenter() {
  router.push({ name: 'CouponCenter' })
}
</script>

<template>
  <div class="billion-panel">
    <div class="billion-header">
      <span class="billion-header__name">{{ t('home.billionSubsidy') }}</span>
      <span class="billion-header__tip">{{ t('home.billionSubsidyDesc') }}</span>
    </div>

    <div class="billion-card promo-card" @click="goCouponCenter">
      <div class="promo-card__title">{{ t('home.billionSubsidy') }}</div>
      <p class="promo-card__desc">{{ t('home.billionSubsidyDesc') }}</p>
      <span class="promo-card__btn">{{ t('home.claimNow') }}</span>
    </div>
  </div>
</template>

<style scoped>
.billion-panel {
  padding: 8px 12px 16px;
}

.billion-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 10px;
  padding: 10px 12px;
  background: #fff;
  border-radius: 8px;
}

.billion-header__name {
  font-size: 16px;
  font-weight: 700;
  color: #e4393c;
}

.billion-header__tip {
  font-size: 12px;
  color: #969799;
}

.billion-card {
  padding: 16px;
  background: #fff;
  border-radius: 12px;
}

.promo-card {
  background: linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%);
  color: #fff;
  cursor: pointer;
}

.promo-card__title {
  font-size: 18px;
  font-weight: 700;
}

.promo-card__desc {
  margin: 6px 0 12px;
  font-size: 13px;
  opacity: 0.92;
}

.promo-card__btn {
  display: inline-block;
  padding: 6px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.22);
  font-size: 13px;
  font-weight: 600;
}
</style>
