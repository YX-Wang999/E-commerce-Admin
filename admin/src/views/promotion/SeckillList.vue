<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { usePromotionRoles } from '@/composables/usePromotionRoles'
import { getProductList } from '@/api/product'
import {
  approveSeckill,
  cancelSeckill,
  createSeckill,
  deleteSeckill,
  getSeckillList,
  rejectSeckill,
  submitSeckill,
  updateSeckill,
} from '@/api/promotion'
import { ACTION_COLUMN } from '@/config/table'

const { t } = useI18n()
const route = useRoute()
const {
  canCreateActivity: canCreate,
  canSubmitActivity: canSubmit,
  canApproveActivity: canApprove,
  canCancelActivity: canCancel,
  canEditActivity: canEdit,
  canDeleteActivity: canDelete,
} = usePromotionRoles()

const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const tableData = ref([])
const productOptions = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ keyword: '', status: '', dateRange: null })

const form = reactive({
  id: null,
  name: '',
  product_ids: [],
  seckill_price: null,
  seckill_stock: 1,
  per_user_limit: 1,
  start_time: '',
  end_time: '',
  warmup_time: '',
})

const dialogTitle = computed(() => (form.id ? t('seckill.edit') : t('seckill.create')))

const STATUS_MAP = computed(() => ({
  pending: { label: t('seckill.statusPending'), type: 'info' },
  reviewing: { label: t('seckill.statusReviewing'), type: 'warning' },
  running: { label: t('seckill.statusRunning'), type: 'success' },
  ended: { label: t('seckill.statusEnded'), type: '' },
  cancelled: { label: t('seckill.statusCancelled'), type: 'danger' },
}))

const rules = computed(() => ({
  name: [{ required: true, message: t('seckill.nameRequired'), trigger: 'blur' }],
  product_ids: [{ required: true, message: t('seckill.productRequired'), trigger: 'change' }],
  seckill_price: [{ required: true, message: t('seckill.priceRequired'), trigger: 'blur' }],
  seckill_stock: [{ required: true, message: t('seckill.stockRequired'), trigger: 'blur' }],
  start_time: [{ required: true, message: t('seckill.startTimeRequired'), trigger: 'change' }],
  end_time: [{ required: true, message: t('seckill.endTimeRequired'), trigger: 'change' }],
}))

function isEditable(row) {
  return ['pending', 'reviewing'].includes(row.status)
}

function buildQueryParams() {
  const params = {
    page: pagination.page,
    page_size: pagination.pageSize,
    keyword: filters.keyword || undefined,
    status: filters.status || undefined,
  }
  if (filters.dateRange?.length === 2) {
    params.start_date = filters.dateRange[0]
    params.end_date = filters.dateRange[1]
  }
  return params
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getSeckillList(buildQueryParams())
    tableData.value = res.data.results || []
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

async function fetchProducts() {
  const res = await getProductList({ page: 1, page_size: 200, status: 'on_sale', all_tenants: 1 })
  productOptions.value = res.data.results || []
}

function resetForm() {
  form.id = null
  form.name = ''
  form.product_ids = []
  form.seckill_price = null
  form.seckill_stock = 1
  form.per_user_limit = 1
  form.start_time = ''
  form.end_time = ''
  form.warmup_time = ''
}

function handleCreate() {
  resetForm()
  dialogVisible.value = true
}

function handleEdit(row) {
  Object.assign(form, {
    id: row.id,
    name: row.name,
    product_ids: row.products?.map((item) => item.id) || [],
    seckill_price: Number(row.seckill_price),
    seckill_stock: row.seckill_stock,
    per_user_limit: row.per_user_limit,
    start_time: row.start_time,
    end_time: row.end_time,
    warmup_time: row.warmup_time || '',
  })
  dialogVisible.value = true
}

function buildPayload() {
  return {
    name: form.name,
    product_ids: form.product_ids,
    seckill_price: form.seckill_price,
    seckill_stock: form.seckill_stock,
    per_user_limit: form.per_user_limit,
    start_time: form.start_time,
    end_time: form.end_time,
    warmup_time: form.warmup_time || null,
  }
}

async function handleSubmitForm() {
  await formRef.value.validate()
  const payload = buildPayload()
  if (form.id) {
    await updateSeckill(form.id, payload)
    ElMessage.success(t('common.updateSuccess'))
  } else {
    await createSeckill(payload)
    ElMessage.success(t('common.createSuccess'))
  }
  dialogVisible.value = false
  fetchList()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(t('seckill.deleteConfirm', { name: row.name }), t('common.tip'), {
    type: 'warning',
  })
  await deleteSeckill(row.id)
  ElMessage.success(t('common.deleteSuccess'))
  fetchList()
}

async function handleSubmitReview(row) {
  await ElMessageBox.confirm(t('seckill.submitConfirm', { name: row.name }), t('common.tip'), {
    type: 'warning',
  })
  await submitSeckill(row.id)
  ElMessage.success(t('seckill.submitSuccess'))
  fetchList()
}

async function handleApprove(row) {
  await ElMessageBox.confirm(t('seckill.approveConfirm', { name: row.name }), t('seckill.auditTitle'), {
    type: 'warning',
  })
  await approveSeckill(row.id)
  ElMessage.success(t('seckill.approveSuccess'))
  fetchList()
}

async function handleReject(row) {
  const { value } = await ElMessageBox.prompt(t('seckill.rejectReasonPlaceholder'), t('seckill.rejectTitle'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    inputPattern: /\S+/,
    inputErrorMessage: t('seckill.rejectReasonRequired'),
  })
  await rejectSeckill(row.id, { reason: value })
  ElMessage.success(t('seckill.rejectSuccess'))
  fetchList()
}

async function handleCancel(row) {
  await ElMessageBox.confirm(t('seckill.cancelConfirm', { name: row.name }), t('common.tip'), {
    type: 'warning',
  })
  await cancelSeckill(row.id)
  ElMessage.success(t('seckill.cancelSuccess'))
  fetchList()
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

function formatProducts(row) {
  return row.products?.map((item) => item.name).join('、') || '-'
}

onMounted(async () => {
  if (route.query.status) {
    filters.status = String(route.query.status)
  }
  await fetchProducts()
  await fetchList()
})
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>{{ t('seckill.listTitle') }}</span>
        <el-button v-if="canCreate" type="primary" :icon="Plus" @click="handleCreate">
          {{ t('seckill.create') }}
        </el-button>
      </div>
    </template>

    <el-form :inline="true" class="filter-form">
      <el-form-item :label="t('common.keyword')">
        <el-input v-model="filters.keyword" clearable :placeholder="t('seckill.name')" style="width: 180px" />
      </el-form-item>
      <el-form-item :label="t('common.status')">
        <el-select v-model="filters.status" :placeholder="t('common.all')" clearable style="width: 130px">
          <el-option :label="t('seckill.statusPending')" value="pending" />
          <el-option :label="t('seckill.statusReviewing')" value="reviewing" />
          <el-option :label="t('seckill.statusRunning')" value="running" />
          <el-option :label="t('seckill.statusEnded')" value="ended" />
          <el-option :label="t('seckill.statusCancelled')" value="cancelled" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('seckill.timeRange')">
        <el-date-picker
          v-model="filters.dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          :start-placeholder="t('seckill.startTime')"
          :end-placeholder="t('seckill.endTime')"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">{{ t('common.search') }}</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="name" :label="t('seckill.name')" min-width="200" show-overflow-tooltip />
      <el-table-column :label="t('seckill.products')" min-width="160" show-overflow-tooltip>
        <template #default="{ row }">{{ formatProducts(row) }}</template>
      </el-table-column>
      <el-table-column prop="seckill_price" :label="t('seckill.seckillPrice')" width="100" />
      <el-table-column prop="seckill_stock" :label="t('seckill.seckillStock')" width="90" />
      <el-table-column prop="per_user_limit" :label="t('seckill.perUserLimit')" width="90" />
      <el-table-column prop="start_time" :label="t('seckill.startTime')" width="170" class-name="col-hide-md" />
      <el-table-column prop="end_time" :label="t('seckill.endTime')" width="170" class-name="col-hide-md" />
      <el-table-column :label="t('common.status')" width="100">
        <template #default="{ row }">
          <el-tag :type="STATUS_MAP[row.status]?.type || 'info'" size="small">
            {{ STATUS_MAP[row.status]?.label || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_by_name" :label="t('seckill.createdBy')" width="100" class-name="col-hide-sm" />
      <el-table-column
        :label="t('common.actions')"
        :min-width="ACTION_COLUMN.promotion"
        class-name="col-actions"
        fixed="right"
      >
        <template #default="{ row }">
          <div class="table-actions">
            <span v-if="canEdit && isEditable(row)" class="table-actions__slot table-actions__slot--edit">
              <el-button link type="primary" @click="handleEdit(row)">{{ t('common.edit') }}</el-button>
            </span>
            <span v-if="canSubmit && row.status === 'pending'" class="table-actions__slot table-actions__slot--md">
              <el-button link type="warning" @click="handleSubmitReview(row)">{{ t('seckill.submit') }}</el-button>
            </span>
            <span v-if="canApprove && row.status === 'reviewing'" class="table-actions__slot table-actions__slot--md">
              <el-button link type="success" @click="handleApprove(row)">{{ t('seckill.approve') }}</el-button>
            </span>
            <span v-if="canApprove && row.status === 'reviewing'" class="table-actions__slot table-actions__slot--md">
              <el-button link type="danger" @click="handleReject(row)">{{ t('seckill.reject') }}</el-button>
            </span>
            <span
              v-if="canCancel && ['pending', 'reviewing', 'running'].includes(row.status)"
              class="table-actions__slot table-actions__slot--md"
            >
              <el-button link type="danger" @click="handleCancel(row)">{{ t('seckill.cancel') }}</el-button>
            </span>
            <span
              v-if="canDelete && ['pending', 'cancelled'].includes(row.status)"
              class="table-actions__slot table-actions__slot--md"
            >
              <el-button link type="danger" @click="handleDelete(row)">{{ t('common.delete') }}</el-button>
            </span>
          </div>
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
  </el-card>

  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="620px" destroy-on-close>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item :label="t('seckill.name')" prop="name">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item :label="t('seckill.products')" prop="product_ids">
        <el-select
          v-model="form.product_ids"
          multiple
          :multiple-limit="3"
          filterable
          :placeholder="t('seckill.productRequired')"
          style="width: 100%"
        >
          <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('seckill.seckillPrice')" prop="seckill_price">
        <el-input-number v-model="form.seckill_price" :min="0.01" :precision="2" style="width: 100%" />
      </el-form-item>
      <el-form-item :label="t('seckill.seckillStock')" prop="seckill_stock">
        <el-input-number v-model="form.seckill_stock" :min="1" style="width: 100%" />
      </el-form-item>
      <el-form-item :label="t('seckill.perUserLimit')">
        <el-input-number v-model="form.per_user_limit" :min="1" style="width: 100%" />
      </el-form-item>
      <el-form-item :label="t('seckill.startTime')" prop="start_time">
        <el-date-picker
          v-model="form.start_time"
          type="datetime"
          value-format="YYYY-MM-DDTHH:mm:ss"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item :label="t('seckill.endTime')" prop="end_time">
        <el-date-picker
          v-model="form.end_time"
          type="datetime"
          value-format="YYYY-MM-DDTHH:mm:ss"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item :label="t('seckill.warmupTime')">
        <el-date-picker
          v-model="form.warmup_time"
          type="datetime"
          value-format="YYYY-MM-DDTHH:mm:ss"
          clearable
          style="width: 100%"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" @click="handleSubmitForm">{{ t('common.confirm') }}</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.filter-form {
  margin-bottom: 16px;
}
.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
