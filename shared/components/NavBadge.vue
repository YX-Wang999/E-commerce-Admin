<script setup>
import { computed } from 'vue'

const props = defineProps({
  count: {
    type: Number,
    default: 0,
  },
  max: {
    type: Number,
    default: 99,
  },
  dot: {
    type: Boolean,
    default: false,
  },
})

const display = computed(() => {
  if (!props.count || props.count <= 0) return ''
  if (props.dot) return ''
  return props.count > props.max ? `${props.max}+` : String(props.count)
})

const showBadge = computed(() => props.dot ? props.count > 0 : Boolean(display.value))
</script>

<template>
  <span class="nav-badge-wrap">
    <slot />
    <span
      v-if="showBadge"
      class="nav-badge"
      :class="{ 'nav-badge--dot': dot }"
      :aria-label="dot ? '未读' : display"
    >
      <template v-if="!dot">{{ display }}</template>
    </span>
  </span>
</template>

<style scoped>
.nav-badge-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.nav-badge {
  position: absolute;
  top: -4px;
  right: -8px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 999px;
  background: #ee0a24;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  line-height: 16px;
  text-align: center;
  box-sizing: border-box;
  pointer-events: none;
}

.nav-badge--dot {
  min-width: 8px;
  width: 8px;
  height: 8px;
  padding: 0;
  top: -2px;
  right: -2px;
}
</style>
