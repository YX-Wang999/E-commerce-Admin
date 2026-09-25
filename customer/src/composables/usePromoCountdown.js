import { computed, onBeforeUnmount, onMounted, ref, unref, watch } from 'vue'

function parseTime(value) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function formatCountdown(ms) {
  if (ms <= 0) return '00:00:00'
  const totalSeconds = Math.floor(ms / 1000)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  return [hours, minutes, seconds]
    .map((part) => String(part).padStart(2, '0'))
    .join(':')
}

export function usePromoCountdown(endTimeRef) {
  const remainingMs = ref(0)
  let timer = null

  function tick() {
    const endTime = parseTime(unref(endTimeRef))
    if (!endTime) {
      remainingMs.value = 0
      return
    }
    remainingMs.value = Math.max(0, endTime.getTime() - Date.now())
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
    () => unref(endTimeRef),
    () => start(),
    { immediate: true },
  )

  onMounted(start)
  onBeforeUnmount(stop)

  const countdownText = computed(() => formatCountdown(remainingMs.value))
  const isExpired = computed(() => remainingMs.value <= 0)
  const hasDeadline = computed(() => Boolean(parseTime(unref(endTimeRef))))

  return {
    countdownText,
    isExpired,
    hasDeadline,
    remainingMs,
  }
}
