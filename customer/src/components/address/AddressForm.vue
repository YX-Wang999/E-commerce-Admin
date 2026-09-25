<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatRegionText, getAreaList } from '@/utils/region'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  initialData: {
    type: Object,
    default: null,
  },
  saving: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'submit', 'cancel'])

const { t } = useI18n()
const formRef = ref(null)
const showAreaPicker = ref(false)

const form = reactive({
  name: '',
  phone: '',
  province: '',
  city: '',
  district: '',
  detail: '',
  is_default: false,
})

const regionText = computed(() => formatRegionText(form.province, form.city, form.district))

const areaList = getAreaList()

const rules = computed(() => ({
  name: [
    { required: true, message: t('address.nameRequired') },
    { pattern: /^.{1,20}$/, message: t('address.nameMax') },
  ],
  phone: [
    { required: true, message: t('address.phoneRequired') },
    { pattern: /^1[3-9]\d{9}$/, message: t('address.phoneInvalid') },
  ],
  region: [
    {
      validator: () => Boolean(form.province && form.city && form.district),
      message: t('address.regionRequired'),
    },
  ],
  detail: [
    { required: true, message: t('address.detailRequired') },
    { pattern: /^.{5,100}$/, message: t('address.detailLength') },
  ],
}))

function resetForm(data = null) {
  Object.assign(form, {
    name: data?.name || '',
    phone: data?.phone || '',
    province: data?.province || '',
    city: data?.city || '',
    district: data?.district || '',
    detail: data?.detail || '',
    is_default: Boolean(data?.is_default),
  })
}

function optionText(option) {
  if (!option) return ''
  return option.text || option.name || ''
}

function onAreaConfirm(payload) {
  const options = payload?.selectedOptions || []
  form.province = optionText(options[0])
  form.city = optionText(options[1])
  form.district = optionText(options[2])
  showAreaPicker.value = false
  formRef.value?.validate('region').catch(() => {})
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  emit('submit', { ...form })
}

function handleCancel() {
  emit('cancel')
  emit('update:modelValue', false)
}

watch(
  () => props.modelValue,
  (visible) => {
    if (visible) {
      resetForm(props.initialData)
    }
  },
)

watch(
  () => props.initialData,
  (data) => {
    if (props.modelValue) {
      resetForm(data)
    }
  },
)
</script>

<template>
  <van-popup
    :show="modelValue"
    round
    position="bottom"
    :style="{ height: '92vh' }"
    @update:show="emit('update:modelValue', $event)"
  >
    <div class="address-form">
      <div class="form-header">
        <button type="button" class="header-btn" @click="handleCancel">{{ t('common.cancel') }}</button>
        <div class="form-title">{{ initialData?.id ? t('address.edit') : t('address.add') }}</div>
        <button type="button" class="header-btn primary" :disabled="saving" @click="handleSubmit">
          {{ t('address.save') }}
        </button>
      </div>

      <van-form ref="formRef" class="form-body">
        <van-cell-group inset>
          <van-field
            v-model="form.name"
            name="name"
            :label="t('address.name')"
            :placeholder="t('address.namePlaceholder')"
            maxlength="20"
            :rules="rules.name"
          />
          <van-field
            v-model="form.phone"
            name="phone"
            type="tel"
            maxlength="11"
            :label="t('address.phone')"
            :placeholder="t('address.phonePlaceholder')"
            :rules="rules.phone"
          />
          <van-field
            :model-value="regionText"
            name="region"
            is-link
            readonly
            :label="t('address.region')"
            :placeholder="t('address.regionPlaceholder')"
            :rules="rules.region"
            @click="showAreaPicker = true"
          />
          <van-field
            v-model="form.detail"
            name="detail"
            type="textarea"
            rows="2"
            autosize
            maxlength="100"
            show-word-limit
            :label="t('address.detail')"
            :placeholder="t('address.detailPlaceholder')"
            :rules="rules.detail"
          />
          <van-cell :title="t('address.setDefault')">
            <template #right-icon>
              <van-switch v-model="form.is_default" size="20" />
            </template>
          </van-cell>
        </van-cell-group>

        <p class="form-tip">{{ t('address.formTip') }}</p>
      </van-form>

      <div class="form-footer">
        <van-button type="primary" block round :loading="saving" @click="handleSubmit">
          {{ t('address.save') }}
        </van-button>
      </div>
    </div>
  </van-popup>

  <van-popup v-model:show="showAreaPicker" round position="bottom" teleport="body">
    <van-area
      :area-list="areaList"
      :columns-num="3"
      :title="t('address.region')"
      :confirm-button-text="t('common.confirm')"
      :cancel-button-text="t('common.cancel')"
      @confirm="onAreaConfirm"
      @cancel="showAreaPicker = false"
    />
  </van-popup>
</template>

<style scoped>
.address-form {
  display: flex;
  flex-direction: column;
  height: 92vh;
  background: #f5f6fa;
}

.form-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.form-title {
  font-size: 16px;
  font-weight: 600;
  color: #323233;
}

.header-btn {
  border: none;
  background: none;
  padding: 0;
  font-size: 14px;
  color: #969799;
  cursor: pointer;
}

.header-btn.primary {
  color: #ee0a24;
  font-weight: 600;
}

.header-btn:disabled {
  opacity: 0.5;
}

.form-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 0;
}

.form-tip {
  margin: 12px 16px 0;
  font-size: 12px;
  line-height: 1.5;
  color: #969799;
}

.form-footer {
  flex-shrink: 0;
  padding: 12px 16px 16px;
  background: #fff;
  border-top: 1px solid #f0f0f0;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.04);
}
</style>
