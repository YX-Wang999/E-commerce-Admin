<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CircleCheckFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import {
  cancelClosureApplication,
  getClosureApplication,
  getClosureConditions,
  submitClosureApplication,
} from '@/api/closure'

const { t } = useI18n()
const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const checks = ref([])
const allPassed = ref(false)
const application = ref(null)
const form = ref({
  reason: '',
  detail: '',
})

const statusTag = computed(() => {
  const status = application.value?.status
  const map = {
    pending: { type: 'warning', label: t('closure.statusPending') },
    approved: { type: 'success', label: t('closure.statusApproved') },
    rejected: { type: 'danger', label: t('closure.statusRejected') },
    notice_period: { type: 'warning', label: t('closure.statusNotice') },
    completed: { type: 'info', label: t('closure.statusCompleted') },
    cancelled: { type: 'info', label: t('closure.statusCancelled') },
  }
  return map[status] || { type: 'info', label: status || '-' }
})

const canSubmit = computed(
  () => allPassed.value && !application.value && form.value.reason.trim().length >= 4,
)

const canCancel = computed(() =>
  ['pending', 'notice_period'].includes(application.value?.status),
)

async function fetchData() {
  loading.value = true
  try {
    const [checkRes, appRes] = await Promise.all([getClosureConditions(), getClosureApplication()])
    checks.value = checkRes.data?.checks || []
    allPassed.value = Boolean(checkRes.data?.all_passed)
    application.value = appRes.data || null
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  if (!canSubmit.value) return
  try {
    await ElMessageBox.confirm(t('closure.submitConfirm'), t('closure.title'), { type: 'warning' })
  } catch {
    return
  }
  submitting.value = true
  try {
    const res = await submitClosureApplication({
      reason: form.value.reason.trim(),
      detail: form.value.detail.trim(),
    })
    application.value = res.data
    ElMessage.success(res.message || t('closure.submitSuccess'))
  } catch (error) {
    ElMessage.error(error?.message || t('closure.submitFailed'))
  } finally {
    submitting.value = false
  }
}

async function handleCancel() {
  try {
    await ElMessageBox.confirm(t('closure.cancelConfirm'), t('closure.title'), { type: 'warning' })
  } catch {
    return
  }
  submitting.value = true
  try {
    await cancelClosureApplication()
    application.value = null
    ElMessage.success(t('closure.cancelSuccess'))
    await fetchData()
  } catch (error) {
    ElMessage.error(error?.message || t('closure.cancelFailed'))
  } finally {
    submitting.value = false
  }
}

onMounted(fetchData)
</script>

<template>
  <div v-loading="loading" class="page-card closure-page">
    <div class="page-header">
      <div>
        <h2>{{ t('closure.title') }}</h2>
        <p class="sub-tip">{{ t('closure.subtitle') }}</p>
      </div>
      <el-button @click="router.push({ name: 'SettingsProfile' })">{{ t('common.back') }}</el-button>
    </div>

    <el-alert type="warning" :closable="false" show-icon class="tip-alert">
      {{ t('closure.warning') }}
    </el-alert>

    <el-card shadow="never" :header="t('closure.checklistTitle')">
      <div v-for="item in checks" :key="item.code" class="check-row">
        <el-icon :class="item.is_completed ? 'ok' : 'bad'">
          <CircleCheckFilled v-if="item.is_completed" />
          <CircleCloseFilled v-else />
        </el-icon>
        <div class="check-body">
          <strong>{{ item.item }}</strong>
          <p v-if="item.remark" class="check-remark">{{ item.remark }}</p>
        </div>
      </div>
    </el-card>

    <el-card v-if="application" shadow="never" :header="t('closure.applicationTitle')">
      <el-descriptions :column="1" border>
        <el-descriptions-item :label="t('closure.status')">
          <el-tag :type="statusTag.type">{{ statusTag.label }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="t('closure.reason')">{{ application.reason }}</el-descriptions-item>
        <el-descriptions-item :label="t('closure.detail')">{{ application.detail || '-' }}</el-descriptions-item>
        <el-descriptions-item v-if="application.notice_end_at" :label="t('closure.noticeEnd')">
          {{ String(application.notice_end_at).replace('T', ' ').slice(0, 19) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="application.reject_reason" :label="t('closure.rejectReason')">
          {{ application.reject_reason }}
        </el-descriptions-item>
      </el-descriptions>
      <div v-if="canCancel" class="actions">
        <el-button type="danger" plain :loading="submitting" @click="handleCancel">
          {{ t('closure.cancelApplication') }}
        </el-button>
      </div>
    </el-card>

    <el-card v-else shadow="never" :header="t('closure.formTitle')">
      <el-form label-width="100px" @submit.prevent="handleSubmit">
        <el-form-item :label="t('closure.reason')" required>
          <el-input v-model="form.reason" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item :label="t('closure.detail')">
          <el-input v-model="form.detail" type="textarea" :rows="4" maxlength="1000" show-word-limit />
        </el-form-item>
        <el-form-item>
          <el-button type="danger" :disabled="!canSubmit" :loading="submitting" @click="handleSubmit">
            {{ t('closure.submit') }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.closure-page .page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.sub-tip {
  margin: 8px 0 0;
  color: #909399;
  font-size: 13px;
}

.tip-alert {
  margin-bottom: 16px;
}

.check-row {
  display: flex;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #ebeef5;
}

.check-row:last-child {
  border-bottom: none;
}

.check-row .ok {
  color: #67c23a;
  font-size: 20px;
}

.check-row .bad {
  color: #f56c6c;
  font-size: 20px;
}

.check-remark {
  margin: 4px 0 0;
  color: #909399;
  font-size: 13px;
}

.actions {
  margin-top: 16px;
}
</style>
