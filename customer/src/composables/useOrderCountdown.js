import { computed, onBeforeUnmount, onMounted, ref, unref, watch } from 'vue'

function parseExpiresAt(value) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function formatCountdown(ms) {
  if (ms <= 0) return '00:00'
  const totalSeconds = Math.floor(ms / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

export function useOrderCountdown(expiresAtRef) {
  const remainingMs = ref(0)
  let timer = null

  function tick() {
    const expiresAt = parseExpiresAt(unref(expiresAtRef))
    if (!expiresAt) {
      remainingMs.value = 0
      return
    }
    remainingMs.value = Math.max(0, expiresAt.getTime() - Date.now())
  }

  function start() {
    stop()
    tick()
    timer = window.setInterval(tick, 1000)
  }

  function stop() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  watch(
    () => unref(expiresAtRef),
    () => start(),
    { immediate: true },
  )

  onMounted(start)
  onBeforeUnmount(stop)

  const countdownText = computed(() => formatCountdown(remainingMs.value))
  const isExpired = computed(() => {
    if (!hasDeadline.value) return false
    return remainingMs.value <= 0
  })
  const hasDeadline = computed(() => Boolean(parseExpiresAt(unref(expiresAtRef))))

  return {
    countdownText,
    isExpired,
    hasDeadline,
    remainingMs,
  }
}
