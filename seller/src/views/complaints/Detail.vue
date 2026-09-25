<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getComplaintDetail, replyComplaint } from '@/api/complaints'
import { useComplaintBadgeStore } from '@/stores/complaintBadge'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const complaintBadgeStore = useComplaintBadgeStore()

const loading = ref(true)
const submitting = ref(false)
const complaint = ref(null)
const replyText = ref('')
const markProcessed = ref(true)

const canReply = computed(() =>
  complaint.value && ['pending', 'merchant_processing'].includes(complaint.value.status),
)

async function fetchDetail() {
  loading.value = true
  try {
    const res = await getComplaintDetail(route.params.id)
    complaint.value = res.data
  } finally {
    loading.value = false
  }
}

async function handleReply() {
  if (!replyText.value.trim()) {
    ElMessage.warning(t('seller.complaintReplyRequired'))
    return
  }
  submitting.value = true
  try {
    const res = await replyComplaint(complaint.value.id, {
      content: replyText.value.trim(),
      mark_processed: markProcessed.value,
    })
    complaint.value = res.data
    replyText.value = ''
    ElMessage.success(t('seller.complaintReplySuccess'))
    await complaintBadgeStore.refresh()
  } finally {
    submitting.value = false
  }
}

onMounted(fetchDetail)
</script>

<template>
  <div class="page-wrap">
    <div class="page-header">
      <el-button link @click="router.back()">← {{ t('seller.back') }}</el-button>
      <h2>{{ t('seller.complaintDetail') }}</h2>
    </div>

    <el-skeleton v-if="loading" rows="8" animated />
    <template v-else-if="complaint">
      <el-descriptions :column="2" border class="info-block">
        <el-descriptions-item :label="t('seller.complaintNo')">{{ complaint.complaint_no }}</el-descriptions-item>
        <el-descriptions-item :label="t('seller.status')">{{ complaint.status_display }}</el-descriptions-item>
        <el-descriptions-item :label="t('seller.customer')">{{ complaint.customer_name }}</el-descriptions-item>
        <el-descriptions-item :label="t('seller.orderNo')">{{ complaint.order_no }}</el-descriptions-item>
        <el-descriptions-item :label="t('seller.complaintTitle')" :span="2">{{ complaint.title }}</el-descriptions-item>
        <el-descriptions-item :label="t('seller.complaintContent')" :span="2">{{ complaint.content }}</el-descriptions-item>
      </el-descriptions>

      <el-card shadow="never" class="message-card">
        <template #header>{{ t('seller.complaintMessages') }}</template>
        <div v-for="msg in complaint.messages || []" :key="msg.id" class="msg-row">
          <div class="msg-meta">{{ msg.sender_type }} · {{ msg.created_at?.replace('T', ' ').slice(0, 19) }}</div>
          <div class="msg-content">{{ msg.content }}</div>
        </div>
      </el-card>

      <el-card v-if="canReply" shadow="never" class="reply-card">
        <template #header>{{ t('seller.complaintReply') }}</template>
        <el-alert
          v-if="complaint.status === 'pending'"
          type="info"
          :closable="false"
          show-icon
          class="reply-tip"
          :title="t('seller.complaintReplyTip')"
        />
        <el-input v-model="replyText" type="textarea" :rows="4" :placeholder="t('seller.complaintReplyPlaceholder')" />
        <div class="reply-actions">
          <el-checkbox v-model="markProcessed">{{ t('seller.complaintMarkProcessed') }}</el-checkbox>
          <el-button type="primary" :loading="submitting" @click="handleReply">{{ t('seller.send') }}</el-button>
        </div>
      </el-card>
      <el-alert
        v-else-if="complaint"
        type="warning"
        :closable="false"
        show-icon
        :title="t('seller.complaintReadonlyTip')"
      />
    </template>
  </div>
</template>

<style scoped>
.page-wrap { padding: 4px 0; }
.page-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.info-block { margin-bottom: 16px; }
.message-card, .reply-card { margin-bottom: 16px; }
.msg-row { padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
.msg-meta { font-size: 12px; color: #909399; margin-bottom: 4px; }
.msg-content { white-space: pre-wrap; }
.reply-actions { margin-top: 12px; display: flex; justify-content: space-between; align-items: center; }
.reply-tip { margin-bottom: 12px; }
</style>
