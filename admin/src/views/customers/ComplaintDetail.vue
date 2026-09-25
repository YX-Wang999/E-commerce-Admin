<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import {
  closeComplaint,
  getComplaintDetail,
  platformReviewComplaint,
  sendComplaintMessage,
} from '@/api/complaint'
import { useComplaintBadgeStore } from '@/stores/complaintBadge'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const complaintBadgeStore = useComplaintBadgeStore()

const loading = ref(true)
const submitting = ref(false)
const complaint = ref(null)
const reviewFormRef = ref(null)
const reviewForm = reactive({
  decision: 'refund',
  platform_remark: '',
  resolution: '',
  internal_note: '',
})
const internalNote = ref('')

const canArbitrate = computed(() => complaint.value?.status === 'platform_reviewing')
const canClose = computed(() => ['resolved', 'rejected'].includes(complaint.value?.status))
const publicMessages = computed(() => (complaint.value?.messages || []).filter((m) => !m.is_internal))
const internalMessages = computed(() => (complaint.value?.messages || []).filter((m) => m.is_internal))

const reviewRules = computed(() => ({
  decision: [{ required: true, message: t('complaint.decisionRequired'), trigger: 'change' }],
  platform_remark: [{ required: true, message: t('complaint.remarkRequired'), trigger: 'blur' }],
}))

async function fetchDetail() {
  loading.value = true
  try {
    const res = await getComplaintDetail(route.params.id)
    complaint.value = res.data
  } finally {
    loading.value = false
  }
}

async function submitReview() {
  await reviewFormRef.value?.validate()
  submitting.value = true
  try {
    const res = await platformReviewComplaint(complaint.value.id, {
      ...reviewForm,
      internal_note: reviewForm.internal_note,
    })
    complaint.value = res.data
    ElMessage.success(t('complaint.reviewSuccess'))
    await complaintBadgeStore.refresh()
  } finally {
    submitting.value = false
  }
}

async function submitInternalNote() {
  if (!internalNote.value.trim()) return
  submitting.value = true
  try {
    const res = await sendComplaintMessage(complaint.value.id, {
      content: internalNote.value.trim(),
      is_internal: true,
    })
    complaint.value = res.data
    internalNote.value = ''
    ElMessage.success(t('complaint.noteSaved'))
  } finally {
    submitting.value = false
  }
}

async function handleClose() {
  submitting.value = true
  try {
    const res = await closeComplaint(complaint.value.id)
    complaint.value = res.data
    ElMessage.success(t('complaint.closeSuccess'))
  } finally {
    submitting.value = false
  }
}

onMounted(fetchDetail)
</script>

<template>
  <div class="complaint-detail-page">
    <div class="page-header">
      <el-button link @click="router.back()">← {{ t('common.back') }}</el-button>
      <h2>{{ t('complaint.detailTitle') }}</h2>
    </div>

    <el-skeleton v-if="loading" rows="10" animated />
    <template v-else-if="complaint">
      <el-descriptions :column="2" border>
        <el-descriptions-item :label="t('complaint.no')">{{ complaint.complaint_no }}</el-descriptions-item>
        <el-descriptions-item :label="t('common.status')">{{ complaint.status_display }}</el-descriptions-item>
        <el-descriptions-item :label="t('complaint.customer')">{{ complaint.customer_name }}</el-descriptions-item>
        <el-descriptions-item :label="t('complaint.tenant')">{{ complaint.tenant_name }}</el-descriptions-item>
        <el-descriptions-item :label="t('complaint.orderNo')">{{ complaint.order_no }}</el-descriptions-item>
        <el-descriptions-item :label="t('complaint.category')">{{ complaint.category_display }}</el-descriptions-item>
        <el-descriptions-item :label="t('complaint.title')" :span="2">{{ complaint.title }}</el-descriptions-item>
        <el-descriptions-item :label="t('complaint.content')" :span="2">{{ complaint.content }}</el-descriptions-item>
      </el-descriptions>

      <el-card shadow="never" class="section-card">
        <template #header>{{ t('complaint.publicMessages') }}</template>
        <div v-for="msg in publicMessages" :key="msg.id" class="msg-row">
          <div class="msg-meta">{{ msg.sender_type }} · {{ msg.created_at?.replace('T', ' ').slice(0, 19) }}</div>
          <div>{{ msg.content }}</div>
        </div>
      </el-card>

      <el-card v-if="canArbitrate" shadow="never" class="section-card">
        <template #header>{{ t('complaint.arbitration') }}</template>
        <el-form ref="reviewFormRef" :model="reviewForm" :rules="reviewRules" label-width="100px">
          <el-form-item :label="t('complaint.decision')" prop="decision">
            <el-radio-group v-model="reviewForm.decision">
              <el-radio value="refund">{{ t('complaint.decisionRefund') }}</el-radio>
              <el-radio value="partial_refund">{{ t('complaint.decisionPartialRefund') }}</el-radio>
              <el-radio value="compensation">{{ t('complaint.decisionCompensation') }}</el-radio>
              <el-radio value="dismiss">{{ t('complaint.decisionDismiss') }}</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item :label="t('complaint.remark')" prop="platform_remark">
            <el-input v-model="reviewForm.platform_remark" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item :label="t('complaint.resolution')">
            <el-input v-model="reviewForm.resolution" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item :label="t('complaint.internalNote')">
            <el-input v-model="reviewForm.internal_note" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="submitting" @click="submitReview">
              {{ t('complaint.executeReview') }}
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <el-card shadow="never" class="section-card">
        <template #header>{{ t('complaint.internalNotes') }}</template>
        <div v-for="msg in internalMessages" :key="msg.id" class="msg-row internal">
          <div class="msg-meta">{{ msg.created_at?.replace('T', ' ').slice(0, 19) }}</div>
          <div>{{ msg.content }}</div>
        </div>
        <el-input v-model="internalNote" type="textarea" :rows="2" :placeholder="t('complaint.internalNotePlaceholder')" />
        <el-button class="mt-8" :loading="submitting" @click="submitInternalNote">{{ t('complaint.saveNote') }}</el-button>
      </el-card>

      <div v-if="canClose" class="footer-actions">
        <el-button type="info" :loading="submitting" @click="handleClose">{{ t('complaint.closeCase') }}</el-button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.complaint-detail-page { padding: 4px 0; }
.page-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.section-card { margin-top: 16px; }
.msg-row { padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
.msg-row.internal { background: #fffbe6; padding: 8px; border-radius: 6px; margin-bottom: 8px; }
.msg-meta { font-size: 12px; color: #909399; margin-bottom: 4px; }
.mt-8 { margin-top: 8px; }
.footer-actions { margin-top: 16px; }
</style>
