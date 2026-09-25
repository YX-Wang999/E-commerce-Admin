import { onMounted, onUnmounted, ref } from 'vue'

/**
 * Hide header on scroll down, show on scroll up.
 * @param {import('vue').Ref<HTMLElement | null>} containerRef
 * @param {number} threshold
 */
export function useScrollHeader(containerRef, threshold = 8) {
  const headerVisible = ref(true)
  let lastScrollTop = 0

  function onScroll() {
    const el = containerRef.value
    if (!el) return

    const scrollTop = el.scrollTop
    if (scrollTop <= 0) {
      headerVisible.value = true
    } else if (scrollTop - lastScrollTop > threshold) {
      headerVisible.value = false
    } else if (lastScrollTop - scrollTop > threshold) {
      headerVisible.value = true
    }
    lastScrollTop = Math.max(0, scrollTop)
  }

  onMounted(() => {
    containerRef.value?.addEventListener('scroll', onScroll, { passive: true })
  })

  onUnmounted(() => {
    containerRef.value?.removeEventListener('scroll', onScroll)
  })

  return { headerVisible }
}
