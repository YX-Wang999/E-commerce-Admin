<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const pageTitle = computed(() => {
  const key = route.meta?.titleKey
  return key ? t(key) : t('common.developing')
})
</script>

<template>
  <div class="channel-placeholder">
    <h2>{{ pageTitle }}</h2>
    <p>{{ t('common.developing') }}</p>
    <van-button type="primary" plain round @click="router.push({ name: 'Home' })">
      {{ t('common.backHome') }}
    </van-button>
  </div>
</template>

<style scoped>
.channel-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 24px 24px;
  color: #969799;
  overscroll-behavior: contain;
}

.channel-placeholder h2 {
  margin: 0 0 12px;
  font-size: 22px;
  color: #323233;
}

.channel-placeholder p {
  margin: 0 0 24px;
  font-size: 14px;
}
</style>
