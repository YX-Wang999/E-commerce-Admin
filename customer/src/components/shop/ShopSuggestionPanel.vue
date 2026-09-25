<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showToast } from 'vant'
import { submitFeedback } from '@/api/feedback'
import { resolveErrorMessage } from '@/utils/feedback'
import { requireLogin } from '@/stores/loginGate'

const props = defineProps({
  tenantId: { type: Number, required: true },
  redirectPath: { type: String, default: '' },
})

const router = useRouter()
const { t } = useI18n()

const showSheet = ref(false)
const content = ref('')
const submitting = ref(false)

async function handleSubmit() {
  const text = content.value.trim()
  if (!text) {
    showToast(t('suggestion.contentRequired'))
    return
  }
  try {
    await requireLogin({ redirect: props.redirectPath })
  } catch {
    return
  }
  submitting.value = true
  try {
    await submitFeedback({
      feedback_type: 'suggestion',
      content: text,
      tenant_id: props.tenantId,
    })
    content.value = ''
    showSheet.value = false
    showToast(t('shop.suggestionSuccess'))
  } catch (error) {
    showToast(resolveErrorMessage(error, 'suggestion.submitFailed'))
  } finally {
    submitting.value = false
  }
}

function goPlatformSuggestion() {
  router.push({ name: 'Suggestions' })
}
</script>

<template>
  <div class="action-card">
    <div class="action-title">{{ t('shop.submitSuggestion') }}</div>
    <p class="action-desc">{{ t('shop.suggestionDesc') }}</p>
    <van-button type="primary" block round icon="edit" @click="showSheet = true">
      {{ t('shop.submitSuggestion') }}
    </van-button>
    <button type="button" class="platform-link" @click="goPlatformSuggestion">
      {{ t('shop.platformSuggestionShort') }}
    </button>

    <van-popup v-model:show="showSheet" position="bottom" round safe-area-inset-bottom>
      <div class="sheet-body">
        <div class="sheet-title">{{ t('shop.submitSuggestion') }}</div>
        <van-field
          v-model="content"
          rows="4"
          autosize
          type="textarea"
          maxlength="500"
          show-word-limit
          :placeholder="t('shop.suggestionInputPlaceholder')"
        />
        <van-button type="primary" block round :loading="submitting" @click="handleSubmit">
          {{ t('suggestion.submit') }}
        </van-button>
      </div>
    </van-popup>
  </div>
</template>

<style scoped>
.action-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px;
}

.action-title {
  font-size: 15px;
  font-weight: 600;
  color: #323233;
}

.action-desc {
  margin: 8px 0 12px;
  font-size: 12px;
  line-height: 1.5;
  color: #969799;
  min-height: 36px;
}

.platform-link {
  display: block;
  width: 100%;
  margin-top: 10px;
  border: none;
  background: transparent;
  color: #1989fa;
  font-size: 12px;
  text-align: center;
  cursor: pointer;
}

.sheet-body {
  padding: 16px 16px 24px;
}

.sheet-title {
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
  text-align: center;
}
</style>
