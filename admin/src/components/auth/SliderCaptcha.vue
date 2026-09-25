<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import SlideVerify from 'vue3-slide-verify'
import 'vue3-slide-verify/dist/style.css'
import { verifyCaptcha } from '@/api/auth'

const props = defineProps({
  captchaId: {
    type: String,
    default: '',
  },
  background: {
    type: String,
    default: '',
  },
  offset: {
    type: Number,
    default: 0,
  },
  width: {
    type: Number,
    default: 278,
  },
  height: {
    type: Number,
    default: 155,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['success', 'fail', 'refresh'])

const { t } = useI18n()

const slideRef = ref(null)
const verifying = ref(false)

const puzzleImages = computed(() => (props.background ? [props.background] : []))

const sliderText = computed(() => {
  if (props.loading) {
    return t('login.sliderLoading')
  }
  return t('login.sliderHint')
})

const canInteract = computed(() => !props.loading && !props.disabled && !verifying.value)

function notifyFail(message = t('login.sliderRetry')) {
  ElMessage.warning({ message, duration: 2500 })
}

async function handleSuccess({ left }) {
  const captchaId = props.captchaId
  const expectedOffset = props.offset
  if (!canInteract.value || !captchaId || !expectedOffset) {
    return
  }

  // 组件 @success 表示拼图 left 已与 blockX(=expectedOffset) 对齐；提交服务端记录的 x 避免舍入误差
  const roundedLeft = Math.round(Number(left))
  const offsetToSend =
    Math.abs(roundedLeft - expectedOffset) <= 5 ? expectedOffset : roundedLeft

  verifying.value = true
  try {
    const res = await verifyCaptcha({
      captcha_id: captchaId,
      offset: offsetToSend,
    })
    if (res?.code !== 0) {
      throw res
    }
    emit('success', { captchaId, offset: offsetToSend })
  } catch (error) {
    notifyFail(t('login.captchaInvalid'))
    emit('fail', error)
    emit('refresh')
  } finally {
    verifying.value = false
  }
}

function handleFail() {
  notifyFail()
  emit('fail')
}

function handleAgain() {
  notifyFail()
  emit('fail')
}

function handleRefresh() {
  emit('refresh')
}
</script>

<template>
  <div
    class="slider-captcha"
    :class="{ 'slider-captcha--disabled': !canInteract }"
    :style="{ width: `${width}px` }"
  >
    <SlideVerify
      v-if="background && offset > 0"
      ref="slideRef"
      :key="captchaId"
      :w="width"
      :h="height"
      :l="42"
      :r="9"
      :offset="offset"
      :imgs="puzzleImages"
      :slider-text="sliderText"
      :accuracy="5"
      :show="true"
      @success="handleSuccess"
      @fail="handleFail"
      @again="handleAgain"
      @refresh="handleRefresh"
    />
    <div v-else class="slider-captcha__placeholder">{{ sliderText }}</div>
  </div>
</template>

<style scoped>
.slider-captcha {
  margin: 0 auto;
}

.slider-captcha--disabled {
  opacity: 0.55;
  pointer-events: none;
}

.slider-captcha__placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 155px;
  border: 2px solid #409eff;
  border-radius: 8px;
  background: #eef1f6;
  color: #606266;
  font-size: 13px;
}

.slider-captcha :deep(.slide-verify) {
  border: 2px solid #409eff;
  border-radius: 8px;
  overflow: hidden;
}

.slider-captcha :deep(.slide-verify-block) {
  border-radius: 4px;
  box-shadow: 0 0 8px rgba(0, 0, 0, 0.35);
}

.slider-captcha :deep(.slide-verify-slider-text) {
  color: #606266 !important;
}
</style>
