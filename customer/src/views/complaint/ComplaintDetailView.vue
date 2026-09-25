<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showToast } from 'vant'
import { confirmDialog } from '@/utils/confirmDialog'
import {
  customerReviewComplaint,
  getComplaint,
  requestPlatformComplaint,
  sendComplaintMessage,
} from '@/api/complaint'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const loading = ref(true)
const sending = ref(false)
const complaint = ref(null)
const inputText = ref('')
const messageListRef = ref(null)

const statusMap = {
  pending: 'complaint.statusPending',
  merchant_processing: 'complaint.statusMerchantProcessing',
  customer_review: 'complaint.statusCustomerReview',
  platform_reviewing: 'complaint.statusPlatformReviewing',
  resolved: 'complaint.statusResolved',
  rejected: 'complaint.statusRejected',
  closed: 'complaint.statusClosed',
}

const senderLabel = {
  customer: 'complaint.senderCustomer',
  merchant: 'complaint.senderMerchant',
  platform: 'complaint.senderPlatform',
}

const canConfirm = computed(() => complaint.value?.status === 'customer_review')
const canRequestPlatform = computed(() =>
  ['customer_review', 'merchant_processing', 'pending'].includes(complaint.value?.status),
)
const canSendMessage = computed(() =>
  complaint.value && !['closed', 'rejected', 'resolved'].includes(complaint.value.status),
)
const visibleMessages = computed(() => complaint.value?.messages || [])

async function fetchDetail() {
  loading.value = true
  try {
    const res = await getComplaint(route.params.id)
    complaint.value = res.data
    await nextTick()
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  } finally {
    loading.value = false
  }
}

async function handleSend() {
  const text = inputText.value.trim()
  if (!text || sending.value) return
  sending.value = true
  try {
    const res = await sendComplaintMessage(complaint.value.id, { content: text })
    complaint.value = res.data
    inputText.value = ''
    await nextTick()
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  } finally {
    sending.value = false
  }
}

async function handleConfirm() {
  try {
    await confirmDialog({ title: t('complaint.confirmSolveTitle'), message: t('complaint.confirmSolveMsg') })
    const res = await customerReviewComplaint(complaint.value.id, { satisfied: true })
    complaint.value = res.data
    showToast(t('complaint.confirmSuccess'))
  } catch {
    // cancelled
  }
}

async function handleRequestPlatform() {
  try {
    await confirmDialog({
      title: t('complaint.requestPlatformTitle'),
      message: t('complaint.requestPlatformMsg'),
    })
    const res = await requestPlatformComplaint(complaint.value.id, { reason: '' })
    complaint.value = res.data
    showToast(t('complaint.requestPlatformSuccess'))
  } catch {
    // cancelled
  }
}

onMounted(fetchDetail)
</script>

<template>
  <div class="complaint-detail-page">
    <van-nav-bar :title="t('complaint.detailTitle')" left-arrow @click-left="router.back()" />

    <van-loading v-if="loading" class="page-loading" />
    <template v-else-if="complaint">
      <div class="status-bar">
        <div class="status">{{ t(statusMap[complaint.status] || 'complaint.statusPending') }}</div>
        <div class="meta">
          {{ complaint.complaint_no }} · {{ t('complaint.orderNo', { no: complaint.order_no || '-' }) }}
        </div>
      </div>

      <div class="info-card">
        <div class="info-title">{{ complaint.title }}</div>
        <div class="info-content">{{ complaint.content }}</div>
        <div v-if="complaint.attachments?.length" class="attachments">
          <a
            v-for="(url, index) in complaint.attachments"
            :key="url"
            :href="url"
            target="_blank"
            rel="noopener"
          >
            📎 {{ t('complaint.attachment', { n: index + 1 }) }}
          </a>
        </div>
        <div v-if="complaint.resolution" class="resolution">
          {{ t('complaint.resolution') }}：{{ complaint.resolution }}
        </div>
      </div>

      <div ref="messageListRef" class="message-list">
        <div
          v-for="msg in visibleMessages"
          :key="msg.id"
          class="message-item"
          :class="msg.sender_type"
        >
          <div class="message-meta">
            {{ t(senderLabel[msg.sender_type] || 'complaint.senderCustomer') }}
            · {{ msg.created_at?.replace('T', ' ').slice(0, 16) }}
          </div>
          <div class="message-bubble">{{ msg.content }}</div>
        </div>
      </div>

      <div v-if="canConfirm || canRequestPlatform" class="action-bar">
        <van-button v-if="canConfirm" type="primary" size="small" @click="handleConfirm">
          {{ t('complaint.confirmSolve') }}
        </van-button>
        <van-button v-if="canRequestPlatform" type="warning" size="small" plain @click="handleRequestPlatform">
          {{ t('complaint.requestPlatform') }}
        </van-button>
      </div>

      <div v-if="canSendMessage" class="input-bar">
        <van-field v-model="inputText" rows="1" autosize type="textarea" :placeholder="t('complaint.inputPlaceholder')" />
        <van-button type="primary" size="small" :loading="sending" @click="handleSend">
          {{ t('complaint.send') }}
        </van-button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.complaint-detail-page {
  min-height: 100vh;
  background: #f5f6fa;
  display: flex;
  flex-direction: column;
}
.page-loading {
  display: flex;
  justify-content: center;
  padding: 48px 0;
}
.status-bar {
  background: #fff;
  padding: 14px 16px;
  border-bottom: 1px solid #f0f0f0;
}
.status {
  font-size: 16px;
  font-weight: 600;
  color: #323233;
}
.meta {
  margin-top: 4px;
  font-size: 12px;
  color: #969799;
}
.info-card {
  background: #fff;
  margin: 12px 16px;
  padding: 14px;
  border-radius: 10px;
}
.info-title {
  font-weight: 600;
  margin-bottom: 8px;
}
.info-content {
  color: #646566;
  font-size: 14px;
  line-height: 1.6;
}
.attachments {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.resolution {
  margin-top: 10px;
  color: #07c160;
  font-size: 13px;
}
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px 120px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.message-item.customer .message-bubble {
  background: #1989fa;
  color: #fff;
  align-self: flex-end;
}
.message-item.merchant .message-bubble,
.message-item.platform .message-bubble {
  background: #fff;
  color: #323233;
  align-self: flex-start;
}
.message-meta {
  font-size: 11px;
  color: #969799;
  margin-bottom: 4px;
}
.message-bubble {
  max-width: 85%;
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.5;
}
.action-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 56px;
  display: flex;
  gap: 8px;
  justify-content: center;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.96);
}
.input-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  gap: 8px;
  align-items: flex-end;
  padding: 8px 12px;
  background: #fff;
  border-top: 1px solid #eee;
}
.input-bar .van-field {
  flex: 1;
  background: #f5f6fa;
  border-radius: 8px;
}
</style>
