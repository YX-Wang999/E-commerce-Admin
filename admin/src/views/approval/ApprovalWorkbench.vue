<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  approveApproval,
  batchApproveApprovals,
  getApprovalDetail,
  getApprovals,
  getApprovalSummary,
  rejectApproval,
} from '@/api/approval'

const { t } = useI18n()
const router = useRouter()
const loading = ref(false)
const detailLoading = ref(false)
const tableData = ref([])
const summary = ref({ pending_total: 0, groups: [] })
const selectedIds = ref([])
const detailVisible = ref(false)
const detail = ref(null)

const filters = reactive({
  approval_type: '',
  status: 'pending',
  keyword: '',
})

const typeOptions = computed(() => [
  { value: '', label: t('common.all') },
  ...(summary.value.groups || []).map((item) => ({
    value: item.approval_type,
    label: `${item.label} (${item.count})`,
  })),
])

async function fetchSummary() {
  const res = await getApprovalSummary()
  summary.value = res.data || { pending_total: 0, groups: [] }
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getApprovals({
      page_size: 50,
      approval_type: filters.approval_type || undefined,
      status: filters.status || undefined,
      keyword: filters.keyword || undefined,
    })
    tableData.value = res.data?.results || res.data || []
  } finally {
    loading.value = false
  }
}

async function openDetail(row) {
  detailVisible.value = true
  detailLoading.value = true
  try {
    const res = await getApprovalDetail(row.id)
    detail.value = res.data
  } finally {
    detailLoading.value = false
  }
}

async function handleApprove(row) {
  try {
    const payload = {}
    if (row.approval_type === 'closure') {
      const { value } = await ElMessageBox.prompt(t('approval.noticeDaysPrompt'), t('approval.approve'), {
        inputValue: '15',
      })
      payload.notice_days = Number(value) || 15
    }
    await approveApproval(row.id, payload)
    ElMessage.success(t('common.success'))
    detailVisible.value = false
    await Promise.all([fetchSummary(), fetchList()])
  } catch {
    /* cancelled */
  }
}

async function handleReject(row) {
  try {
    const { value } = await ElMessageBox.prompt(t('approval.rejectPrompt'), t('approval.reject'), {
      inputValidator: (val) => Boolean(val?.trim()) || t('approval.rejectRequired'),
    })
    await rejectApproval(row.id, { reject_reason: value })
    ElMessage.success(t('common.success'))
    detailVisible.value = false
    await Promise.all([fetchSummary(), fetchList()])
  } catch {
    /* cancelled */
  }
}

async function handleBatchApprove() {
  if (!selectedIds.value.length) {
    ElMessage.warning(t('approval.selectFirst'))
    return
  }
  try {
    await ElMessageBox.confirm(t('approval.batchConfirm', { count: selectedIds.value.length }), t('approval.batchApprove'))
    await batchApproveApprovals(selectedIds.value)
    ElMessage.success(t('common.success'))
    selectedIds.value = []
    await Promise.all([fetchSummary(), fetchList()])
  } catch {
    /* cancelled */
  }
}

function goBusiness(row) {
  if (row.action_url) {
    router.push(row.action_url)
  }
}

function priorityTagType(priority) {
  if (priority === 'urgent') return 'danger'
  if (priority === 'high') return 'warning'
  return 'info'
}

onMounted(async () => {
  await fetchSummary()
  await fetchList()
})
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>{{ t('approval.title') }}</span>
        <el-tag type="danger" v-if="summary.pending_total">{{ t('approval.pendingCount', { count: summary.pending_total }) }}</el-tag>
      </div>
    </template>

    <div class="summary-grid">
      <el-card
        v-for="item in summary.groups"
        :key="item.approval_type"
        shadow="hover"
        class="summary-card"
        @click="filters.approval_type = item.approval_type; fetchList()"
      >
        <div class="summary-count">{{ item.count }}</div>
        <div class="summary-label">{{ item.label }}</div>
      </el-card>
      <el-empty v-if="!summary.groups?.length" :description="t('approval.noPending')" />
    </div>

    <div class="toolbar">
      <el-select v-model="filters.approval_type" clearable style="width: 180px" @change="fetchList">
        <el-option v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-select v-model="filters.status" style="width: 140px" @change="fetchList">
        <el-option value="pending" :label="t('approval.statusPending')" />
        <el-option value="approved" :label="t('approval.statusApproved')" />
        <el-option value="rejected" :label="t('approval.statusRejected')" />
      </el-select>
      <el-input
        v-model="filters.keyword"
        clearable
        :placeholder="t('approval.keywordPlaceholder')"
        style="width: 220px"
        @keyup.enter="fetchList"
      />
      <el-button type="primary" @click="fetchList">{{ t('common.search') }}</el-button>
      <el-button
        v-if="filters.status === 'pending'"
        type="success"
        :disabled="!selectedIds.length"
        @click="handleBatchApprove"
      >
        {{ t('approval.batchApprove') }}
      </el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
      @selection-change="(rows) => (selectedIds = rows.map((row) => row.id))"
    >
      <el-table-column v-if="filters.status === 'pending'" type="selection" width="48" />
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="approval_type_label" :label="t('approval.type')" width="120" />
      <el-table-column prop="title" :label="t('approval.itemTitle')" min-width="200" show-overflow-tooltip />
      <el-table-column prop="summary" :label="t('approval.summary')" min-width="180" show-overflow-tooltip />
      <el-table-column prop="priority_label" :label="t('approval.priority')" width="90">
        <template #default="{ row }">
          <el-tag :type="priorityTagType(row.priority)" size="small">{{ row.priority_label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status_label" :label="t('approval.status')" width="100" />
      <el-table-column prop="created_at" :label="t('common.createTime')" width="170">
        <template #default="{ row }">{{ String(row.created_at || '').replace('T', ' ').slice(0, 19) }}</template>
      </el-table-column>
      <el-table-column :label="t('common.actions')" width="260" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">{{ t('common.detail') }}</el-button>
          <el-button v-if="row.action_url" link @click="goBusiness(row)">{{ t('approval.goBusiness') }}</el-button>
          <template v-if="row.status === 'pending'">
            <el-button link type="success" @click="handleApprove(row)">{{ t('approval.approve') }}</el-button>
            <el-button link type="danger" @click="handleReject(row)">{{ t('approval.reject') }}</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <el-drawer v-model="detailVisible" :title="t('approval.detailTitle')" size="480px">
      <div v-loading="detailLoading">
        <template v-if="detail">
          <p><strong>{{ t('approval.itemTitle') }}：</strong>{{ detail.title }}</p>
          <p><strong>{{ t('approval.summary') }}：</strong>{{ detail.summary }}</p>
          <p><strong>{{ t('approval.status') }}：</strong>{{ detail.status_label }}</p>
          <el-divider />
          <pre class="json-block">{{ JSON.stringify(detail.application_data || {}, null, 2) }}</pre>
          <el-divider />
          <h4>{{ t('approval.logs') }}</h4>
          <el-timeline>
            <el-timeline-item
              v-for="log in detail.logs || []"
              :key="log.id"
              :timestamp="String(log.created_at || '').replace('T', ' ').slice(0, 19)"
            >
              {{ log.operator_name || t('approval.system') }} — {{ log.action }} — {{ log.remark }}
            </el-timeline-item>
          </el-timeline>
          <div v-if="detail.status === 'pending'" class="drawer-actions">
            <el-button type="success" @click="handleApprove(detail)">{{ t('approval.approve') }}</el-button>
            <el-button type="danger" @click="handleReject(detail)">{{ t('approval.reject') }}</el-button>
          </div>
        </template>
      </div>
    </el-drawer>
  </el-card>
</template>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.summary-card {
  cursor: pointer;
  text-align: center;
}

.summary-count {
  font-size: 28px;
  font-weight: 700;
  color: #409eff;
}

.summary-label {
  margin-top: 4px;
  color: #606266;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.json-block {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 6px;
  font-size: 12px;
  overflow: auto;
}

.drawer-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}
</style>
