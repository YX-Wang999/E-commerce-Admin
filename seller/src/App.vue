<script setup>
import { computed } from 'vue'
import { ElConfigProvider } from 'element-plus'
import { useLocaleStore } from '@/stores/locale'

const localeStore = useLocaleStore()
const elementLocale = computed(() => localeStore.elementLocale)
</script>

<template>
  <ElConfigProvider :locale="elementLocale">
    <router-view />
  </ElConfigProvider>
</template>
