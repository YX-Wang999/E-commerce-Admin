<script setup>
import PhoneTelInput from '@/components/auth/PhoneTelInput.vue'

defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  label: {
    type: String,
    default: '',
  },
  name: {
    type: String,
    default: 'phone',
  },
  rules: {
    type: Array,
    default: () => [],
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

defineEmits(['update:modelValue'])
</script>

<template>
  <van-field
    :model-value="modelValue"
    :name="name"
    class="auth-phone-field"
    label-align="top"
    :label="label"
    :rules="rules"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <template #input>
      <PhoneTelInput
        :model-value="modelValue"
        :default-country-code="defaultCountryCode"
        :placeholder="placeholder"
        @update:model-value="$emit('update:modelValue', $event)"
      />
    </template>
  </van-field>
</template>

<style scoped>
.auth-phone-field :deep(.van-field__body) {
  width: 100%;
  min-width: 0;
}

.auth-phone-field :deep(.van-field__control) {
  width: 100%;
  min-width: 0;
}
</style>
