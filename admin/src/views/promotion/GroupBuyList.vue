<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { usePromotionRoles } from '@/composables/usePromotionRoles'
import { getProductList } from '@/api/product'
import {
  approveGroupBuy,
  cancelGroupBuy,
  createGroupBuy,
  deleteGroupBuy,
  getGroupBuyList,
  rejectGroupBuy,
  submitGroupBuy,
  updateGroupBuy,
} from '@/api/promotion'
import { ACTION_COLUMN } from '@/config/table'

const { t } = useI18n()
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
  product_id: null,
  group_price: null,
  group_size: 3,
  stock: 1,
  per_user_limit: 5,
  group_valid_hours: 24,
  auto_group: false,
  start_time: '',
  end_time: '',
})

const dialogTitle = computed(() => (form.id ? t('groupBuy.edit') : t('groupBuy.create')))

const STATUS_MAP = computed(() => ({
  pending: { label: t('groupBuy.statusPending'), type: 'info' },
  reviewing: { label: t('groupBuy.statusReviewing'), type: 'warning' },
  running: { label: t('groupBuy.statusRunning'), type: 'success' },
  ended: { label: t('groupBuy.statusEnded'), type: '' },
  cancelled: { label: t('groupBuy.statusCancelled'), type: 'danger' },
}))

const rules = computed(() => ({
  name: [{ required: true, message: t('groupBuy.nameRequired'), trigger: 'blur' }],
  product_id: [{ required: true, message: t('groupBuy.productRequired'), trigger: 'change' }],
  group_price: [{ required: true, message: t('groupBuy.priceRequired'), trigger: 'blur' }],
  stock: [{ required: true, message: t('groupBuy.stockRequired'), trigger: 'blur' }],
  start_time: [{ required: true, message: t('groupBuy.startTimeRequired'), trigger: 'change' }],
  end_time: [{ required: true, message: t('groupBuy.endTimeRequired'), trigger: 'change' }],
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
    const res = await getGroupBuyList(buildQueryParams())
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
  Object.assign(form, {
    id: null,
    name: '',
    product_id: null,
    group_price: null,
    group_size: 3,
    stock: 1,
    per_user_limit: 5,
    group_valid_hours: 24,
    auto_group: false,
    start_time: '',
    end_time: '',
  })
}

function handleCreate() {
  resetForm()
  dialogVisible.value = true
}

function handleEdit(row) {
  Object.assign(form, {
    id: row.id,
    name: row.name,
    product_id: row.product?.id || null,
    group_price: Number(row.group_price),
    group_size: row.group_size,
    stock: row.stock,
    per_user_limit: row.per_user_limit,
    group_valid_hours: row.group_valid_hours,
    auto_group: row.auto_group,
    start_time: row.start_time,
    end_time: row.end_time,
  })
  dialogVisible.value = true
}

async function handleSubmitForm() {
  await formRef.value.validate()
  const payload = { ...form }
  delete payload.id
  if (form.id) {
    await updateGroupBuy(form.id, payload)
    ElMessage.success(t('common.updateSuccess'))
  } else {
    await createGroupBuy(payload)
    ElMessage.success(t('common.createSuccess'))
  }
  dialogVisible.value = false
  fetchList()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(t('groupBuy.deleteConfirm', { name: row.name }), t('common.tip'), { type: 'warning' })
  await deleteGroupBuy(row.id)
  ElMessage.success(t('common.deleteSuccess'))
  fetchList()
}

async function handleSubmitReview(row) {
  await ElMessageBox.confirm(t('groupBuy.submitConfirm', { name: row.name }), t('common.tip'), { type: 'warning' })
  await submitGroupBuy(row.id)
  ElMessage.success(t('groupBuy.submitSuccess'))
  fetchList()
}

async function handleApprove(row) {
  await ElMessageBox.confirm(t('groupBuy.approveConfirm', { name: row.name }), t('groupBuy.auditTitle'), { type: 'warning' })
  await approveGroupBuy(row.id)
  ElMessage.success(t('groupBuy.approveSuccess'))
  fetchList()
}

async function handleReject(row) {
  const { value } = await ElMessageBox.prompt(t('groupBuy.rejectReasonPlaceholder'), t('groupBuy.rejectTitle'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    inputPattern: /\S+/,
    inputErrorMessage: t('groupBuy.rejectReasonRequired'),
  })
  await rejectGroupBuy(row.id, { reason: value })
  ElMessage.success(t('groupBuy.rejectSuccess'))
  fetchList()
}

async function handleCancel(row) {
  await ElMessageBox.confirm(t('groupBuy.cancelConfirm', { name: row.name }), t('common.tip'), { type: 'warning' })
  await cancelGroupBuy(row.id)
  ElMessage.success(t('groupBuy.cancelSuccess'))
  fetchList()
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

onMounted(async () => {
  await fetchProducts()
  await fetchList()
})
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>{{ t('groupBuy.listTitle') }}</span>
        <el-button v-if="canCreate" type="primary" :icon="Plus" @click="handleCreate">{{ t('groupBuy.create') }}</el-button>
      </div>
    </template>

    <el-form :inline="true" class="filter-form">
      <el-form-item :label="t('common.keyword')">
        <el-input v-model="filters.keyword" clearable style="width: 180px" />
      </el-form-item>
      <el-form-item :label="t('common.status')">
        <el-select v-model="filters.status" :placeholder="t('common.all')" clearable style="width: 130px">
          <el-option :label="t('groupBuy.statusPending')" value="pending" />
          <el-option :label="t('groupBuy.statusReviewing')" value="reviewing" />
          <el-option :label="t('groupBuy.statusRunning')" value="running" />
          <el-option :label="t('groupBuy.statusEnded')" value="ended" />
          <el-option :label="t('groupBuy.statusCancelled')" value="cancelled" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('groupBuy.timeRange')">
        <el-date-picker v-model="filters.dateRange" type="daterange" value-format="YYYY-MM-DD" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">{{ t('common.search') }}</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="name" :label="t('groupBuy.name')" min-width="200" show-overflow-tooltip />
      <el-table-column :label="t('groupBuy.product')" min-width="140">
        <template #default="{ row }">{{ row.product?.name || '-' }}</template>
      </el-table-column>
      <el-table-column prop="group_price" :label="t('groupBuy.groupPrice')" width="90" />
      <el-table-column prop="group_size" :label="t('groupBuy.groupSize')" width="90" />
      <el-table-column prop="stock" :label="t('groupBuy.stock')" width="80" />
      <el-table-column prop="group_valid_hours" :label="t('groupBuy.validHours')" width="100" />
      <el-table-column :label="t('groupBuy.autoGroup')" width="90">
        <template #default="{ row }">{{ row.auto_group ? t('common.yes') : t('common.no') }}</template>
      </el-table-column>
      <el-table-column :label="t('common.status')" width="100">
        <template #default="{ row }">
          <el-tag :type="STATUS_MAP[row.status]?.type || 'info'" size="small">
            {{ STATUS_MAP[row.status]?.label || row.status }}
          </el-tag>
        </template>
      </el-table-column>
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
              <el-button link type="warning" @click="handleSubmitReview(row)">{{ t('groupBuy.submit') }}</el-button>
            </span>
            <span v-if="canApprove && row.status === 'reviewing'" class="table-actions__slot table-actions__slot--md">
              <el-button link type="success" @click="handleApprove(row)">{{ t('groupBuy.approve') }}</el-button>
            </span>
            <span v-if="canApprove && row.status === 'reviewing'" class="table-actions__slot table-actions__slot--md">
              <el-button link type="danger" @click="handleReject(row)">{{ t('groupBuy.reject') }}</el-button>
            </span>
            <span v-if="canCancel && ['pending', 'reviewing', 'running'].includes(row.status)" class="table-actions__slot table-actions__slot--md">
              <el-button link type="danger" @click="handleCancel(row)">{{ t('groupBuy.cancel') }}</el-button>
            </span>
            <span v-if="canDelete && ['pending', 'cancelled'].includes(row.status)" class="table-actions__slot table-actions__slot--md">
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
    <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
      <el-form-item :label="t('groupBuy.name')" prop="name">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item :label="t('groupBuy.product')" prop="product_id">
        <el-select v-model="form.product_id" filterable :placeholder="t('groupBuy.productRequired')" style="width: 100%">
          <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('groupBuy.groupPrice')" prop="group_price">
        <el-input-number v-model="form.group_price" :min="0.01" :precision="2" style="width: 100%" />
      </el-form-item>
      <el-form-item :label="t('groupBuy.groupSize')">
        <el-input-number v-model="form.group_size" :min="2" style="width: 100%" />
      </el-form-item>
      <el-form-item :label="t('groupBuy.stock')" prop="stock">
        <el-input-number v-model="form.stock" :min="1" style="width: 100%" />
      </el-form-item>
      <el-form-item :label="t('groupBuy.perUserLimit')">
        <el-input-number v-model="form.per_user_limit" :min="1" style="width: 100%" />
      </el-form-item>
      <el-form-item :label="t('groupBuy.validHours')">
        <el-input-number v-model="form.group_valid_hours" :min="1" style="width: 100%" />
      </el-form-item>
      <el-form-item :label="t('groupBuy.autoGroup')">
        <el-switch v-model="form.auto_group" />
      </el-form-item>
      <el-form-item :label="t('groupBuy.startTime')" prop="start_time">
        <el-date-picker v-model="form.start_time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
      </el-form-item>
      <el-form-item :label="t('groupBuy.endTime')" prop="end_time">
        <el-date-picker v-model="form.end_time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" @click="handleSubmitForm">{{ t('common.confirm') }}</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.card-header { display: flex; align-items: center; justify-content: space-between; }
.filter-form { margin-bottom: 16px; }
.pagination { margin-top: 16px; justify-content: flex-end; }
</style>
