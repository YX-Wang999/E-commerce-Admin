<script setup>
import { useRouter } from 'vue-router'

defineProps({
  title: {
    type: String,
    required: true,
  },
})

const router = useRouter()

function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push({ name: 'Profile' })
  }
}
</script>

<template>
  <van-nav-bar
    :title="title"
    left-arrow
    fixed
    placeholder
    safe-area-inset-top
    class="sub-page-nav"
    @click-left="goBack"
  />
</template>

<style scoped>
.sub-page-nav {
  --van-nav-bar-background: #fff;
}
</style>
