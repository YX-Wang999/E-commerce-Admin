<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { usePromotionRoles } from '@/composables/usePromotionRoles'
import { getCategoryList, getProductList } from '@/api/product'
import {
  createCoupon,
  deleteCoupon,
  disableCoupon,
  getCouponList,
  publishCoupon,
  updateCoupon,
} from '@/api/promotion'
import { ACTION_COLUMN } from '@/config/table'

const { t } = useI18n()
const {
  canCreateCoupon: canCreate,
  canEditCoupon: canEdit,
  canPublishCoupon: canPublish,
  canDeleteCoupon: canDelete,
} = usePromotionRoles()

const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const tableData = ref([])
const productOptions = ref([])
const categoryOptions = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ keyword: '', status: '', coupon_type: '' })

const form = reactive({
  id: null,
  name: '',
  coupon_type: 'fixed',
  discount_amount: null,
  discount_rate: null,
  max_discount: null,
  min_amount: 0,
  total_quantity: 100,
  per_user_limit: 1,
  applicable_scope: 'all',
  category_id: null,
  product_ids: [],
  valid_type: 'fixed',
  valid_start: '',
  valid_end: '',
  valid_days: null,
})

const dialogTitle = computed(() => (form.id ? t('coupon.edit') : t('coupon.create')))

const TYPE_OPTIONS = computed(() => [
  { label: t('coupon.typeFixed'), value: 'fixed' },
  { label: t('coupon.typeDiscount'), value: 'discount' },
  { label: t('coupon.typeFree'), value: 'free' },
])

const SCOPE_OPTIONS = computed(() => [
  { label: t('coupon.scopeAll'), value: 'all' },
  { label: t('coupon.scopeCategory'), value: 'category' },
  { label: t('coupon.scopeProduct'), value: 'product' },
])

const VALID_TYPE_OPTIONS = computed(() => [
  { label: t('coupon.validFixed'), value: 'fixed' },
  { label: t('coupon.validAfterReceive'), value: 'after_receive' },
])

const STATUS_MAP = computed(() => ({
  draft: { label: t('coupon.statusDraft'), type: 'info' },
  published: { label: t('coupon.statusPublished'), type: 'success' },
  expired: { label: t('coupon.statusExpired'), type: '' },
  disabled: { label: t('coupon.statusDisabled'), type: 'danger' },
}))

const rules = computed(() => ({
  name: [{ required: true, message: t('coupon.nameRequired'), trigger: 'blur' }],
  total_quantity: [{ required: true, message: t('coupon.totalRequired'), trigger: 'blur' }],
}))

function isEditable(row) {
  return ['draft', 'disabled'].includes(row.status)
}

function couponTypeLabel(type) {
  return TYPE_OPTIONS.value.find((item) => item.value === type)?.label || type
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getCouponList({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
      coupon_type: filters.coupon_type || undefined,
    })
    tableData.value = res.data.results || []
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

async function fetchOptions() {
  const [prodRes, catRes] = await Promise.all([
    getProductList({ page: 1, page_size: 200, status: 'on_sale', all_tenants: 1 }),
    getCategoryList({ page: 1, page_size: 200 }),
  ])
  productOptions.value = prodRes.data.results || []
  categoryOptions.value = catRes.data.results || []
}

function resetForm() {
  Object.assign(form, {
    id: null,
    name: '',
    coupon_type: 'fixed',
    discount_amount: null,
    discount_rate: null,
    max_discount: null,
    min_amount: 0,
    total_quantity: 100,
    per_user_limit: 1,
    applicable_scope: 'all',
    category_id: null,
    product_ids: [],
    valid_type: 'fixed',
    valid_start: '',
    valid_end: '',
    valid_days: null,
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
    coupon_type: row.coupon_type,
    discount_amount: row.discount_amount ? Number(row.discount_amount) : null,
    discount_rate: row.discount_rate ? Number(row.discount_rate) : null,
    max_discount: row.max_discount ? Number(row.max_discount) : null,
    min_amount: Number(row.min_amount),
    total_quantity: row.total_quantity,
    per_user_limit: row.per_user_limit,
    applicable_scope: row.applicable_scope,
    category_id: row.applicable_category || null,
    product_ids: row.applicable_products?.map((item) => item.id) || [],
    valid_type: row.valid_type,
    valid_start: row.valid_start || '',
    valid_end: row.valid_end || '',
    valid_days: row.valid_days,
  })
  dialogVisible.value = true
}

function buildPayload() {
  return {
    name: form.name,
    coupon_type: form.coupon_type,
    discount_amount: form.coupon_type === 'fixed' ? form.discount_amount : null,
    discount_rate: form.coupon_type === 'discount' ? form.discount_rate : null,
    max_discount: form.coupon_type === 'discount' ? form.max_discount : null,
    min_amount: form.min_amount,
    total_quantity: form.total_quantity,
    per_user_limit: form.per_user_limit,
    applicable_scope: form.applicable_scope,
    category_id: form.applicable_scope === 'category' ? form.category_id : null,
    product_ids: form.applicable_scope === 'product' ? form.product_ids : [],
    valid_type: form.valid_type,
    valid_start: form.valid_type === 'fixed' ? form.valid_start : null,
    valid_end: form.valid_type === 'fixed' ? form.valid_end : null,
    valid_days: form.valid_type === 'after_receive' ? form.valid_days : null,
  }
}

async function handleSubmitForm() {
  await formRef.value.validate()
  const payload = buildPayload()
  if (form.id) {
    await updateCoupon(form.id, payload)
    ElMessage.success(t('common.updateSuccess'))
  } else {
    await createCoupon(payload)
    ElMessage.success(t('common.createSuccess'))
  }
  dialogVisible.value = false
  fetchList()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(t('coupon.deleteConfirm', { name: row.name }), t('common.tip'), { type: 'warning' })
  await deleteCoupon(row.id)
  ElMessage.success(t('common.deleteSuccess'))
  fetchList()
}

async function handlePublish(row) {
  await ElMessageBox.confirm(t('coupon.publishConfirm', { name: row.name }), t('common.tip'), { type: 'warning' })
  await publishCoupon(row.id)
  ElMessage.success(t('coupon.publishSuccess'))
  fetchList()
}

async function handleDisable(row) {
  await ElMessageBox.confirm(t('coupon.disableConfirm', { name: row.name }), t('common.tip'), { type: 'warning' })
  await disableCoupon(row.id)
  ElMessage.success(t('coupon.disableSuccess'))
  fetchList()
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

watch(
  () => form.applicable_scope,
  (scope) => {
    if (scope !== 'category') form.category_id = null
    if (scope !== 'product') form.product_ids = []
  },
)

onMounted(async () => {
  await fetchOptions()
  await fetchList()
})
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>{{ t('coupon.listTitle') }}</span>
        <el-button v-if="canCreate" type="primary" :icon="Plus" @click="handleCreate">{{ t('coupon.create') }}</el-button>
      </div>
    </template>

    <el-form :inline="true" class="filter-form">
      <el-form-item :label="t('common.keyword')">
        <el-input v-model="filters.keyword" clearable style="width: 180px" />
      </el-form-item>
      <el-form-item :label="t('coupon.type')">
        <el-select v-model="filters.coupon_type" :placeholder="t('common.all')" clearable style="width: 120px">
          <el-option v-for="item in TYPE_OPTIONS" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('common.status')">
        <el-select v-model="filters.status" :placeholder="t('common.all')" clearable style="width: 120px">
          <el-option :label="t('coupon.statusDraft')" value="draft" />
          <el-option :label="t('coupon.statusPublished')" value="published" />
          <el-option :label="t('coupon.statusExpired')" value="expired" />
          <el-option :label="t('coupon.statusDisabled')" value="disabled" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">{{ t('common.search') }}</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="name" :label="t('coupon.name')" min-width="200" show-overflow-tooltip />
      <el-table-column :label="t('coupon.type')" width="100">
        <template #default="{ row }">{{ couponTypeLabel(row.coupon_type) }}</template>
      </el-table-column>
      <el-table-column prop="min_amount" :label="t('coupon.minAmount')" width="90" />
      <el-table-column :label="t('coupon.discountValue')" width="100">
        <template #default="{ row }">
          <span v-if="row.coupon_type === 'fixed'">{{ row.discount_amount }}</span>
          <span v-else-if="row.coupon_type === 'discount'">{{ row.discount_rate }}%</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="total_quantity" :label="t('coupon.totalQuantity')" width="90" />
      <el-table-column prop="received_count" :label="t('coupon.receivedCount')" width="80" />
      <el-table-column prop="used_count" :label="t('coupon.usedCount')" width="80" />
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
            <span v-if="canPublish && row.status === 'draft'" class="table-actions__slot table-actions__slot--md">
              <el-button link type="success" @click="handlePublish(row)">{{ t('coupon.publish') }}</el-button>
            </span>
            <span v-if="canPublish && row.status === 'published'" class="table-actions__slot table-actions__slot--md">
              <el-button link type="warning" @click="handleDisable(row)">{{ t('coupon.disable') }}</el-button>
            </span>
            <span v-if="canDelete && row.status === 'draft'" class="table-actions__slot table-actions__slot--md">
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

  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="680px" destroy-on-close>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
      <el-form-item :label="t('coupon.name')" prop="name">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item :label="t('coupon.type')">
        <el-select v-model="form.coupon_type" style="width: 100%">
          <el-option v-for="item in TYPE_OPTIONS" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="form.coupon_type === 'fixed'" :label="t('coupon.discountAmount')">
        <el-input-number v-model="form.discount_amount" :min="0.01" :precision="2" style="width: 100%" />
      </el-form-item>
      <template v-if="form.coupon_type === 'discount'">
        <el-form-item :label="t('coupon.discountRate')">
          <el-input-number v-model="form.discount_rate" :min="1" :max="99" :precision="1" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('coupon.maxDiscount')">
          <el-input-number v-model="form.max_discount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
      </template>
      <el-form-item :label="t('coupon.minAmount')">
        <el-input-number v-model="form.min_amount" :min="0" :precision="2" style="width: 100%" />
      </el-form-item>
      <el-form-item :label="t('coupon.totalQuantity')" prop="total_quantity">
        <el-input-number v-model="form.total_quantity" :min="1" style="width: 100%" />
      </el-form-item>
      <el-form-item :label="t('coupon.perUserLimit')">
        <el-input-number v-model="form.per_user_limit" :min="1" style="width: 100%" />
      </el-form-item>
      <el-form-item :label="t('coupon.applicableScope')">
        <el-select v-model="form.applicable_scope" style="width: 100%">
          <el-option v-for="item in SCOPE_OPTIONS" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="form.applicable_scope === 'category'" :label="t('coupon.category')">
        <el-select v-model="form.category_id" filterable style="width: 100%">
          <el-option v-for="item in categoryOptions" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="form.applicable_scope === 'product'" :label="t('coupon.products')">
        <el-select v-model="form.product_ids" multiple filterable style="width: 100%">
          <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('coupon.validType')">
        <el-select v-model="form.valid_type" style="width: 100%">
          <el-option v-for="item in VALID_TYPE_OPTIONS" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </el-form-item>
      <template v-if="form.valid_type === 'fixed'">
        <el-form-item :label="t('coupon.validStart')">
          <el-date-picker v-model="form.valid_start" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('coupon.validEnd')">
          <el-date-picker v-model="form.valid_end" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
        </el-form-item>
      </template>
      <el-form-item v-else :label="t('coupon.validDays')">
        <el-input-number v-model="form.valid_days" :min="1" style="width: 100%" />
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
