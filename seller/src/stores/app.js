import { defineStore } from 'pinia'
import { ref } from 'vue'

const MOBILE_BREAKPOINT = 768

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const isMobile = ref(false)

  function applyViewport(width = window.innerWidth) {
    isMobile.value = width <= MOBILE_BREAKPOINT
    if (isMobile.value) {
      sidebarCollapsed.value = true
    }
  }

  function initViewport() {
    applyViewport(window.innerWidth)
    window.addEventListener('resize', () => applyViewport(window.innerWidth), { passive: true })
  }

  function toggleSidebar() {
    if (isMobile.value) {
      return
    }
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  return {
    sidebarCollapsed,
    isMobile,
    applyViewport,
    initViewport,
    toggleSidebar,
  }
})
