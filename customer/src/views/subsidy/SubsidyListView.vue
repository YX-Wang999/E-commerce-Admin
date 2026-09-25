<script setup>
import HomeSubsidyPanel from '@/components/home/HomeSubsidyPanel.vue'
</script>

<template>
  <div class="subsidy-page">
    <HomeSubsidyPanel />
  </div>
</template>

<style scoped>
.subsidy-page {
  min-height: 100%;
  background: #f5f6fa;
}

@media (min-width: 992px) {
  .subsidy-page {
    max-width: 1190px;
    margin: 0 auto;
    padding: 16px 8px 24px;
  }
}
</style>
