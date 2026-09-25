<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Service, User } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useChatBadgeStore } from '@/stores/chatBadge'
import {
  assignConversation,
  closeConversation,
  getChatConversations,
  getChatStats,
  getConversationMessages,
  updateChatPresence,
} from '@/api/chat'
import { useChatWebSocket } from '@/composables/useChatWebSocket'
import { formatChatTime } from '@/utils/websocket'

const props = defineProps({
  conversationScope: {
    type: String,
    default: 'customer',
    validator: (value) => ['customer', 'merchant', 'all'].includes(value),
  },
})

const MERCHANT_TYPES = new Set(['b2p', 'p2b'])
const CUSTOMER_TYPES = new Set(['b2c', 'c2p', 'c2p_b'])

const { t } = useI18n()
const route = useRoute()
const authStore = useAuthStore()
const chatBadgeStore = useChatBadgeStore()

const loading = ref(false)
const conversations = ref([])
const selectedId = ref(null)
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const typingUserName = ref('')
const messageListRef = ref(null)
const stats = ref({
  online_staff: 0,
  pending_conversations: 0,
  today_messages: 0,
})

let listTimer = null
let presenceTimer = null

const selectedConversation = computed(() =>
  conversations.value.find((item) => item.id === selectedId.value) || null,
)

const conversationId = computed(() => selectedId.value)

const roleCodes = computed(() => authStore.user?.roles?.map((item) => item.code) || [])
const canAssign = computed(() =>
  Boolean(authStore.user?.is_superuser) || roleCodes.value.some((code) => ['ops_director', 'ops_manager', 'super_admin'].includes(code)),
)
const canClose = computed(() => true)

const statusMap = computed(() => ({
  pending: { label: t('chat.statusPending'), type: 'warning' },
  active: { label: t('chat.statusActive'), type: 'success' },
  closed: { label: t('chat.statusClosed'), type: 'info' },
}))

async function scrollToBottom() {
  await nextTick()
  const el = messageListRef.value
  if (el) el.scrollTop = el.scrollHeight
}

async function fetchConversations() {
  try {
    const res = await getChatConversations()
    let list = res.data || []
    if (props.conversationScope === 'merchant') {
      list = list.filter((item) => MERCHANT_TYPES.has(item.conversation_type))
    } else if (props.conversationScope === 'customer') {
      list = list.filter((item) => !item.conversation_type || CUSTOMER_TYPES.has(item.conversation_type))
    }
    conversations.value = list
    if (selectedId.value && !conversations.value.some((item) => item.id === selectedId.value)) {
      selectedId.value = null
      messages.value = []
    }
  } catch {
    // handled by interceptor
  }
}

async function fetchStats() {
  try {
    const res = await getChatStats()
    stats.value = res.data || stats.value
  } catch {
    // optional
  }
}

async function loadMessages(conversationId) {
  const res = await getConversationMessages(conversationId)
  messages.value = res.data || []
  await scrollToBottom()
}

function appendMessage(message) {
  if (messages.value.some((item) => item.id === message.id)) return
  messages.value.push(message)
  scrollToBottom()
  fetchConversations()
  chatBadgeStore.refresh()
}

const { sendMessage, notifyTyping, disconnect } = useChatWebSocket(conversationId, {
  onMessage: (message) => {
    appendMessage(message)
    typingUserName.value = ''
  },
  onTyping: (data) => {
    if (!data.is_staff && data.typing) {
      typingUserName.value = data.sender_name
    } else if (!data.is_staff) {
      typingUserName.value = ''
    }
  },
})

async function selectConversation(item) {
  selectedId.value = item.id
  loading.value = true
  try {
    if (item.status === 'pending' && canAssign.value) {
      await assignConversation(item.id)
      await fetchConversations()
    }
    await loadMessages(item.id)
    await Promise.all([fetchConversations(), chatBadgeStore.refresh()])
  } finally {
    loading.value = false
  }
}

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || !selectedId.value || sending.value) return
  sending.value = true
  const ok = sendMessage(text)
  if (ok) {
    inputText.value = ''
  } else {
    ElMessage.error(t('chat.sendFailed'))
  }
  sending.value = false
}

async function handleClose() {
  if (!selectedId.value) return
  try {
    await ElMessageBox.confirm(t('chat.closeConfirmMessage'), t('chat.closeConfirmTitle'), {
      type: 'warning',
    })
  } catch {
    return
  }
  await closeConversation(selectedId.value)
  disconnect()
  selectedId.value = null
  ElMessage.success(t('chat.closeSuccess'))
  messages.value = []
  await Promise.all([fetchConversations(), chatBadgeStore.refresh()])
}

async function handleAssign() {
  if (!selectedId.value) return
  await assignConversation(selectedId.value)
  ElMessage.success(t('chat.assignSuccess'))
  await fetchConversations()
}

function displayUserName(item) {
  if (item.conversation_type === 'b2p' || item.conversation_type === 'p2b') {
    return item.tenant_name || item.customer_name || `#${item.tenant}`
  }
  return item.customer_name || item.customer_phone || `#${item.customer}`
}

function isMerchantConversation(item) {
  return item?.conversation_type === 'b2p' || item?.conversation_type === 'p2b'
}

/** Left = peer, right = self (current viewer). */
function messageRowClass(item) {
  if (isMerchantConversation(selectedConversation.value)) {
    return item.is_platform_staff ? 'is-self' : 'is-peer'
  }
  return item.is_staff ? 'is-self' : 'is-peer'
}

function selfRoleLabel() {
  if (isMerchantConversation(selectedConversation.value)) {
    return t('chat.platformLabel')
  }
  return t('chat.staffLabel')
}

function peerRoleLabel() {
  if (isMerchantConversation(selectedConversation.value)) {
    return t('chat.merchantLabel')
  }
  return t('chat.userLabel')
}

onMounted(async () => {
  loading.value = true
  await updateChatPresence(true)
  await Promise.all([fetchConversations(), fetchStats()])
  loading.value = false

  const queryConvId = route.query.conversation_id
  if (queryConvId) {
    const id = Number(queryConvId)
    const target = conversations.value.find((item) => item.id === id)
    if (target) {
      await selectConversation(target)
    } else {
      selectedId.value = id
      await loadMessages(id)
      await Promise.all([fetchConversations(), chatBadgeStore.refresh()])
    }
  }

  listTimer = setInterval(() => {
    fetchConversations()
    fetchStats()
  }, 15000)

  presenceTimer = setInterval(() => {
    updateChatPresence(true)
  }, 30000)
})

onUnmounted(async () => {
  clearInterval(listTimer)
  clearInterval(presenceTimer)
  await updateChatPresence(false)
})

watch(messages, () => scrollToBottom(), { deep: true })
</script>

<template>
  <div class="chat-workbench">
    <div class="workbench-header">
      <div>
        <h2>{{ t('chat.workbenchTitle') }}</h2>
        <p class="subtitle">{{ t('chat.workbenchSubtitle') }}</p>
      </div>
      <el-tag type="success" effect="dark">{{ t('chat.onlineStatus') }}</el-tag>
    </div>

    <div v-loading="loading" class="workbench-body">
      <aside class="conversation-panel">
        <div class="panel-title">{{ t('chat.conversationList') }}</div>
        <div v-if="!conversations.length" class="panel-empty">{{ t('chat.noConversations') }}</div>
        <button
          v-for="item in conversations"
          :key="item.id"
          type="button"
          class="conversation-item"
          :class="{ active: selectedId === item.id }"
          @click="selectConversation(item)"
        >
          <div class="item-head">
            <span class="item-user">{{ displayUserName(item) }}</span>
            <el-badge v-if="item.staff_unread_count" :value="item.staff_unread_count" />
          </div>
          <div class="item-meta">
            <el-tag size="small" type="info">{{ item.conversation_type_display || item.conversation_type }}</el-tag>
            <el-tag size="small" :type="statusMap[item.status]?.type">
              {{ statusMap[item.status]?.label }}
            </el-tag>
            <span v-if="item.assigned_to_name" class="assignee">
              {{ t('chat.assignee', { name: item.assigned_to_name }) }}
            </span>
          </div>
          <div v-if="item.last_message" class="item-preview">
            {{ item.last_message.content }}
          </div>
        </button>
      </aside>

      <section class="chat-panel">
        <template v-if="selectedConversation">
          <div class="chat-panel-head">
            <div>
              <strong>{{ displayUserName(selectedConversation) }}</strong>
              <span v-if="selectedConversation.assigned_to_name" class="assignee-line">
                {{ t('chat.currentAssignee', { name: selectedConversation.assigned_to_name }) }}
              </span>
            </div>
            <div class="chat-actions">
              <el-button
                v-if="selectedConversation.status === 'pending' && canAssign"
                size="small"
                @click="handleAssign"
              >
                {{ t('chat.assign') }}
              </el-button>
              <el-button
                v-if="selectedConversation.status !== 'closed' && canClose"
                size="small"
                type="danger"
                plain
                @click="handleClose"
              >
                {{ t('chat.close') }}
              </el-button>
            </div>
          </div>

          <div ref="messageListRef" class="message-list">
            <div
              v-for="item in messages"
              :key="item.id"
              class="message-row"
              :class="messageRowClass(item)"
            >
              <div class="message-inner">
                <div class="avatar" :class="messageRowClass(item) === 'is-self' ? 'staff-avatar' : 'user-avatar'">
                  <el-icon><Service v-if="messageRowClass(item) === 'is-self'" /><User v-else /></el-icon>
                </div>
                <div class="message-content">
                  <div class="message-meta">
                    <span class="sender">{{ item.sender_name }}</span>
                    <span class="role-tag" :class="messageRowClass(item) === 'is-self' ? 'staff-tag' : 'user-tag'">
                      {{ messageRowClass(item) === 'is-self' ? selfRoleLabel() : peerRoleLabel() }}
                    </span>
                    <span class="time">{{ formatChatTime(item.created_at) }}</span>
                  </div>
                  <div class="bubble">{{ item.content }}</div>
                </div>
              </div>
            </div>
            <div v-if="typingUserName" class="typing-tip">
              {{ t('chat.userTyping', { name: typingUserName }) }}
            </div>
          </div>

          <div class="chat-input-bar">
            <el-input
              v-model="inputText"
              type="textarea"
              :rows="2"
              maxlength="500"
              :placeholder="t('chat.inputPlaceholder')"
              :disabled="selectedConversation.status === 'closed'"
              @input="notifyTyping"
              @keyup.enter.exact="handleSend"
            />
            <el-button
              type="primary"
              :loading="sending"
              :disabled="selectedConversation.status === 'closed'"
              @click="handleSend"
            >
              {{ t('chat.send') }}
            </el-button>
          </div>
        </template>
        <el-empty v-else :description="t('chat.selectConversation')" />
      </section>
    </div>

    <div class="workbench-footer">
      <span>{{ t('chat.statsOnline', { count: stats.online_staff }) }}</span>
      <span>{{ t('chat.statsPending', { count: stats.pending_conversations }) }}</span>
      <span>{{ t('chat.statsMessages', { count: stats.today_messages }) }}</span>
    </div>
  </div>
</template>

<style scoped>
.chat-workbench {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: calc(100vh - 120px);
}

.workbench-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.workbench-header h2 {
  margin: 0;
  font-size: 20px;
}

.subtitle {
  margin: 4px 0 0;
  color: #909399;
  font-size: 13px;
}

.workbench-body {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 12px;
  min-height: 560px;
}

.conversation-panel,
.chat-panel {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
}

.conversation-panel {
  display: flex;
  flex-direction: column;
}

.panel-title {
  padding: 12px 14px;
  font-weight: 600;
  border-bottom: 1px solid #ebeef5;
}

.panel-empty {
  padding: 24px 14px;
  color: #909399;
  font-size: 13px;
}

.conversation-item {
  width: 100%;
  border: none;
  background: #fff;
  text-align: left;
  padding: 12px 14px;
  border-bottom: 1px solid #f2f3f5;
  cursor: pointer;
}

.conversation-item.active,
.conversation-item:hover {
  background: #f5f9ff;
}

.item-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.item-user {
  font-weight: 600;
  color: #303133;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  font-size: 12px;
}

.assignee {
  color: #909399;
}

.item-preview {
  margin-top: 6px;
  color: #909399;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-panel {
  display: flex;
  flex-direction: column;
}

.chat-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
}

.assignee-line {
  display: block;
  margin-top: 4px;
  color: #909399;
  font-size: 12px;
}

.chat-actions {
  display: flex;
  gap: 8px;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
  gap: 14px;
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
  display: flex;
  gap: 10px;
  max-width: 78%;
}

.message-row.is-self .message-inner {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-avatar {
  background: #fff;
  color: #606266;
  border: 1px solid #ebeef5;
}

.staff-avatar {
  background: #409eff;
  color: #fff;
}

.message-content {
  min-width: 0;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
  color: #909399;
  flex-wrap: wrap;
}

.role-tag {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 10px;
}

.user-tag {
  background: #f4f4f5;
  color: #909399;
}

.staff-tag {
  background: #ecf5ff;
  color: #409eff;
}

.bubble {
  padding: 10px 12px;
  border-radius: 8px;
  line-height: 1.5;
  word-break: break-word;
}

.message-row.is-self .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-row.is-self .message-meta {
  flex-direction: row-reverse;
}

.message-row.is-self .sender {
  color: #409eff;
  font-weight: 600;
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

.typing-tip {
  font-size: 12px;
  color: #909399;
}

.chat-input-bar {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  border-top: 1px solid #ebeef5;
}

.chat-input-bar .el-input {
  flex: 1;
}

.workbench-footer {
  display: flex;
  gap: 24px;
  padding: 10px 4px;
  color: #606266;
  font-size: 13px;
}

@media (max-width: 960px) {
  .workbench-body {
    grid-template-columns: 1fr;
  }
}
</style>
