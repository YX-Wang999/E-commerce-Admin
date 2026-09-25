import { computed, onMounted, onUnmounted, ref } from 'vue'

/** Unified breakpoints aligned with Element Plus grid. */
export const BREAKPOINTS = {
  xs: 576,
  sm: 768,
  md: 992,
  lg: 1200,
  xl: 1920,
}

function readWidth() {
  return typeof window !== 'undefined' ? window.innerWidth : BREAKPOINTS.lg
}

/**
 * Reactive viewport helpers for layout, forms and dialogs.
 */
export function useResponsive() {
  const width = ref(readWidth())

  const isXs = computed(() => width.value < BREAKPOINTS.xs)
  const isMobile = computed(() => width.value < BREAKPOINTS.md)
  const isTablet = computed(() => width.value >= BREAKPOINTS.md && width.value < BREAKPOINTS.lg)
  const isDesktop = computed(() => width.value >= BREAKPOINTS.lg)
  const isCompactActions = computed(() => width.value < BREAKPOINTS.sm)

  const dialogWidth = computed(() => {
    if (width.value < BREAKPOINTS.xs) {
      return '95%'
    }
    if (width.value < BREAKPOINTS.md) {
      return '92%'
    }
    if (width.value < BREAKPOINTS.lg) {
      return '80%'
    }
    return '700px'
  })

  function updateWidth() {
    width.value = readWidth()
  }

  onMounted(() => {
    window.addEventListener('resize', updateWidth, { passive: true })
  })

  onUnmounted(() => {
    window.removeEventListener('resize', updateWidth)
  })

  return {
    width,
    isXs,
    isMobile,
    isTablet,
    isDesktop,
    isCompactActions,
    dialogWidth,
    updateWidth,
  }
}

/** Non-reactive width check for one-off usage. */
export function getDialogWidth(fallback = '700px') {
  const w = readWidth()
  if (w < BREAKPOINTS.xs) {
    return '95%'
  }
  if (w < BREAKPOINTS.md) {
    return '92%'
  }
  if (w < BREAKPOINTS.lg) {
    return '80%'
  }
  return fallback
}
