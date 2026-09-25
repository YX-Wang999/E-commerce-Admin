<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  show: { type: Boolean, default: false },
  order: { type: Object, default: null },
  mode: { type: String, default: 'cancel' },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['update:show', 'confirm'])

const { t } = useI18n()

const reasonOptions = [
  { value: '不想要了', labelKey: 'order.cancelReasonNoWant' },
  { value: '信息填错了', labelKey: 'order.cancelReasonWrongInfo' },
  { value: '价格太贵了', labelKey: 'order.cancelReasonTooExpensive' },
  { value: '其他', labelKey: 'order.cancelReasonOther' },
]

const selectedReason = ref('不想要了')
const detail = ref('')

const visible = computed({
  get: () => props.show,
  set: (value) => emit('update:show', value),
})

const isOther = computed(() => selectedReason.value === '其他')

watch(
  () => props.show,
  (open) => {
    if (open) {
      selectedReason.value = '不想要了'
      detail.value = ''
    }
  },
)

function handleConfirm() {
  if (isOther.value && !detail.value.trim()) {
    return
  }
  emit('confirm', {
    reason: selectedReason.value,
    detail: isOther.value ? detail.value.trim() : detail.value.trim(),
  })
}
</script>

<template>
  <van-popup v-model:show="visible" round position="bottom" :style="{ maxHeight: '85vh' }">
    <div class="cancel-dialog">
      <div class="dialog-title">{{ t('order.cancelTitle') }}</div>
      <div v-if="order" class="order-summary">
        <div>{{ t('checkout.orderNo', { no: order.order_no }) }}</div>
        <div class="order-amount">
          {{ t('checkout.payAmount') }}：¥{{ Number(order.total_amount).toFixed(2) }}
        </div>
      </div>

      <div class="field-label">{{ t('order.cancelReasonLabel') }}</div>
      <van-radio-group v-model="selectedReason" class="reason-group">
        <van-radio v-for="item in reasonOptions" :key="item.value" :name="item.value">
          {{ t(item.labelKey) }}
        </van-radio>
      </van-radio-group>

      <van-field
        v-model="detail"
        rows="2"
        autosize
        type="textarea"
        :label="t('order.cancelDetailLabel')"
        :placeholder="isOther ? t('order.cancelDetailRequired') : t('order.cancelDetailPlaceholder')"
        maxlength="200"
        show-word-limit
        class="detail-field"
      />

      <div class="dialog-actions">
        <van-button block round @click="visible = false">{{ t('common.cancel') }}</van-button>
        <van-button
          block
          round
          type="danger"
          :loading="loading"
          :disabled="isOther && !detail.trim()"
          @click="handleConfirm"
        >
          {{ mode === 'apply' ? t('order.confirmApplyCancel') : t('order.confirmCancel') }}
        </van-button>
      </div>
    </div>
  </van-popup>
</template>

<style scoped>
.cancel-dialog {
  padding: 20px 16px calc(16px + env(safe-area-inset-bottom));
}

.dialog-title {
  font-size: 17px;
  font-weight: 600;
  text-align: center;
  margin-bottom: 16px;
}

.order-summary {
  padding: 12px;
  background: #f7f8fa;
  border-radius: 8px;
  font-size: 14px;
  color: #646566;
  line-height: 1.6;
}

.order-amount {
  margin-top: 4px;
  color: #323233;
  font-weight: 600;
}

.field-label {
  margin: 16px 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: #323233;
}

.reason-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-field {
  margin-top: 12px;
  padding: 0;
}

.dialog-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 20px;
}
</style>
