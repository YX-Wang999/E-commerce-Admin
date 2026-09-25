<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <div class="loading-wrap">
    <van-loading type="spinner" size="24px">{{ t('common.loading') }}</van-loading>
  </div>
</template>

<style scoped>
.loading-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}
</style>
