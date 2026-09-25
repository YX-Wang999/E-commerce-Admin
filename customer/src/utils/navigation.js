/** Safe back navigation with home fallback. */
export function navigateBack(router, fallback = { name: 'Home' }) {
  if (typeof window !== 'undefined' && window.history.state?.back) {
    router.back()
    return
  }
  router.push(fallback)
}
