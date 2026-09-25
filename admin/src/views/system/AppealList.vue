<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { getAppealList, replyAppeal } from '@/api/appeal'
import TableActionMenu from '@/components/TableActionMenu.vue'
import { ACTION_COLUMN } from '@/config/table'

const { t } = useI18n()
const authStore = useAuthStore()

const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ keyword: '', status: '' })

const detailVisible = ref(false)
const replyVisible = ref(false)
const currentRow = ref(null)
const replyFormRef = ref(null)
const replyForm = reactive({
  reply: '',
  status: 'resolved',
})

const roleCodes = computed(() => authStore.user?.roles?.map((item) => item.code) || [])
const canReply = computed(() => {
  if (authStore.user?.is_superuser) return true
  return roleCodes.value.includes('ops_director') || roleCodes.value.includes('super_admin')
})

const STATUS_MAP = computed(() => ({
  pending: { label: t('appeal.statusPending'), type: 'warning' },
  processing: { label: t('appeal.statusProcessing'), type: '' },
  resolved: { label: t('appeal.statusResolved'), type: 'success' },
  rejected: { label: t('appeal.statusRejected'), type: 'danger' },
}))

const statusOptions = computed(() => [
  { label: t('common.all'), value: '' },
  { label: t('appeal.statusPending'), value: 'pending' },
  { label: t('appeal.statusProcessing'), value: 'processing' },
  { label: t('appeal.statusResolved'), value: 'resolved' },
  { label: t('appeal.statusRejected'), value: 'rejected' },
])

const replyRules = computed(() => ({
  reply: [{ required: true, message: t('appeal.replyRequired'), trigger: 'blur' }],
  status: [{ required: true, message: t('appeal.statusRequired'), trigger: 'change' }],
}))

async function fetchList() {
  loading.value = true
  try {
    const res = await getAppealList({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
    })
    tableData.value = res.data.results || []
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

function openDetail(row) {
  currentRow.value = row
  detailVisible.value = true
}

function openReply(row) {
  currentRow.value = row
  replyForm.reply = row.reply || ''
  replyForm.status = row.status === 'pending' ? 'resolved' : row.status
  replyVisible.value = true
}

async function submitReply() {
  await replyFormRef.value?.validate()
  await replyAppeal(currentRow.value.id, {
    reply: replyForm.reply,
    status: replyForm.status,
  })
  ElMessage.success(t('appeal.replySuccess'))
  replyVisible.value = false
  detailVisible.value = false
  fetchList()
}

function buildRowActions(row) {
  const actions = [{ label: t('common.detail'), onClick: () => openDetail(row) }]
  if (canReply.value && ['pending', 'processing'].includes(row.status)) {
    actions.push({
      label: t('appeal.reply'),
      type: 'primary',
      onClick: () => openReply(row),
    })
  }
  return actions
}

onMounted(fetchList)
</script>

<template>
  <div class="appeal-page">
    <el-card shadow="never">
      <template #header>
        <span>{{ t('appeal.listTitle') }}</span>
      </template>

      <div class="filter-bar">
        <el-input
          v-model="filters.keyword"
          :placeholder="t('appeal.searchPlaceholder')"
          clearable
          style="width: 240px"
          @keyup.enter="handleSearch"
        />
        <el-select v-model="filters.status" clearable :placeholder="t('appeal.statusFilter')" style="width: 160px">
          <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-button type="primary" @click="handleSearch">{{ t('common.search') }}</el-button>
      </div>

      <el-table v-loading="loading" :data="tableData" border>
        <el-table-column prop="tenant_name" :label="t('appeal.tenantName')" min-width="140" />
        <el-table-column prop="tenant_phone" :label="t('appeal.tenantPhone')" width="130" />
        <el-table-column prop="title" :label="t('appeal.title')" min-width="180" show-overflow-tooltip />
        <el-table-column :label="t('appeal.status')" width="110">
          <template #default="{ row }">
            <el-tag :type="STATUS_MAP[row.status]?.type">{{ STATUS_MAP[row.status]?.label || row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('appeal.createdAt')" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column
          :label="t('common.actions')"
          :min-width="ACTION_COLUMN.promotion"
          class-name="col-actions"
          fixed="right"
        >
          <template #default="{ row }">
            <TableActionMenu :actions="buildRowActions(row)" />
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="fetchList"
          @size-change="handleSearch"
        />
      </div>
    </el-card>

    <el-dialog v-model="detailVisible" :title="t('appeal.detailTitle')" width="640px">
      <el-descriptions v-if="currentRow" :column="1" border>
        <el-descriptions-item :label="t('appeal.tenantName')">{{ currentRow.tenant_name }}</el-descriptions-item>
        <el-descriptions-item :label="t('appeal.tenantPhone')">{{ currentRow.tenant_phone }}</el-descriptions-item>
        <el-descriptions-item :label="t('appeal.title')">{{ currentRow.title }}</el-descriptions-item>
        <el-descriptions-item :label="t('appeal.content')">
          <div class="content-block">{{ currentRow.content }}</div>
        </el-descriptions-item>
        <el-descriptions-item :label="t('appeal.status')">
          <el-tag :type="STATUS_MAP[currentRow.status]?.type">
            {{ STATUS_MAP[currentRow.status]?.label || currentRow.status }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="t('appeal.platformReply')">
          {{ currentRow.reply || '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('appeal.createdAt')">{{ formatDate(currentRow.created_at) }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button
          v-if="canReply && currentRow && ['pending', 'processing'].includes(currentRow.status)"
          type="primary"
          @click="openReply(currentRow)"
        >
          {{ t('appeal.reply') }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="replyVisible" :title="t('appeal.replyTitle')" width="560px">
      <el-form ref="replyFormRef" :model="replyForm" :rules="replyRules" label-width="90px">
        <el-form-item :label="t('appeal.replyContent')" prop="reply">
          <el-input v-model="replyForm.reply" type="textarea" :rows="5" />
        </el-form-item>
        <el-form-item :label="t('appeal.status')" prop="status">
          <el-select v-model="replyForm.status" style="width: 100%">
            <el-option :label="t('appeal.statusProcessing')" value="processing" />
            <el-option :label="t('appeal.statusResolved')" value="resolved" />
            <el-option :label="t('appeal.statusRejected')" value="rejected" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="replyVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitReply">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.content-block {
  white-space: pre-wrap;
  line-height: 1.6;
}
</style>
