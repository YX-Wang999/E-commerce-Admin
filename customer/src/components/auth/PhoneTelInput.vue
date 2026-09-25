<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import VueTelNumInput from 'vue-tel-num-input'
import 'vue-tel-num-input/style.css'
import 'vue-tel-num-input/flags.css'
import { parsePhoneNumberFromString } from 'libphonenumber-js'
import { telModelToE164 } from '@/utils/phone'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  defaultCountryCode: {
    type: String,
    default: 'CN',
  },
  placeholder: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue'])

const { t } = useI18n()
const telModel = ref({})
const mountKey = ref(0)

const inputPlaceholder = computed(() => props.placeholder || t('auth.phonePlaceholder'))

const initialValue = computed(() => {
  const phone = props.modelValue?.trim()
  if (!phone) return ''
  const parsed = parsePhoneNumberFromString(phone)
  if (parsed?.isValid()) return parsed.formatNational()
  return phone
})

watch(
  telModel,
  (val) => {
    emit('update:modelValue', telModelToE164(val))
  },
  { deep: true },
)

watch(
  () => props.modelValue,
  (phone, prev) => {
    const next = phone?.trim() || ''
    const current = telModelToE164(telModel.value)
    if (next && next !== current && !prev) {
      mountKey.value += 1
    }
  },
)
</script>

<template>
  <VueTelNumInput
    :key="mountKey"
    v-model="telModel"
    disable-sizing
    :default-country-code="defaultCountryCode"
    :international="false"
    :initial-value="initialValue"
    :placeholder="inputPlaceholder"
    :prefix="{ hideCountryName: true }"
    class="phone-tel-input"
  />
</template>

<style scoped>
.phone-tel-input {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  --tel-input-height: 36px;
  --tel-input-font-size: 14px;
  --tel-input-padding-x: 10px;
  --tel-input-prefix-padding-x: 8px;
  --tel-input-border-radius: 6px;
  --tel-input-input-width: 100%;
  --tel-input-icon-size: 12px;
  --tel-item-padding-x: 10px;
}

:deep(.tel-num-input) {
  width: 100%;
  max-width: 100%;
  min-width: 0;
}

:deep(.tel-num-input__head) {
  display: flex;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

:deep(.tel-num-input__head .prefix-container) {
  flex: 0 0 auto;
  max-width: 96px;
  padding-left: 8px;
  padding-right: 8px;
  gap: 4px;
  font-size: 13px;
}

:deep(.tel-num-input__head .prefix-container .emoji) {
  font-size: 16px;
  line-height: 1;
}

:deep(.tel-num-input__head input) {
  flex: 1 1 0;
  width: 0 !important;
  min-width: 0;
  max-width: 100%;
}

:deep(.tel-num-input__body) {
  z-index: 20;
  left: 0;
  right: 0;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}
</style>
