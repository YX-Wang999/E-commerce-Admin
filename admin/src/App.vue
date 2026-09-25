<script setup>
import { computed } from 'vue'
import { useLocaleStore } from '@/stores/locale'

const localeStore = useLocaleStore()

const elementLocale = computed(() => localeStore.elementLocale)
</script>

<template>
  <el-config-provider :locale="elementLocale">
    <router-view />
  </el-config-provider>
</template>

<style>
html,
body,
#app {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
}
</style>
