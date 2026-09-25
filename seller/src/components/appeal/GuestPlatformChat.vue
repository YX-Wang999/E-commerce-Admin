<script setup>
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getAppealChatMessages, sendAppealChatMessage } from '@/api/tenant'
import { formatChatTime } from '@/utils/websocket'

const props = defineProps({
  account: { type: String, required: true },
  password: { type: String, required: true },
  conversationId: { type: Number, required: true },
  merchantUserId: { type: Number, default: null },
})

const { t } = useI18n()
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const loading = ref(false)
const messageListRef = ref(null)
let pollTimer = null

async function scrollToBottom() {
  await nextTick()
  const el = messageListRef.value
  if (el) {
    el.scrollTop = el.scrollHeight
  }
}

async function fetchMessages(silent = false) {
  if (!props.conversationId) return
  if (!silent) loading.value = true
  try {
    const res = await getAppealChatMessages({
      account: props.account,
      password: props.password,
      conversation_id: props.conversationId,
    })
    const next = res.data || []
    const changed = next.length !== messages.value.length
      || (next.length && next[next.length - 1]?.id !== messages.value[messages.value.length - 1]?.id)
    messages.value = next
    if (changed) {
      await scrollToBottom()
    }
  } catch (error) {
    if (!silent) {
      ElMessage.error(error?.message || t('seller.appealChatLoadFailed'))
    }
  } finally {
    if (!silent) loading.value = false
  }
}

async function handleSend() {
  const content = inputText.value.trim()
  if (!content || sending.value) return
  sending.value = true
  try {
    await sendAppealChatMessage({
      account: props.account,
      password: props.password,
      conversation_id: props.conversationId,
      content,
    })
    inputText.value = ''
    await fetchMessages(true)
  } catch (error) {
    ElMessage.error(error?.message || t('seller.appealChatSendFailed'))
  } finally {
    sending.value = false
  }
}

function isMerchantMessage(msg) {
  if (msg.is_platform_staff === false && (msg.is_staff || msg.sender_type === 'staff')) {
    return true
  }
  if (props.merchantUserId && msg.sender === props.merchantUserId) {
    return true
  }
  return msg.sender_type === 'user'
}

watch(
  () => props.conversationId,
  () => {
    fetchMessages()
  },
)

onMounted(() => {
  fetchMessages()
  pollTimer = window.setInterval(() => fetchMessages(true), 4000)
})

onUnmounted(() => {
  if (pollTimer) {
    window.clearInterval(pollTimer)
  }
})
</script>

<template>
  <div class="guest-platform-chat">
    <p class="chat-tip">{{ t('seller.appealChatTip') }}</p>
    <div ref="messageListRef" v-loading="loading" class="message-list">
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="message-row"
        :class="isMerchantMessage(msg) ? 'is-merchant' : 'is-staff'"
      >
        <div class="bubble">
          <div v-if="msg.sender_name" class="sender">{{ msg.sender_name }}</div>
          <div>{{ msg.content }}</div>
          <div class="time">{{ formatChatTime(msg.created_at) }}</div>
        </div>
      </div>
      <el-empty v-if="!loading && !messages.length" :description="t('seller.appealChatEmpty')" />
    </div>
    <div class="composer">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="2"
        :placeholder="t('seller.appealChatPlaceholder')"
        @keyup.enter.ctrl="handleSend"
      />
      <el-button type="primary" :loading="sending" @click="handleSend">
        {{ t('seller.appealChatSend') }}
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.guest-platform-chat {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-tip {
  margin: 0;
  font-size: 13px;
  color: #909399;
}

.message-list {
  min-height: 220px;
  max-height: 320px;
  overflow-y: auto;
  padding: 12px;
  background: #f5f6fa;
  border-radius: 8px;
}

.message-row {
  display: flex;
  margin-bottom: 12px;
}

.message-row.is-merchant {
  justify-content: flex-end;
}

.message-row.is-staff,
.message-row:not(.is-merchant) {
  justify-content: flex-start;
}

.bubble {
  max-width: 82%;
  padding: 10px 12px;
  border-radius: 10px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  font-size: 14px;
  line-height: 1.5;
}

.message-row.is-merchant .bubble {
  background: #ecf5ff;
}

.sender {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.time {
  margin-top: 6px;
  font-size: 11px;
  color: #c0c4cc;
}

.composer {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.composer .el-button {
  flex-shrink: 0;
}
</style>
