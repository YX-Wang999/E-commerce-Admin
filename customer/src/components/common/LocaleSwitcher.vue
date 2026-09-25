<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { LOCALE_OPTIONS, setLocale, getLocale } from '@/i18n'

const { t } = useI18n()

const currentLocale = computed(() => getLocale())

const options = computed(() =>
  LOCALE_OPTIONS.map((item) => ({
    value: item.value,
    label: t(item.labelKey),
  })),
)

function onChange(event) {
  setLocale(event.target.value)
}
</script>

<template>
  <label class="locale-switcher">
    <span class="locale-label">{{ t('locale.label') }}</span>
    <select class="locale-select" :value="currentLocale" @change="onChange">
      <option v-for="item in options" :key="item.value" :value="item.value">
        {{ item.label }}
      </option>
    </select>
  </label>
</template>

<style scoped>
.locale-switcher {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.locale-label {
  color: #999;
  font-size: 12px;
}
.locale-select {
  border: none;
  background: transparent;
  color: #666;
  font-size: 12px;
  cursor: pointer;
  outline: none;
}
.locale-select:hover {
  color: #e1251b;
}
</style>
