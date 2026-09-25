<script setup>

import { computed, nextTick, onMounted, ref, watch } from 'vue'

import { useRoute, useRouter } from 'vue-router'

import { useI18n } from 'vue-i18n'

import { showToast } from 'vant'
import { confirmDialog } from '@/utils/confirmDialog'

import {

  closeConversation,

  createComplaint,

  getConversationMessages,

  getMyConversation,

  listConversations,

  sendConversationMessage,

  startNewConversation,

  transferToPlatform,

} from '@/api/chat'

import { useChatWebSocket } from '@/composables/useChatWebSocket'

import { formatChatTime } from '@/utils/websocket'



const router = useRouter()

const route = useRoute()

const { t } = useI18n()



const loading = ref(true)

const listLoading = ref(false)

const listError = ref('')

const conversations = ref([])

const conversation = ref(null)

const messages = ref([])

const inputText = ref('')

const sending = ref(false)

const closing = ref(false)

const typingStaffName = ref('')

const offlineNotice = ref('')

const messageListRef = ref(null)



const activeConversationId = computed(() => {

  const raw = route.query.conversation_id

  return raw ? Number(raw) : null

})



const inChatView = computed(() => Boolean(activeConversationId.value))



const conversationId = computed(() => conversation.value?.id || null)

const isClosed = computed(() => conversation.value?.status === 'closed')



const statusLabel = computed(() => {

  if (!conversation.value) return ''

  if (conversation.value.status === 'pending') return t('chat.statusPending')

  if (conversation.value.status === 'active') return t('chat.statusActive')

  return t('chat.statusClosed')

})



async function scrollToBottom() {

  await nextTick()

  const el = messageListRef.value

  if (el) {

    el.scrollTop = el.scrollHeight

  }

}



const chatSubtitle = computed(() => {

  if (!conversation.value) return ''

  const type = conversation.value.conversation_type

  if (type === 'b2c') {

    return t('chat.subtitleB2c', { name: conversation.value.tenant_name || t('chat.shopFallback') })

  }

  if (type === 'c2p_b') return t('chat.subtitleComplaint')

  if (type === 'c2p') return t('chat.subtitlePlatform')

  return statusLabel.value

})



const showTransfer = computed(() =>

  conversation.value

  && !isClosed.value

  && ['b2c', 'c2p_b'].includes(conversation.value.conversation_type),

)



function conversationTitle(item) {

  if (item.conversation_type === 'b2c') {

    return t('chat.subtitleB2c', { name: item.tenant_name || t('chat.shopFallback') })

  }

  if (item.conversation_type === 'c2p_b') return t('chat.subtitleComplaint')

  if (item.conversation_type === 'c2p') return t('chat.subtitlePlatform')

  return item.conversation_type_display || t('chat.title')

}



function conversationPreview(item) {

  return item.last_message?.content || t('chat.empty')

}



function formatListTime(value) {

  if (!value) return ''

  return formatChatTime(value)

}



async function loadConversationList() {

  listLoading.value = true

  listError.value = ''

  try {

    const res = await listConversations()

    conversations.value = res.data || []

  } catch (error) {

    conversations.value = []

    listError.value = error?.response?.data?.message || t('chat.listFailed')

  } finally {

    listLoading.value = false

  }

}



async function loadConversationDetail() {

  if (!activeConversationId.value) {

    conversation.value = null

    messages.value = []

    return

  }



  loading.value = true

  try {

    const selected = conversations.value.find((item) => item.id === activeConversationId.value)

    if (selected) {

      conversation.value = selected

    } else {

      await loadConversationList()

      const matched = conversations.value.find((item) => item.id === activeConversationId.value)

      if (!matched) {

        showToast(t('chat.conversationNotFound'))

        router.replace({ path: '/chat' })

        return

      }

      conversation.value = matched

    }

    await loadMessages()

  } finally {

    loading.value = false

  }

}



function openConversation(item) {

  router.push({

    path: '/chat',

    query: { conversation_id: String(item.id) },

  })

}



async function handleStartNewChat() {

  loading.value = true

  try {

    const res = await startNewConversation()

    await loadConversationList()

    router.push({

      path: '/chat',

      query: { conversation_id: String(res.data.id) },

    })

  } finally {

    loading.value = false

  }

}



async function handleTransferPlatform() {

  if (!conversation.value?.id) return

  try {

    const res = await transferToPlatform(conversation.value.id)

    conversation.value = res.data

    messages.value = []

    await loadMessages()

    await loadConversationList()

    showToast(t('chat.transferSuccess'))

  } catch {

    // handled by interceptor

  }

}



async function loadMessages() {

  if (!conversation.value?.id) return

  const res = await getConversationMessages(conversation.value.id)

  messages.value = res.data || []

  await scrollToBottom()

}



function appendMessage(message) {

  if (messages.value.some((item) => item.id === message.id)) return

  const tempIndex = messages.value.findIndex(

    (item) => String(item.id).startsWith('temp-') && item.content === message.content,

  )

  if (tempIndex >= 0) {

    messages.value.splice(tempIndex, 1, message)

  } else {

    messages.value.push(message)

  }

  scrollToBottom()

}



const { sendMessage, notifyTyping, disconnect } = useChatWebSocket(conversationId, {

  onMessage: (message) => {

    appendMessage(message)

    typingStaffName.value = ''

    if (message.is_staff) {

      offlineNotice.value = ''

    }

  },

  onTyping: (data) => {

    if (data.is_staff && data.typing) {

      typingStaffName.value = data.sender_name

      offlineNotice.value = ''

    } else if (data.is_staff) {

      typingStaffName.value = ''

    }

  },

  onStaffOffline: (message) => {

    offlineNotice.value = message || t('chat.staffOfflineHint')

  },

  onError: (message) => {

    if (message) showToast(message)

  },

})



async function handleSend() {

  const text = inputText.value.trim()

  if (!text || sending.value) return

  if (isClosed.value) {

    showToast(t('chat.closedHint'))

    return

  }

  if (!conversation.value?.id) return



  sending.value = true

  const tempId = `temp-${Date.now()}`

  messages.value.push({

    id: tempId,

    content: text,

    is_staff: false,

    sender_name: t('chat.me'),

    created_at: new Date().toISOString(),

  })

  inputText.value = ''

  await scrollToBottom()



  const wsOk = sendMessage(text)

  if (!wsOk) {

    try {

      const res = await sendConversationMessage(conversation.value.id, { content: text })

      appendMessage(res.data)

    } catch {

      messages.value = messages.value.filter((item) => item.id !== tempId)

      inputText.value = text

      showToast(t('chat.sendFailed'))

    }

  }

  sending.value = false

}



async function handleClose() {

  if (!conversation.value?.id || isClosed.value) return

  try {

    await confirmDialog({

      title: t('chat.closeConfirmTitle'),

      message: t('chat.closeConfirmMessage'),

    })

  } catch {

    return

  }

  closing.value = true

  try {

    const res = await closeConversation(conversation.value.id)

    conversation.value = res.data

    disconnect()

    await loadConversationList()

    showToast(t('chat.closeSuccess'))

  } catch {

    // handled by request interceptor

  } finally {

    closing.value = false

  }

}



async function handleNewChat() {

  await handleStartNewChat()

}



function handleNavBack() {

  if (inChatView.value) {

    router.replace({ path: '/chat' })

    return

  }

  router.back()

}



function handleInput() {

  notifyTyping()

}



watch(messages, () => scrollToBottom(), { deep: true })



watch(

  () => route.query.conversation_id,

  async (id) => {

    if (id) {

      await loadConversationDetail()

    } else {

      disconnect()

      conversation.value = null

      messages.value = []

      loading.value = false

    }

  },

)



onMounted(async () => {

  await loadConversationList()



  if (route.query.action === 'complaint' && route.query.tenant_id && !route.query.conversation_id) {

    loading.value = true

    try {

      const res = await createComplaint({

        tenant_id: Number(route.query.tenant_id),

        category: 'product_quality',

        content: t('chat.complaintDefaultContent'),

      })

      showToast(t('chat.complaintSubmitted'))

      const convId = res.data?.conversation_id

      if (convId) {

        router.replace({

          path: '/chat',

          query: { conversation_id: String(convId) },

        })

        return

      }

    } catch {

      loading.value = false

      return

    }

  }



  if (route.query.tenant_id && !route.query.conversation_id) {

    const res = await getMyConversation({ tenant_id: route.query.tenant_id })

    router.replace({

      path: '/chat',

      query: {

        conversation_id: String(res.data.id),

        ...(route.query.action ? { action: route.query.action } : {}),

        tenant_id: route.query.tenant_id,

      },

    })

    return

  }



  if (activeConversationId.value) {

    await loadConversationDetail()

  } else {

    loading.value = false

  }

})

</script>



<template>

  <div class="chat-page" :class="{ 'is-detail': inChatView }">

    <van-nav-bar

      :title="inChatView ? t('chat.title') : t('chat.conversationList')"

      :subtitle="inChatView ? chatSubtitle : ''"

      left-arrow

      fixed

      placeholder

      @click-left="handleNavBack"

    >

      <template v-if="inChatView" #right>

        <button

          v-if="showTransfer"

          type="button"

          class="nav-action"

          @click="handleTransferPlatform"

        >

          {{ t('chat.transferPlatform') }}

        </button>

        <button

          v-else-if="conversation && !isClosed"

          type="button"

          class="nav-action"

          :disabled="closing"

          @click="handleClose"

        >

          {{ t('chat.close') }}

        </button>

        <span v-else-if="conversation" class="status-tag">{{ statusLabel }}</span>

      </template>

    </van-nav-bar>



    <template v-if="!inChatView">

      <div class="list-toolbar">

        <van-button type="primary" size="small" round icon="plus" @click="handleStartNewChat">

          {{ t('chat.newChat') }}

        </van-button>

      </div>



      <van-loading v-if="listLoading" class="page-loading" vertical>

        {{ t('common.loading') }}

      </van-loading>



      <van-empty v-else-if="listError" :description="listError">

        <van-button round type="primary" size="small" @click="loadConversationList">

          {{ t('common.retry') }}

        </van-button>

      </van-empty>



      <van-empty v-else-if="!conversations.length" :description="t('chat.noConversations')">

        <van-button round type="primary" size="small" @click="handleStartNewChat">

          {{ t('chat.newChat') }}

        </van-button>

      </van-empty>



      <van-cell-group v-else inset class="conversation-list">

        <van-cell

          v-for="item in conversations"

          :key="item.id"

          is-link

          @click="openConversation(item)"

        >

          <template #title>

            <div class="conv-title">{{ conversationTitle(item) }}</div>

            <div class="conv-preview">{{ conversationPreview(item) }}</div>

          </template>

          <template #value>

            <div class="conv-meta">

              <van-badge v-if="item.unread_count" :content="item.unread_count" />

              <span class="conv-time">{{ formatListTime(item.last_message?.created_at || item.updated_at) }}</span>

              <van-tag v-if="item.status === 'closed'" plain type="default" size="medium">

                {{ t('chat.statusClosed') }}

              </van-tag>

            </div>

          </template>

        </van-cell>

      </van-cell-group>

    </template>



    <van-loading v-else-if="loading" class="page-loading" vertical>

      {{ t('common.loading') }}

    </van-loading>



    <template v-else>

      <div ref="messageListRef" class="message-list">

        <div v-if="!messages.length" class="empty-tip">{{ t('chat.empty') }}</div>

        <div

          v-for="item in messages"

          :key="item.id"

          class="message-row"

          :class="item.is_staff ? 'is-staff' : 'is-user'"

        >

          <div class="message-inner">

            <div class="avatar" :class="item.is_staff ? 'staff-avatar' : 'user-avatar'">

              <van-icon :name="item.is_staff ? 'service-o' : 'user-o'" size="18" />

            </div>

            <div class="message-content">

              <div class="sender-line">

                <span class="sender-name">{{ item.is_staff ? item.sender_name : t('chat.me') }}</span>

                <span class="role-tag" :class="item.is_staff ? 'staff-tag' : 'user-tag'">

                  {{ item.is_staff ? t('chat.staffLabel') : t('chat.userLabel') }}

                </span>

              </div>

              <div class="bubble">{{ item.content }}</div>

              <div class="time">{{ formatChatTime(item.created_at) }}</div>

            </div>

          </div>

        </div>

        <div v-if="typingStaffName" class="typing-tip">

          {{ t('chat.typing', { name: typingStaffName }) }}

        </div>

        <div v-if="offlineNotice" class="offline-notice">

          {{ offlineNotice }}

        </div>

      </div>



      <div v-if="isClosed" class="closed-bar">

        <span>{{ t('chat.closedHint') }}</span>

        <van-button size="small" type="primary" @click="handleNewChat">

          {{ t('chat.newChat') }}

        </van-button>

      </div>



      <div v-else class="chat-input-bar" @keydown.ctrl.enter.prevent="handleSend">
        <van-field

          v-model="inputText"

          rows="1"

          autosize

          type="textarea"

          maxlength="500"

          :placeholder="t('chat.inputPlaceholder')"

          @update:model-value="handleInput"

        />

        <van-button type="primary" size="small" :loading="sending" @click="handleSend">

          {{ t('chat.send') }}

        </van-button>

      </div>

    </template>

  </div>

</template>



<style scoped>

.chat-page {

  min-height: 100vh;

  background: #f5f6fa;

}



.chat-page.is-detail {

  display: flex;

  flex-direction: column;

  height: 100vh;

}



.nav-action {

  border: none;

  background: none;

  padding: 0;

  font-size: 14px;

  color: #ee0a24;

  cursor: pointer;

}



.status-tag {

  font-size: 12px;

  color: #969799;

}



.list-toolbar {

  display: flex;

  justify-content: flex-end;

  padding: 12px 16px 0;

}



.conversation-list {

  margin-top: 8px;

}



.conv-title {

  font-size: 15px;

  font-weight: 600;

  color: #323233;

}



.conv-preview {

  margin-top: 4px;

  font-size: 13px;

  color: #969799;

  overflow: hidden;

  text-overflow: ellipsis;

  white-space: nowrap;

  max-width: 220px;

}



.conv-meta {

  display: flex;

  flex-direction: column;

  align-items: flex-end;

  gap: 6px;

}



.conv-time {

  font-size: 11px;

  color: #969799;

}



.page-loading {

  display: flex;

  justify-content: center;

  padding: 80px 0;

}



.message-list {

  flex: 1;

  overflow-y: auto;

  padding: 12px 12px 8px;

  display: flex;

  flex-direction: column;

  gap: 12px;

}



.empty-tip {

  text-align: center;

  color: #969799;

  font-size: 14px;

  padding: 40px 0;

}



.message-row {

  display: flex;

  width: 100%;

}



.message-row.is-staff {

  justify-content: flex-start;

}



.message-row.is-user {

  justify-content: flex-end;

}



.message-inner {

  display: flex;

  gap: 8px;

  max-width: 88%;

}



.message-row.is-user .message-inner {

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



.staff-avatar {

  background: #fff;

  color: #1989fa;

  border: 1px solid #dceefe;

}



.user-avatar {

  background: #1989fa;

  color: #fff;

}



.message-content {

  min-width: 0;

}



.message-row.is-user .message-content {

  align-items: flex-end;

  display: flex;

  flex-direction: column;

}



.sender-line {

  display: flex;

  align-items: center;

  gap: 6px;

  margin-bottom: 4px;

}



.message-row.is-user .sender-line {

  flex-direction: row-reverse;

}



.sender-name {

  font-size: 12px;

  font-weight: 600;

  color: #646566;

}



.role-tag {

  font-size: 10px;

  padding: 1px 6px;

  border-radius: 10px;

}



.staff-tag {

  background: #ecf5ff;

  color: #1989fa;

}



.user-tag {

  background: #e8f3ff;

  color: #1989fa;

}



.bubble {

  padding: 10px 12px;

  border-radius: 10px;

  font-size: 14px;

  line-height: 1.5;

  word-break: break-word;

}



.is-staff .bubble {

  background: #fff;

  color: #323233;

  border-top-left-radius: 2px;

  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);

}



.is-user .bubble {

  background: #1989fa;

  color: #fff;

  border-top-right-radius: 2px;

}



.time {

  margin-top: 4px;

  font-size: 11px;

  color: #969799;

}



.typing-tip {

  font-size: 12px;

  color: #969799;

  padding: 4px 4px 8px;

}



.offline-notice {

  margin: 8px 4px;

  padding: 10px 12px;

  font-size: 13px;

  line-height: 1.5;

  color: #646566;

  background: #fff7e8;

  border: 1px solid #ffe7ba;

  border-radius: 8px;

}



.closed-bar {

  display: flex;

  align-items: center;

  justify-content: space-between;

  gap: 12px;

  padding: 12px 16px;

  background: #fff7f7;

  border-top: 1px solid #ffd6d6;

  font-size: 13px;

  color: #646566;

}



.chat-input-bar {

  display: flex;

  align-items: flex-end;

  gap: 8px;

  padding: 8px 12px 12px;

  background: #fff;

  border-top: 1px solid #eee;

}



.chat-input-bar .van-field {

  flex: 1;

  background: #f7f8fa;

  border-radius: 8px;

}



.chat-input-bar .van-button {

  flex-shrink: 0;

  min-width: 64px;

}

</style>


