<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import {
  assignConversation,
  closeConversation,
  getChatConversations,
  getConversationMessages,
  openPlatformChat,
  sendConversationMessage,
} from '@/api/chat'
import { useAppStore } from '@/stores/app'
import { useChatBadgeStore } from '@/stores/chatBadge'
import { useChatWebSocket } from '@/composables/useChatWebSocket'
import { formatChatTime } from '@/utils/websocket'

const { t } = useI18n()
const route = useRoute()
const appStore = useAppStore()
const chatBadgeStore = useChatBadgeStore()
const loading = ref(false)
const conversations = ref([])
const selectedId = ref(null)
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const messageListRef = ref(null)

let listTimer = null

const selectedConversation = computed(() =>
  conversations.value.find((item) => item.id === selectedId.value) || null,
)

const conversationId = computed(() => selectedId.value)

const mobileShowChat = computed(() => appStore.isMobile && Boolean(selectedId.value))

const statusMap = computed(() => ({
  pending: { label: t('seller.statusPending'), type: 'warning' },
  active: { label: t('seller.statusActive'), type: 'success' },
  closed: { label: t('seller.statusClosed'), type: 'info' },
}))

function isPlatformChat(item) {
  return item?.conversation_type === 'b2p' || item?.conversation_type === 'p2b'
}

function messageRowClass(msg) {
  if (isPlatformChat(selectedConversation.value)) {
    return msg.is_platform_staff ? 'is-peer' : 'is-self'
  }
  return msg.is_staff ? 'is-self' : 'is-peer'
}

function conversationUnread(item) {
  return item.staff_unread_count || item.unread_count || 0
}

async function scrollToBottom() {
  await nextTick()
  const el = messageListRef.value
  if (el) el.scrollTop = el.scrollHeight
}

async function fetchConversations() {
  try {
    const res = await getChatConversations()
    conversations.value = res.data || []
    if (selectedId.value && !conversations.value.some((item) => item.id === selectedId.value)) {
      selectedId.value = null
      messages.value = []
    }
  } catch {
    // handled by interceptor
  }
}

async function fetchMessages() {
  if (!selectedId.value) {
    messages.value = []
    return
  }
  loading.value = true
  try {
    const res = await getConversationMessages(selectedId.value)
    messages.value = res.data || []
    await scrollToBottom()
    await fetchConversations()
  } finally {
    loading.value = false
  }
}

async function selectConversation(id) {
  selectedId.value = id
  await fetchMessages()
  await chatBadgeStore.refresh()
}

function backToList() {
  selectedId.value = null
  messages.value = []
}

async function handleOpenPlatformChat() {
  try {
    const res = await openPlatformChat()
    selectedId.value = res.data.id
    await fetchConversations()
    await fetchMessages()
    ElMessage.success(t('seller.chatConnectedPlatform'))
  } catch {
    // handled by interceptor
  }
}

async function handleAssign() {
  if (!selectedId.value) return
  try {
    await assignConversation(selectedId.value)
    ElMessage.success(t('seller.chatAssigned'))
    await fetchConversations()
    await fetchMessages()
  } catch {
    // handled
  }
}

async function handleClose() {
  if (!selectedId.value) return
  try {
    await closeConversation(selectedId.value)
    disconnect()
    selectedId.value = null
    messages.value = []
    ElMessage.success(t('seller.chatClosed'))
    await fetchConversations()
  } catch {
    // handled
  }
}

function appendMessage(message) {
  if (!message?.id || messages.value.some((item) => item.id === message.id)) return
  const tempIndex = messages.value.findIndex(
    (item) => String(item.id).startsWith('temp-') && item.content === message.content,
  )
  if (tempIndex >= 0) {
    messages.value.splice(tempIndex, 1, message)
  } else {
    messages.value.push(message)
  }
  scrollToBottom()
  fetchConversations()
  chatBadgeStore.refresh()
}

const { sendMessage, disconnect } = useChatWebSocket(conversationId, {
  onMessage(data) {
    appendMessage(data)
  },
  onError(message) {
    if (message) ElMessage.error(message)
  },
})

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || !selectedId.value || sending.value) return
  sending.value = true
  const tempId = `temp-${Date.now()}`
  messages.value.push({
    id: tempId,
    content: text,
    is_staff: true,
    is_platform_staff: false,
    sender_name: '',
    created_at: new Date().toISOString(),
  })
  inputText.value = ''
  await scrollToBottom()
  const ok = sendMessage(text)
  if (!ok) {
    try {
      const res = await sendConversationMessage(selectedId.value, { content: text })
      appendMessage(res.data)
    } catch {
      messages.value = messages.value.filter((item) => item.id !== tempId)
      inputText.value = text
      ElMessage.error(t('seller.sendFailed'))
    }
  }
  sending.value = false
}

function conversationTitle(item) {
  if (isPlatformChat(item)) {
    return t('seller.platformSupport')
  }
  return item.customer_name || item.user_name || t('seller.conversationFallback', { id: item.id })
}

function chatWithLabel(conv) {
  if (isPlatformChat(conv)) {
    return t('seller.chatWith', { name: t('seller.platformSupport') })
  }
  const name = conv.user_name || conv.user?.nickname || t('seller.customerFallback')
  return t('seller.chatWith', { name })
}

watch(selectedId, fetchMessages)

onMounted(async () => {
  await fetchConversations()
  const queryConvId = route.query.conversation_id
  if (queryConvId) {
    const id = Number(queryConvId)
    if (conversations.value.some((item) => item.id === id)) {
      await selectConversation(id)
    } else {
      selectedId.value = id
      await fetchMessages()
      await chatBadgeStore.refresh()
    }
  }
  listTimer = window.setInterval(fetchConversations, 15000)
})

onUnmounted(() => {
  if (listTimer) window.clearInterval(listTimer)
})
</script>

<template>
  <div
    class="chat-workbench page-card"
    :class="{ 'is-mobile': appStore.isMobile, 'show-chat': mobileShowChat }"
  >
    <div v-if="!mobileShowChat" class="page-header">
      <h2>{{ t('seller.chat') }}</h2>
      <div class="header-actions">
        <el-button type="primary" plain @click="handleOpenPlatformChat">{{ t('seller.contactPlatformBtn') }}</el-button>
        <el-button @click="fetchConversations">{{ t('seller.refresh') }}</el-button>
      </div>
    </div>

    <div
      class="workbench-body"
      :class="{ 'is-mobile': appStore.isMobile, 'show-chat': mobileShowChat }"
    >
      <div class="workbench-track">
        <aside class="conversation-list">
          <div
            v-for="item in conversations"
            :key="item.id"
            class="conversation-item"
            :class="{ active: item.id === selectedId }"
            @click="selectConversation(item.id)"
          >
            <div class="conv-head">
              <div class="conv-title">{{ conversationTitle(item) }}</div>
              <el-badge v-if="conversationUnread(item)" :value="conversationUnread(item)" />
            </div>
            <div class="conv-meta">
              <el-tag size="small" type="info">{{ item.conversation_type_display || item.conversation_type }}</el-tag>
              <el-tag :type="statusMap[item.status]?.type || 'info'" size="small">
                {{ statusMap[item.status]?.label || item.status }}
              </el-tag>
              <span>{{ formatChatTime(item.updated_at || item.created_at) }}</span>
            </div>
          </div>
          <el-empty v-if="!conversations.length" :description="t('seller.noConversation')" />
        </aside>

        <section class="chat-panel">
          <template v-if="selectedConversation">
            <div class="chat-toolbar">
              <div class="toolbar-left">
                <button
                  v-if="appStore.isMobile"
                  type="button"
                  class="mobile-back-btn"
                  @click="backToList"
                >
                  <el-icon><ArrowLeft /></el-icon>
                  {{ t('seller.back') }}
                </button>
                <span class="toolbar-title">{{ chatWithLabel(selectedConversation) }}</span>
              </div>
              <div class="toolbar-actions">
                <el-button
                  v-if="selectedConversation.status !== 'closed'"
                  size="small"
                  @click="handleAssign"
                >
                  {{ t('seller.assign') }}
                </el-button>
                <el-button
                  v-if="selectedConversation.status !== 'closed'"
                  size="small"
                  type="danger"
                  plain
                  @click="handleClose"
                >
                  {{ t('seller.closeChat') }}
                </el-button>
              </div>
            </div>

            <div ref="messageListRef" v-loading="loading" class="message-list">
              <div
                v-for="msg in messages"
                :key="msg.id"
                class="message-row"
                :class="messageRowClass(msg)"
              >
                <div class="message-inner">
                  <div v-if="messageRowClass(msg) === 'is-peer'" class="sender-name">{{ msg.sender_name }}</div>
                  <div class="bubble">{{ msg.content }}</div>
                  <div class="time">{{ formatChatTime(msg.created_at) }}</div>
                </div>
              </div>
              <el-empty v-if="!messages.length && !loading" :description="t('seller.noMessage')" />
            </div>

            <div v-if="selectedConversation.status !== 'closed'" class="composer">
              <el-input
                v-model="inputText"
                type="textarea"
                :rows="appStore.isMobile ? 2 : 3"
                :placeholder="t('seller.chatInputPlaceholder')"
                @keydown.ctrl.enter.prevent="handleSend"
              />
              <el-button type="primary" :loading="sending" @click="handleSend">{{ t('seller.send') }}</el-button>
            </div>
          </template>
          <el-empty v-else :description="t('seller.selectConversation')" />
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-workbench {
  min-height: calc(100vh - 120px);
}

.workbench-body {
  min-height: 560px;
}

.workbench-body:not(.is-mobile) .workbench-track {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
  min-height: 560px;
}

.conversation-list {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: auto;
  max-height: 640px;
  background: #fafafa;
}

.conversation-item {
  padding: 12px 14px;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
}

.conversation-item:hover,
.conversation-item.active {
  background: #ecf5ff;
}

.conv-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.conv-title {
  font-weight: 600;
  margin-bottom: 6px;
}

.conv-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.chat-panel {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  min-height: 560px;
  background: #fff;
}

.chat-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.toolbar-title {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-back-btn {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
  padding: 4px 8px 4px 0;
  border: none;
  background: transparent;
  color: #409eff;
  font-size: 14px;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.message-list {
  flex: 1;
  overflow: auto;
  padding: 16px;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

.message-row {
  display: flex;
  width: 100%;
}

.message-row.is-peer {
  justify-content: flex-start;
}

.message-row.is-self {
  justify-content: flex-end;
}

.message-inner {
  max-width: 75%;
  display: flex;
  flex-direction: column;
}

.message-row.is-self .message-inner {
  align-items: flex-end;
}

.sender-name {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.bubble {
  padding: 10px 14px;
  border-radius: 10px;
  line-height: 1.5;
  word-break: break-word;
}

.message-row.is-peer .bubble {
  background: #fff;
  border: 1px solid #ebeef5;
  border-top-left-radius: 2px;
}

.message-row.is-self .bubble {
  background: #409eff;
  color: #fff;
  border-top-right-radius: 2px;
}

.time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.composer {
  border-top: 1px solid #ebeef5;
  padding: 12px 16px;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  align-items: end;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .chat-workbench.page-card {
    margin: -12px;
    padding: 12px 0 0;
    min-height: calc(100dvh - 56px - 62px - env(safe-area-inset-bottom, 0px));
    border-radius: 0;
    box-shadow: none;
    display: flex;
    flex-direction: column;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
    padding: 0 12px 12px;
    margin-bottom: 0;
  }

  .page-header h2 {
    font-size: 17px;
  }

  .header-actions {
    display: flex;
    gap: 8px;
  }

  .header-actions .el-button {
    flex: 1;
  }

  .workbench-body.is-mobile {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }

  .workbench-body.is-mobile .workbench-track {
    display: flex;
    width: 200%;
    height: 100%;
    min-height: 420px;
    transition: transform 0.32s cubic-bezier(0.32, 0.72, 0, 1);
    will-change: transform;
  }

  .workbench-body.is-mobile.show-chat .workbench-track {
    transform: translateX(-50%);
  }

  .workbench-body.is-mobile .conversation-list,
  .workbench-body.is-mobile .chat-panel {
    width: 50%;
    flex-shrink: 0;
    max-height: none;
    min-height: 0;
    border-radius: 0;
    border-left: none;
    border-right: none;
  }

  .workbench-body.is-mobile .conversation-list {
    border-top: 1px solid #ebeef5;
  }

  .workbench-body.is-mobile .chat-panel {
    border-top: 1px solid #ebeef5;
  }

  .workbench-body.is-mobile .chat-toolbar {
    padding: 10px 12px;
  }

  .workbench-body.is-mobile .toolbar-actions .el-button {
    padding: 5px 8px;
  }

  .workbench-body.is-mobile .message-list {
    padding: 12px;
  }

  .workbench-body.is-mobile .composer {
    padding: 10px 12px calc(10px + env(safe-area-inset-bottom, 0px));
  }
}
</style>
