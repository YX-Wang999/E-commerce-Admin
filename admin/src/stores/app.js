import { defineStore } from 'pinia'
import { ref } from 'vue'
import { BREAKPOINTS } from '@/composables/useResponsive'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const mobileSidebarOpen = ref(false)
  const isMobile = ref(false)
  const isTablet = ref(false)
  const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : BREAKPOINTS.lg)
  const siteTitle = ref('Admin 管理系统')

  function applyViewport(width) {
    viewportWidth.value = width
    isMobile.value = width < BREAKPOINTS.md
    isTablet.value = width >= BREAKPOINTS.md && width < BREAKPOINTS.lg

    if (isMobile.value) {
      mobileSidebarOpen.value = false
      sidebarCollapsed.value = true
      return
    }

    mobileSidebarOpen.value = false
    if (isTablet.value) {
      sidebarCollapsed.value = true
      return
    }

    sidebarCollapsed.value = false
  }

  function initViewport() {
    applyViewport(window.innerWidth)
  }

  function toggleSidebar() {
    if (isMobile.value) {
      mobileSidebarOpen.value = !mobileSidebarOpen.value
      return
    }
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function closeMobileSidebar() {
    mobileSidebarOpen.value = false
  }

  function setSiteTitle(title) {
    siteTitle.value = title
  }

  return {
    sidebarCollapsed,
    mobileSidebarOpen,
    isMobile,
    isTablet,
    viewportWidth,
    siteTitle,
    initViewport,
    applyViewport,
    toggleSidebar,
    closeMobileSidebar,
    setSiteTitle,
  }
})
