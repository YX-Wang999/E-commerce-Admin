<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMediaQuery } from '@vueuse/core'
import { useScrollHeader } from '@shared/composables/useScrollHeader.js'
import { useHotReload } from '@/composables/useHotReload'
import HomeHeader from '@/components/layout/HomeHeader.vue'
import MobileTopBar from '@/components/layout/MobileTopBar.vue'
import SiteFooter from '@/components/layout/SiteFooter.vue'
import TabBar from '@/components/layout/TabBar.vue'

const MOBILE_TAB_ROUTES = new Set(['Home', 'Category', 'Notifications', 'Cart', 'Profile'])

const router = useRouter()
const route = useRoute()
const searchKeyword = ref('')
const mainRef = ref(null)
const isMobile = useMediaQuery('(max-width: 768px)')

const showSiteChrome = computed(() => !route.matched.some((record) => record.meta.plainLayout))
const showDesktopChrome = computed(() => showSiteChrome.value && !isMobile.value)
const showMobileTabShell = computed(
  () => isMobile.value && showSiteChrome.value && MOBILE_TAB_ROUTES.has(String(route.name)),
)
const showMobileTopBar = computed(() => {
  if (!isMobile.value || !showSiteChrome.value || route.meta.plainLayout) return false
  if (route.meta.hideMobileTopBar) return false
  if (MOBILE_TAB_ROUTES.has(String(route.name))) return false
  return true
})

const usePageTransition = computed(
  () => showSiteChrome.value && !showMobileTabShell.value && String(route.name) !== 'Home',
)

const { headerVisible } = useScrollHeader(mainRef)

useHotReload()

function handleSearch(value) {
  const keyword = (value ?? searchKeyword.value ?? '').trim()
  router.push({
    name: 'Search',
    query: keyword ? { keyword } : {},
  })
}

onMounted(() => {
  if (mainRef.value && isMobile.value) {
    mainRef.value.scrollTop = 0
  }
})
</script>

<template>
  <div class="main-layout" :class="{ 'is-mobile-tab': showMobileTabShell }">
    <HomeHeader
      v-if="showDesktopChrome"
      v-model:keyword="searchKeyword"
      @search="handleSearch"
    />

    <MobileTopBar v-if="showMobileTopBar" :visible="headerVisible" />

    <main
      ref="mainRef"
      class="main-content"
      :class="{
        'main-content--mobile-tab': showMobileTabShell,
        'main-content--mobile-scroll': isMobile && showSiteChrome && !showMobileTabShell,
      }"
    >
      <router-view v-if="!usePageTransition" />
      <router-view v-else v-slot="{ Component }">
        <Transition name="page-fade" mode="out-in">
          <component :is="Component" :key="route.path" />
        </Transition>
      </router-view>
    </main>

    <SiteFooter v-if="showDesktopChrome" />

    <TabBar v-if="showMobileTabShell" />
  </div>
</template>

<style scoped>
.main-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg, #f5f5f5);
}

.main-layout.is-mobile-tab {
  height: 100vh;
  overflow: hidden;
}

.main-content {
  flex: 1;
  min-height: 0;
}

.main-content--mobile-tab {
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
  padding-bottom: calc(50px + env(safe-area-inset-bottom, 0px));
}

.main-content--mobile-scroll {
  overflow-y: auto;
  overscroll-behavior-y: contain;
  -webkit-overflow-scrolling: touch;
}
</style>
