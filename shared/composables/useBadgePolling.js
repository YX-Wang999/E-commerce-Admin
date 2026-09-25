/** Poll badge data only while WebSocket is disconnected (fallback). */

const DEFAULT_INTERVAL_MS = 30000

export function createBadgePolling({
  isConnected,
  pollFn,
  intervalMs = DEFAULT_INTERVAL_MS,
}) {
  let timer = null

  async function tick() {
    try {
      await pollFn()
    } catch {
      // ignore polling errors
    }
  }

  function start() {
    stop()
    void tick()
    timer = window.setInterval(tick, intervalMs)
  }

  function stop() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  return { start, stop, tick }
}
