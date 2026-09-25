<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getFeedbackList, replyFeedback } from '@/api/feedback'

const { t } = useI18n()

const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ status: '', feedback_type: '' })

const replyVisible = ref(false)
const replySubmitting = ref(false)
const currentRow = ref(null)
const replyForm = reactive({
  status: 'done',
  handler_remark: '',
})

const TYPE_MAP = computed(() => ({
  suggestion: { label: t('seller.feedbackTypeSuggestion'), type: 'success' },
  inquiry: { label: t('seller.feedbackTypeInquiry'), type: 'info' },
  complaint: { label: t('seller.feedbackTypeComplaint'), type: 'danger' },
  after_sales: { label: t('seller.feedbackTypeAfterSales'), type: 'warning' },
}))

const STATUS_MAP = computed(() => ({
  pending: { label: t('seller.feedbackStatusPending'), type: 'warning' },
  processing: { label: t('seller.feedbackStatusProcessing'), type: '' },
  done: { label: t('seller.feedbackStatusDone'), type: 'success' },
  closed: { label: t('seller.feedbackStatusClosed'), type: 'info' },
}))

async function fetchList() {
  loading.value = true
  try {
    const res = await getFeedbackList({
      page: pagination.page,
      page_size: pagination.pageSize,
      status: filters.status || undefined,
      feedback_type: filters.feedback_type || undefined,
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

function openReply(row) {
  currentRow.value = row
  replyForm.status = row.status === 'pending' ? 'done' : row.status
  replyForm.handler_remark = row.handler_remark || ''
  replyVisible.value = true
}

async function handleReplySubmit() {
  if (!replyForm.handler_remark.trim()) {
    ElMessage.warning(t('seller.feedbackReplyRequired'))
    return
  }
  replySubmitting.value = true
  try {
    await replyFeedback(currentRow.value.id, {
      status: replyForm.status,
      handler_remark: replyForm.handler_remark.trim(),
    })
    ElMessage.success(t('seller.feedbackReplySuccess'))
    replyVisible.value = false
    await fetchList()
  } finally {
    replySubmitting.value = false
  }
}

defineExpose({ fetchList })

onMounted(fetchList)
</script>

<template>
  <div>
    <el-form :inline="true" class="filter-form">
      <el-form-item :label="t('seller.status')">
        <el-select v-model="filters.status" clearable style="width: 140px" @change="handleSearch">
          <el-option :label="t('seller.feedbackStatusPending')" value="pending" />
          <el-option :label="t('seller.feedbackStatusProcessing')" value="processing" />
          <el-option :label="t('seller.feedbackStatusDone')" value="done" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('seller.feedbackType')">
        <el-select v-model="filters.feedback_type" clearable style="width: 140px" @change="handleSearch">
          <el-option :label="t('seller.feedbackTypeSuggestion')" value="suggestion" />
          <el-option :label="t('seller.feedbackTypeInquiry')" value="inquiry" />
          <el-option :label="t('seller.feedbackTypeAfterSales')" value="after_sales" />
        </el-select>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="nickname" :label="t('seller.customer')" width="110" />
      <el-table-column prop="phone" :label="t('seller.phoneLabel')" width="130" />
      <el-table-column :label="t('seller.feedbackType')" width="100">
        <template #default="{ row }">
          <el-tag :type="TYPE_MAP[row.feedback_type]?.type || 'info'" size="small">
            {{ TYPE_MAP[row.feedback_type]?.label || row.feedback_type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="content" :label="t('seller.feedbackContent')" min-width="220" show-overflow-tooltip />
      <el-table-column :label="t('seller.status')" width="100">
        <template #default="{ row }">
          <el-tag :type="STATUS_MAP[row.status]?.type || 'info'" size="small">
            {{ STATUS_MAP[row.status]?.label || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" :label="t('seller.createTime')" width="170" />
      <el-table-column :label="t('seller.actions')" width="100" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'pending' || row.status === 'processing'"
            link
            type="primary"
            @click="openReply(row)"
          >
            {{ t('seller.handle') }}
          </el-button>
          <el-button v-else link type="primary" @click="openReply(row)">
            {{ t('seller.detail') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :total="pagination.total"
      layout="total, prev, pager, next"
      class="pagination"
      @current-change="fetchList"
    />

    <el-dialog v-model="replyVisible" :title="t('seller.feedbackReply')" width="520px" destroy-on-close>
      <div v-if="currentRow" class="dialog-content">{{ currentRow.content }}</div>
      <el-form label-width="80px" class="reply-form">
        <el-form-item :label="t('seller.status')">
          <el-select v-model="replyForm.status" style="width: 100%">
            <el-option :label="t('seller.feedbackStatusProcessing')" value="processing" />
            <el-option :label="t('seller.feedbackStatusDone')" value="done" />
            <el-option :label="t('seller.feedbackStatusClosed')" value="closed" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('seller.feedbackReplyLabel')">
          <el-input
            v-model="replyForm.handler_remark"
            type="textarea"
            :rows="4"
            :placeholder="t('seller.feedbackReplyPlaceholder')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="replyVisible = false">{{ t('seller.appealCancel') }}</el-button>
        <el-button type="primary" :loading="replySubmitting" @click="handleReplySubmit">
          {{ t('seller.feedbackSubmitReply') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.filter-form { margin-bottom: 16px; }
.pagination { margin-top: 16px; justify-content: flex-end; }
.dialog-content {
  margin-bottom: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  line-height: 1.6;
  white-space: pre-wrap;
}
.reply-form { margin-top: 8px; }
</style>
