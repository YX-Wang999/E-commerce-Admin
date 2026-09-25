<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPendingChanges, reviewTenantChange } from '@/api/tenantChange'
import { useTenantRoles } from '@/composables/useTenantRoles'

const router = useRouter()
const { t } = useI18n()
const { canReviewChanges } = useTenantRoles()

const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const STATUS_MAP = {
  pending: { label: '待审核', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' },
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getPendingChanges({
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    tableData.value = res.data?.results || []
    pagination.total = res.data?.count || 0
  } finally {
    loading.value = false
  }
}

function goTenant(row) {
  router.push({ name: 'TenantDetail', params: { id: row.tenant }, query: { tab: 'changes' } })
}

async function handleReview(row, action) {
  let remark = ''
  if (action === 'reject') {
    const { value } = await ElMessageBox.prompt('请输入驳回原因（可选）', '驳回变更', {
      confirmButtonText: '确认驳回',
      cancelButtonText: '取消',
    }).catch(() => ({ value: null }))
    if (value === null) return
    remark = value || ''
  } else {
    await ElMessageBox.confirm(`确认通过「${row.field_label}」变更？`, '审核通过', { type: 'warning' })
  }
  await reviewTenantChange(row.tenant, row.id, { action, remark })
  ElMessage.success(action === 'approve' ? '已通过' : '已驳回')
  fetchList()
}

onMounted(fetchList)
</script>

<template>
  <div v-loading="loading" class="pending-changes-page">
    <div class="page-header">
      <h2>待审核变更</h2>
      <el-button @click="fetchList">{{ t('common.refresh') }}</el-button>
    </div>

    <el-table :data="tableData" border>
      <el-table-column prop="tenant_name" label="商户" min-width="140" />
      <el-table-column prop="field_label" label="变更字段" width="120" />
      <el-table-column prop="old_value" label="原值" min-width="120" show-overflow-tooltip />
      <el-table-column prop="new_value" label="新值" min-width="120" show-overflow-tooltip />
      <el-table-column prop="operator_name" label="提交人" width="100" />
      <el-table-column label="提交时间" width="170">
        <template #default="{ row }">{{ new Date(row.created_at).toLocaleString() }}</template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="goTenant(row)">查看商户</el-button>
          <template v-if="canReviewChanges">
            <el-button link type="success" @click="handleReview(row, 'approve')">通过</el-button>
            <el-button link type="danger" @click="handleReview(row, 'reject')">驳回</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, prev, pager, next"
        :total="pagination.total"
        @current-change="fetchList"
      />
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
}

.pager {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
