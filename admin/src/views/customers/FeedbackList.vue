<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { deleteFeedback, getFeedbackList, replyFeedback } from '@/api/feedback'
import { resolveImageUrl } from '@/utils/media'
import TableActionMenu from '@/components/TableActionMenu.vue'
import { ACTION_COLUMN } from '@/config/table'

const { t } = useI18n()
const route = useRoute()
const authStore = useAuthStore()

const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ keyword: '', feedback_type: '', status: '' })

const replyVisible = ref(false)
const detailVisible = ref(false)
const replyFormRef = ref(null)
const currentRow = ref(null)

const replyForm = reactive({
  status: 'processing',
  handler_remark: '',
})

const roleCodes = computed(() => authStore.user?.roles?.map((item) => item.code) || [])
const isSuper = computed(() => Boolean(authStore.user?.is_superuser))
const canReply = computed(() => {
  if (isSuper.value) return true
  return roleCodes.value.includes('cs_staff')
})
const canDelete = computed(() => isSuper.value || roleCodes.value.includes('super_admin'))

const TYPE_MAP = computed(() => ({
  complaint: { label: t('feedback.typeComplaint'), type: 'danger' },
  suggestion: { label: t('feedback.typeSuggestion'), type: 'success' },
  inquiry: { label: t('feedback.typeInquiry'), type: 'info' },
  after_sales: { label: t('feedback.typeAfterSales'), type: 'warning' },
}))

const STATUS_MAP = computed(() => ({
  pending: { label: t('feedback.statusPending'), type: 'warning' },
  processing: { label: t('feedback.statusProcessing'), type: '' },
  done: { label: t('feedback.statusDone'), type: 'success' },
  closed: { label: t('feedback.statusClosed'), type: 'info' },
}))

const replyRules = computed(() => ({
  status: [{ required: true, message: t('feedback.statusRequired'), trigger: 'change' }],
}))

async function fetchList() {
  loading.value = true
  try {
    const res = await getFeedbackList({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      feedback_type: filters.feedback_type || undefined,
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

function openDetail(row) {
  currentRow.value = row
  detailVisible.value = true
}

function openReply(row) {
  currentRow.value = row
  replyForm.status = row.status === 'pending' ? 'processing' : row.status
  replyForm.handler_remark = row.handler_remark || ''
  replyVisible.value = true
}

async function handleReplySubmit() {
  await replyFormRef.value.validate()
  await replyFeedback(currentRow.value.id, {
    status: replyForm.status,
    handler_remark: replyForm.handler_remark,
  })
  ElMessage.success(t('feedback.replySuccess'))
  replyVisible.value = false
  fetchList()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(
    t('feedback.deleteConfirm', { name: row.nickname }),
    t('common.tip'),
    { type: 'warning' },
  )
  await deleteFeedback(row.id)
  ElMessage.success(t('common.deleteSuccess'))
  fetchList()
}

function buildActions(row) {
  const actions = [{ label: t('common.detail'), onClick: () => openDetail(row) }]
  if (canReply.value) {
    actions.push({ label: t('feedback.reply'), type: 'primary', onClick: () => openReply(row) })
  }
  if (canDelete.value) {
    actions.push({
      label: t('common.delete'),
      type: 'danger',
      danger: true,
      onClick: () => handleDelete(row),
    })
  }
  return actions
}

onMounted(() => {
  if (route.query.status) {
    filters.status = String(route.query.status)
  }
  fetchList()
})
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <span>{{ t('feedback.listTitle') }}</span>
    </template>

    <el-form :inline="true" class="filter-form">
      <el-form-item :label="t('common.keyword')">
        <el-input
          v-model="filters.keyword"
          :placeholder="t('feedback.keywordPlaceholder')"
          clearable
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item :label="t('feedback.type')">
        <el-select
          v-model="filters.feedback_type"
          :placeholder="t('common.all')"
          clearable
          style="width: 120px"
        >
          <el-option :label="t('feedback.typeComplaint')" value="complaint" />
          <el-option :label="t('feedback.typeSuggestion')" value="suggestion" />
          <el-option :label="t('feedback.typeInquiry')" value="inquiry" />
          <el-option :label="t('feedback.typeAfterSales')" value="after_sales" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('common.status')">
        <el-select
          v-model="filters.status"
          :placeholder="t('common.all')"
          clearable
          style="width: 120px"
        >
          <el-option :label="t('feedback.statusPending')" value="pending" />
          <el-option :label="t('feedback.statusProcessing')" value="processing" />
          <el-option :label="t('feedback.statusDone')" value="done" />
          <el-option :label="t('feedback.statusClosed')" value="closed" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">{{ t('common.search') }}</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="nickname" :label="t('feedback.nickname')" width="100" />
      <el-table-column prop="phone" :label="t('feedback.phone')" width="130" />
      <el-table-column :label="t('feedback.type')" width="90">
        <template #default="{ row }">
          <el-tag :type="TYPE_MAP[row.feedback_type]?.type || 'info'" size="small">
            {{ row.feedback_type_label || TYPE_MAP[row.feedback_type]?.label || row.feedback_type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="content"
        :label="t('feedback.content')"
        min-width="200"
        show-overflow-tooltip
      />
      <el-table-column :label="t('common.status')" width="100">
        <template #default="{ row }">
          <el-tag :type="STATUS_MAP[row.status]?.type || 'info'" size="small">
            {{ row.status_label || STATUS_MAP[row.status]?.label || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="handler_name" :label="t('feedback.handler')" width="100" />
      <el-table-column prop="created_at" :label="t('feedback.createdAt')" width="170" class-name="col-hide-md" />
      <el-table-column
        :label="t('common.actions')"
        :min-width="ACTION_COLUMN.standard"
        class-name="col-actions"
        fixed="right"
      >
        <template #default="{ row }">
          <TableActionMenu :actions="buildActions(row)" />
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        background
        @current-change="fetchList"
        @size-change="handleSearch"
      />
    </div>
  </el-card>

  <el-dialog v-model="detailVisible" :title="t('feedback.detailTitle')" width="560px">
    <template v-if="currentRow">
      <el-descriptions :column="1" border>
        <el-descriptions-item :label="t('feedback.nickname')">{{ currentRow.nickname }}</el-descriptions-item>
        <el-descriptions-item :label="t('feedback.phone')">{{ currentRow.phone }}</el-descriptions-item>
        <el-descriptions-item :label="t('feedback.type')">
          {{ currentRow.feedback_type_label || TYPE_MAP[currentRow.feedback_type]?.label }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('feedback.content')">{{ currentRow.content }}</el-descriptions-item>
        <el-descriptions-item v-if="currentRow.images?.length" :label="t('feedback.images')">
          <div class="image-list">
            <el-image
              v-for="(url, idx) in currentRow.images"
              :key="idx"
              :src="resolveImageUrl(url)"
              :preview-src-list="currentRow.images.map(resolveImageUrl)"
              fit="cover"
              class="thumb"
            />
          </div>
        </el-descriptions-item>
        <el-descriptions-item :label="t('common.status')">
          {{ currentRow.status_label || STATUS_MAP[currentRow.status]?.label }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('feedback.handler')">
          {{ currentRow.handler_name || t('common.noData') }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('feedback.handlerRemark')">
          {{ currentRow.handler_remark || t('common.noData') }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('feedback.createdAt')">{{ currentRow.created_at }}</el-descriptions-item>
        <el-descriptions-item :label="t('feedback.handledAt')">
          {{ currentRow.handled_at || t('common.noData') }}
        </el-descriptions-item>
      </el-descriptions>
    </template>
    <template #footer>
      <el-button @click="detailVisible = false">{{ t('common.close') }}</el-button>
      <el-button v-if="canReply" type="primary" @click="detailVisible = false; openReply(currentRow)">
        {{ t('feedback.reply') }}
      </el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="replyVisible" :title="t('feedback.replyTitle')" width="480px">
    <el-form ref="replyFormRef" :model="replyForm" :rules="replyRules" label-width="90px">
      <el-form-item :label="t('common.status')" prop="status">
        <el-select v-model="replyForm.status" style="width: 100%">
          <el-option :label="t('feedback.statusPending')" value="pending" />
          <el-option :label="t('feedback.statusProcessing')" value="processing" />
          <el-option :label="t('feedback.statusDone')" value="done" />
          <el-option :label="t('feedback.statusClosed')" value="closed" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('feedback.handlerRemark')" prop="handler_remark">
        <el-input
          v-model="replyForm.handler_remark"
          type="textarea"
          :rows="4"
          :placeholder="t('feedback.handlerRemarkPlaceholder')"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="replyVisible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" @click="handleReplySubmit">{{ t('common.confirm') }}</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.filter-form {
  margin-bottom: 16px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.image-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.thumb {
  width: 72px;
  height: 72px;
  border-radius: 4px;
}
</style>
