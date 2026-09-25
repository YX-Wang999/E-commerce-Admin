<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showToast } from 'vant'
import { getMyFeedbacks, submitFeedback } from '@/api/feedback'
import { resolveErrorMessage } from '@/utils/feedback'

const router = useRouter()
const { t } = useI18n()

const loading = ref(true)
const submitting = ref(false)
const showTypePicker = ref(false)
const items = ref([])
const content = ref('')
const feedbackType = ref('suggestion')

const typeOptions = [
  { value: 'suggestion', labelKey: 'suggestion.typeSuggestion' },
  { value: 'inquiry', labelKey: 'suggestion.typeInquiry' },
  { value: 'complaint', labelKey: 'suggestion.typeComplaint' },
  { value: 'after_sales', labelKey: 'suggestion.typeAfterSales' },
]

const typeLabel = ref(t('suggestion.typeSuggestion'))

function formatTime(value) {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

function statusLabel(status) {
  const map = {
    pending: 'suggestion.statusPending',
    processing: 'suggestion.statusProcessing',
    done: 'suggestion.statusDone',
    closed: 'suggestion.statusClosed',
  }
  return t(map[status] || 'suggestion.statusPending')
}

function onTypeConfirm({ selectedOptions }) {
  const picked = selectedOptions?.[0]
  if (picked) {
    feedbackType.value = picked.value
    typeLabel.value = picked.text
  }
  showTypePicker.value = false
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getMyFeedbacks()
    items.value = res.data || []
  } catch (error) {
    showToast(resolveErrorMessage(error, 'suggestion.loadFailed'))
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  const text = content.value.trim()
  if (!text) {
    showToast(t('suggestion.contentRequired'))
    return
  }
  submitting.value = true
  try {
    await submitFeedback({
      feedback_type: feedbackType.value,
      content: text,
    })
    content.value = ''
    showToast(t('suggestion.submitSuccess'))
    await fetchList()
  } catch (error) {
    showToast(resolveErrorMessage(error, 'suggestion.submitFailed'))
  } finally {
    submitting.value = false
  }
}

onMounted(fetchList)
</script>

<template>
  <div class="suggestion-page">
    <van-nav-bar
      :title="t('suggestion.title')"
      left-arrow
      fixed
      placeholder
      @click-left="router.back()"
    />

    <div class="form-card">
      <div class="section-title">{{ t('suggestion.submitTitle') }}</div>
      <van-field
        is-link
        readonly
        :label="t('suggestion.typeLabel')"
        :model-value="typeLabel"
        @click="showTypePicker = true"
      />
      <van-field
        v-model="content"
        rows="4"
        autosize
        type="textarea"
        maxlength="500"
        show-word-limit
        :label="t('suggestion.contentLabel')"
        :placeholder="t('suggestion.contentPlaceholder')"
      />
      <van-button type="primary" block round :loading="submitting" @click="handleSubmit">
        {{ t('suggestion.submit') }}
      </van-button>
    </div>

    <div class="section-title list-title">{{ t('suggestion.historyTitle') }}</div>
    <van-loading v-if="loading" class="page-loading" vertical>{{ t('common.loading') }}</van-loading>
    <van-empty v-else-if="!items.length" :description="t('suggestion.empty')" />
    <van-cell-group v-else inset>
      <van-cell
        v-for="item in items"
        :key="item.id"
        :title="item.feedback_type_label || item.feedback_type"
        :label="`${item.content}\n${formatTime(item.created_at)}`"
      >
        <template #value>
          <div class="item-meta">
            <van-tag :type="item.status === 'done' ? 'success' : 'primary'" plain size="medium">
              {{ statusLabel(item.status) }}
            </van-tag>
            <div v-if="item.handler_remark" class="reply-text">
              {{ t('suggestion.replyPrefix') }}{{ item.handler_remark }}
            </div>
          </div>
        </template>
      </van-cell>
    </van-cell-group>

    <van-popup v-model:show="showTypePicker" position="bottom" round>
      <van-picker
        :columns="typeOptions.map((item) => ({ text: t(item.labelKey), value: item.value }))"
        @confirm="onTypeConfirm"
        @cancel="showTypePicker = false"
      />
    </van-popup>
  </div>
</template>

<style scoped>
.suggestion-page {
  min-height: 100vh;
  background: #f5f6fa;
  padding-bottom: 24px;
}

.form-card {
  margin: 12px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #323233;
  margin-bottom: 12px;
}

.list-title {
  margin: 8px 16px 12px;
}

.page-loading {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.item-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  max-width: 160px;
}

.reply-text {
  font-size: 12px;
  color: #646566;
  line-height: 1.5;
  text-align: right;
  word-break: break-word;
}
</style>
