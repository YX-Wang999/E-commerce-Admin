<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTenantChangeLogs, reviewTenantChange } from '@/api/tenantChange'
import { useTenantRoles } from '@/composables/useTenantRoles'

const props = defineProps({
  tenantId: { type: [Number, String], required: true },
  compact: { type: Boolean, default: false },
})

const emit = defineEmits(['reviewed'])
const { t } = useI18n()
const { canReviewChanges } = useTenantRoles()

const loading = ref(false)
const logs = ref([])
const statusFilter = ref('')

const STATUS_MAP = {
  pending: { label: '待审核', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' },
}

async function fetchLogs() {
  if (!props.tenantId) return
  loading.value = true
  try {
    const res = await getTenantChangeLogs(props.tenantId, {
      page: 1,
      page_size: props.compact ? 10 : 50,
      status: statusFilter.value || undefined,
    })
    logs.value = res.data?.results || res.data || []
  } catch {
    logs.value = []
  } finally {
    loading.value = false
  }
}

async function handleReview(row, action) {
  let remark = ''
  if (action === 'reject') {
    const { value } = await ElMessageBox.prompt('请输入驳回原因（可选）', '驳回变更', {
      confirmButtonText: '确认驳回',
      cancelButtonText: '取消',
      inputPlaceholder: '审核备注',
    }).catch(() => ({ value: null }))
    if (value === null) return
    remark = value || ''
  } else {
    await ElMessageBox.confirm(`确认通过「${row.field_label}」变更？`, '审核通过', { type: 'warning' })
  }
  await reviewTenantChange(props.tenantId, row.id, { action, remark })
  ElMessage.success(action === 'approve' ? '已通过' : '已驳回')
  await fetchLogs()
  emit('reviewed')
}

const pendingCount = computed(() => logs.value.filter((item) => item.status === 'pending').length)

onMounted(fetchLogs)

watch(() => props.tenantId, () => {
  if (props.tenantId) fetchLogs()
})

defineExpose({ refresh: fetchLogs, pendingCount })
</script>

<template>
  <div v-loading="loading" class="change-review-panel">
    <div v-if="!compact" class="panel-toolbar">
      <el-radio-group v-model="statusFilter" @change="fetchLogs">
        <el-radio-button label="">{{ t('common.all') }}</el-radio-button>
        <el-radio-button label="pending">待审核</el-radio-button>
        <el-radio-button label="approved">已通过</el-radio-button>
        <el-radio-button label="rejected">已驳回</el-radio-button>
      </el-radio-group>
      <el-button @click="fetchLogs">{{ t('common.refresh') }}</el-button>
    </div>

    <el-table :data="logs" border empty-text="暂无变更记录">
      <el-table-column prop="field_label" label="字段" width="120" />
      <el-table-column prop="old_value" label="原值" min-width="140" show-overflow-tooltip />
      <el-table-column prop="new_value" label="新值" min-width="140" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="STATUS_MAP[row.status]?.type || 'info'" size="small">
            {{ STATUS_MAP[row.status]?.label || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="operator_name" label="提交人" width="100" />
      <el-table-column label="提交时间" width="170">
        <template #default="{ row }">{{ new Date(row.created_at).toLocaleString() }}</template>
      </el-table-column>
      <el-table-column prop="review_remark" label="审核备注" min-width="120" show-overflow-tooltip />
      <el-table-column v-if="canReviewChanges" label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'pending'">
            <el-button link type="success" @click="handleReview(row, 'approve')">通过</el-button>
            <el-button link type="danger" @click="handleReview(row, 'reject')">驳回</el-button>
          </template>
          <span v-else>-</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.panel-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 12px;
  flex-wrap: wrap;
}
</style>
