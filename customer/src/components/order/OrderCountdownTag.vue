<script setup>
import { computed, toRef } from 'vue'
import { useI18n } from 'vue-i18n'
import { useOrderCountdown } from '@/composables/useOrderCountdown'

const props = defineProps({
  expiresAt: { type: String, default: '' },
  status: { type: String, default: '' },
})

const { t } = useI18n()
const { countdownText, isExpired, hasDeadline } = useOrderCountdown(toRef(props, 'expiresAt'))

const visible = computed(
  () => props.status === 'pending' && hasDeadline.value && !isExpired.value,
)
</script>

<template>
  <span v-if="visible" class="countdown-tag">
    {{ t('order.payCountdown', { time: countdownText }) }}
  </span>
</template>

<style scoped>
.countdown-tag {
  display: inline-block;
  margin-top: 8px;
  padding: 2px 8px;
  font-size: 12px;
  color: #ed6a0c;
  background: #fff7e8;
  border-radius: 4px;
}
</style>
