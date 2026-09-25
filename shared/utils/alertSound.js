/** Urgent triple-beep with AudioContext unlock for browser autoplay policies. */

let audioCtx = null
let unlockListenersAttached = false

function getAudioContext() {
  const AudioCtx = window.AudioContext || window.webkitAudioContext
  if (!AudioCtx) return null
  if (!audioCtx || audioCtx.state === 'closed') {
    audioCtx = new AudioCtx()
  }
  return audioCtx
}

export async function unlockAlertSound() {
  const ctx = getAudioContext()
  if (!ctx) return false
  if (ctx.state === 'running') return true
  try {
    await ctx.resume()
    return ctx.state === 'running'
  } catch {
    return false
  }
}

export function initAlertSoundUnlock() {
  if (unlockListenersAttached || typeof window === 'undefined') return
  unlockListenersAttached = true

  const events = ['pointerdown', 'keydown', 'touchstart', 'click']
  const tryUnlock = async () => {
    const ok = await unlockAlertSound()
    if (!ok) return
    events.forEach((eventName) => {
      window.removeEventListener(eventName, tryUnlock)
    })
  }

  events.forEach((eventName) => {
    window.addEventListener(eventName, tryUnlock, { passive: true })
  })
}

function scheduleBeeps(ctx) {
  const playBeep = (start, freq = 880) => {
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'square'
    osc.frequency.value = freq
    gain.gain.value = 0.14
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start(start)
    osc.stop(start + 0.14)
  }
  playBeep(ctx.currentTime, 880)
  playBeep(ctx.currentTime + 0.2, 988)
  playBeep(ctx.currentTime + 0.4, 880)
}

export async function playUrgentAlertSound() {
  const ctx = getAudioContext()
  if (!ctx) return false

  try {
    if (ctx.state === 'suspended') {
      await ctx.resume()
    }
    if (ctx.state !== 'running') return false
    scheduleBeeps(ctx)
    return true
  } catch {
    return false
  }
}
