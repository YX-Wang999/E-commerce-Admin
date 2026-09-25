import { ref } from 'vue'

/**
 * 首页频道横向滑动手势：左滑下一频道，右滑上一频道。
 */
export function useChannelSwipe({ channels, activeChannel, onChange }) {
  const startX = ref(0)
  const startY = ref(0)
  const tracking = ref(false)

  const SWIPE_THRESHOLD = 48

  function channelIndex() {
    return channels.findIndex((tab) => tab.key === activeChannel.value)
  }

  function onTouchStart(event) {
    if (!event.touches?.length) return
    const touch = event.touches[0]
    startX.value = touch.clientX
    startY.value = touch.clientY
    tracking.value = true
  }

  function onTouchEnd(event) {
    if (!tracking.value || !event.changedTouches?.length) return
    tracking.value = false

    const touch = event.changedTouches[0]
    const deltaX = touch.clientX - startX.value
    const deltaY = touch.clientY - startY.value

    if (Math.abs(deltaX) < SWIPE_THRESHOLD) return
    if (Math.abs(deltaX) < Math.abs(deltaY) * 1.2) return

    const index = channelIndex()
    if (index < 0) return

    if (deltaX < 0 && index < channels.length - 1) {
      onChange(channels[index + 1].key)
      return
    }
    if (deltaX > 0 && index > 0) {
      onChange(channels[index - 1].key)
    }
  }

  function onTouchCancel() {
    tracking.value = false
  }

  return {
    onTouchStart,
    onTouchEnd,
    onTouchCancel,
  }
}
