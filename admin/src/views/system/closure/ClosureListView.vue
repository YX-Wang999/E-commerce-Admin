<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  approveClosure,
  completeClosure,
  exportClosures,
  getClosureApplications,
  rejectClosure,
} from '@/api/closure'

const { t } = useI18n()
const router = useRouter()
const loading = ref(false)
const tableData = ref([])
const status = ref('')

const statusOptions = [
  { value: '', label: t('common.all') },
  { value: 'pending', label: t('closure.statusPending') },
  { value: 'notice_period', label: t('closure.statusNotice') },
  { value: 'completed', label: t('closure.statusCompleted') },
  { value: 'rejected', label: t('closure.statusRejected') },
  { value: 'cancelled', label: t('closure.statusCancelled') },
]

async function fetchList() {
  loading.value = true
  try {
    const res = await getClosureApplications({ page_size: 50, status: status.value || undefined })
    tableData.value = res.data.results || res.data || []
  } finally {
    loading.value = false
  }
}

async function handleApprove(row) {
  try {
    const { value } = await ElMessageBox.prompt(t('closure.noticeDaysPrompt'), t('closure.approve'), {
      inputValue: '15',
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
    })
    await approveClosure(row.id, { notice_days: Number(value) || 15 })
    ElMessage.success(t('common.success'))
    fetchList()
  } catch {
    /* cancelled */
  }
}

async function handleReject(row) {
  try {
    const { value } = await ElMessageBox.prompt(t('closure.rejectPrompt'), t('closure.reject'), {
      inputValidator: (val) => Boolean(val?.trim()) || t('closure.rejectRequired'),
    })
    await rejectClosure(row.id, { reject_reason: value })
    ElMessage.success(t('common.success'))
    fetchList()
  } catch {
    /* cancelled */
  }
}

async function handleComplete(row) {
  try {
    await ElMessageBox.confirm(t('closure.completeConfirm'), t('closure.complete'), { type: 'warning' })
    await completeClosure(row.id)
    ElMessage.success(t('common.success'))
    fetchList()
  } catch {
    /* cancelled */
  }
}

async function handleExport() {
  try {
    const blob = await exportClosures()
    const url = URL.createObjectURL(blob instanceof Blob ? blob : new Blob([blob]))
    const link = document.createElement('a')
    link.href = url
    link.download = 'closure_applications.csv'
    link.click()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error(t('common.loadFailed'))
  }
}

onMounted(fetchList)
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>{{ t('closure.manageTitle') }}</span>
        <div class="actions">
          <el-select v-model="status" style="width: 160px" @change="fetchList">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-button @click="handleExport">{{ t('closure.export') }}</el-button>
        </div>
      </div>
    </template>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="tenant_name" :label="t('tenant.name')" min-width="140" />
      <el-table-column prop="reason" :label="t('closure.reason')" min-width="160" show-overflow-tooltip />
      <el-table-column prop="status_label" :label="t('closure.status')" width="110" />
      <el-table-column prop="created_at" :label="t('common.createTime')" width="170">
        <template #default="{ row }">{{ String(row.created_at || '').replace('T', ' ').slice(0, 19) }}</template>
      </el-table-column>
      <el-table-column :label="t('common.actions')" width="260" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="router.push(`/system/closures/${row.id}`)">
            {{ t('common.detail') }}
          </el-button>
          <el-button v-if="row.status === 'pending'" link type="success" @click="handleApprove(row)">
            {{ t('closure.approve') }}
          </el-button>
          <el-button v-if="row.status === 'pending'" link type="danger" @click="handleReject(row)">
            {{ t('closure.reject') }}
          </el-button>
          <el-button v-if="row.status === 'notice_period'" link type="danger" @click="handleComplete(row)">
            {{ t('closure.complete') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.actions {
  display: flex;
  gap: 8px;
}
</style>
