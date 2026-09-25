<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  checkTenantField,
  createTenant,
  deleteTenant,
  updateTenant,
} from '@/api/tenant'
import { validateTenantName } from '@/utils/tenantName'
import { getDepartmentFlatList } from '@/api/department'
import TableActionMenu from '@/components/TableActionMenu.vue'
import { useTenantRoles } from '@/composables/useTenantRoles'
import { ACTION_COLUMN } from '@/config/table'
import { useTenantStore } from '@/stores/tenant'

const { t } = useI18n()
const router = useRouter()
const tenantStore = useTenantStore()
const { canCreate, canDelete } = useTenantRoles()

const STATUS_META = {
  pending: { type: 'warning', labelKey: 'tenant.statusPending' },
  active: { type: 'success', labelKey: 'tenant.statusActive' },
  suspended: { type: 'warning', labelKey: 'tenant.statusSuspended' },
  closed: { type: 'danger', labelKey: 'tenant.statusClosed' },
}

const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const departments = ref([])
const tableData = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ keyword: '', status: '' })
const fieldErrors = reactive({ contact_phone: '', name: '', contact_name: '' })
const fieldWarnings = reactive({ name: '' })
const fieldValid = reactive({ contact_phone: false })

const form = reactive({
  id: null,
  name: '',
  code: '',
  contact_name: '',
  contact_phone: '',
  contact_email: '',
  address: '',
  department: null,
})

const stats = computed(() => tenantStore.stats)

const statusOptions = computed(() => [
  { label: t('common.all'), value: '' },
  { label: t('tenant.statusPending'), value: 'pending' },
  { label: t('tenant.statusActive'), value: 'active' },
  { label: t('tenant.statusSuspended'), value: 'suspended' },
  { label: t('tenant.statusClosed'), value: 'closed' },
])

const dialogTitle = computed(() => (
  form.id ? t('tenant.editTitle') : t('tenant.createTitle')
))

const rules = computed(() => ({
  name: [
    { required: true, message: t('tenant.nameRequired'), trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        const formatError = validateTenantName(value)
        if (formatError) {
          callback(new Error(formatError))
          return
        }
        if (fieldErrors.name) {
          callback(new Error(fieldErrors.name))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
  contact_name: [
    { required: true, message: t('tenant.contactRequired'), trigger: 'blur' },
    {
      validator: (_rule, _value, callback) => {
        if (fieldErrors.contact_name) {
          callback(new Error(fieldErrors.contact_name))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  contact_phone: [
    { required: true, message: t('tenant.phoneRequired'), trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: t('tenant.phoneInvalid'), trigger: 'blur' },
    {
      validator: (_rule, _value, callback) => {
        if (fieldErrors.contact_phone) {
          callback(new Error(fieldErrors.contact_phone))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  contact_email: [
    { required: true, message: t('tenant.emailRequired'), trigger: 'blur' },
    { type: 'email', message: t('tenant.emailInvalid'), trigger: 'blur' },
  ],
}))

async function checkField(field, value) {
  if (!value) {
    fieldErrors[field] = ''
    if (field === 'contact_phone') {
      fieldValid[field] = false
    }
    return
  }
  try {
    const res = await checkTenantField({
      field,
      value,
      exclude_id: form.id || undefined,
    })
    const data = res.data || {}
    if (data.errors?.length) {
      fieldErrors[field] = data.errors[0]
      if (field === 'name') fieldWarnings.name = ''
      if (field === 'contact_phone') {
        fieldValid[field] = false
      }
    } else {
      fieldErrors[field] = ''
      if (field === 'name') {
        fieldWarnings.name = data.warnings?.[0] || ''
      }
      if (field === 'contact_phone') {
        fieldValid[field] = true
      }
    }
    formRef.value?.validateField(field)
  } catch {
    fieldErrors[field] = ''
    if (field === 'contact_phone') {
      fieldValid[field] = false
    }
  }
}

function clearFieldState() {
  fieldErrors.contact_phone = ''
  fieldErrors.name = ''
  fieldErrors.contact_name = ''
  fieldWarnings.name = ''
  fieldValid.contact_phone = false
}

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

function statusTag(status) {
  const meta = STATUS_META[status] || { type: 'info', labelKey: status }
  return { type: meta.type, label: t(meta.labelKey) }
}

async function fetchDepartments() {
  const res = await getDepartmentFlatList()
  departments.value = res.data || []
}

async function fetchList() {
  loading.value = true
  try {
    const data = await tenantStore.fetchList({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
    })
    tableData.value = data.results || []
    pagination.total = data.count || 0
  } finally {
    loading.value = false
  }
}

async function refreshAll() {
  await Promise.all([tenantStore.fetchStats(), fetchList()])
}

function handleSearch() {
  pagination.page = 1
  refreshAll()
}

function resetForm() {
  form.id = null
  form.name = ''
  form.code = ''
  form.contact_name = ''
  form.contact_phone = ''
  form.contact_email = ''
  form.address = ''
  form.department = null
  clearFieldState()
}

function handleCreate() {
  resetForm()
  dialogVisible.value = true
}

function handleEdit(row) {
  form.id = row.id
  form.name = row.name
  form.code = row.code
  form.contact_name = row.contact_name
  form.contact_phone = row.contact_phone
  form.contact_email = row.contact_email
  form.address = row.address || ''
  form.department = row.department || null
  dialogVisible.value = true
}

function handleView(row) {
  router.push({ name: 'TenantDetail', params: { id: row.id } })
}

async function handleDelete(row) {
  await ElMessageBox.confirm(
    t('tenant.deleteConfirm', { name: row.name }),
    t('common.tip'),
    { type: 'warning' },
  )
  await deleteTenant(row.id)
  ElMessage.success(t('common.deleteSuccess'))
  refreshAll()
}

function buildRowActions(row) {
  const actions = [
    {
      label: t('tenant.viewDetail'),
      onClick: () => handleView(row),
    },
  ]
  if (canCreate.value) {
    actions.push({
      label: t('common.edit'),
      onClick: () => handleEdit(row),
    })
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

async function handleSubmit() {
  await formRef.value.validate()
  if (fieldErrors.contact_phone || fieldErrors.name || fieldErrors.contact_name) {
    ElMessage.error(fieldErrors.contact_phone || fieldErrors.name || fieldErrors.contact_name)
    return
  }
  if (fieldWarnings.name) {
    try {
      await ElMessageBox.confirm(fieldWarnings.name, t('common.tip'), {
        type: 'warning',
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
      })
    } catch {
      return
    }
  }
  const payload = {
    name: form.name,
    contact_name: form.contact_name,
    contact_phone: form.contact_phone,
    contact_email: form.contact_email,
    address: form.address,
    department: form.department,
  }
  if (form.id) {
    await updateTenant(form.id, payload)
    ElMessage.success(t('common.updateSuccess'))
  } else {
    await createTenant(payload)
    ElMessage.success(t('common.createSuccess'))
  }
  dialogVisible.value = false
  refreshAll()
}

onMounted(async () => {
  await fetchDepartments()
  await refreshAll()
})
</script>

<template>
  <div class="tenant-page">
    <el-row :gutter="20" class="stat-cards">
      <el-col :xs="12" :sm="6">
        <el-card shadow="never">
          <div class="stat-number">{{ stats.total }}</div>
          <div class="stat-label">{{ t('tenant.statTotal') }}</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never" :class="{ 'stat-pending-alert': stats.pending > 0 }">
          <div class="stat-number stats-pending">
            <span v-if="stats.pending > 0" class="pending-dot" />
            {{ stats.pending }}
          </div>
          <div class="stat-label">{{ t('tenant.statPending') }}</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never">
          <div class="stat-number stats-active">{{ stats.active }}</div>
          <div class="stat-label">{{ t('tenant.statActive') }}</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never">
          <div class="stat-number stats-suspended">{{ stats.suspended }}</div>
          <div class="stat-label">{{ t('tenant.statSuspended') }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="list-card">
      <template #header>
        <div class="card-header">
          <span>{{ t('tenant.listTitle') }}</span>
          <el-button v-if="canCreate" type="primary" @click="handleCreate">
            {{ t('tenant.createTitle') }}
          </el-button>
        </div>
      </template>

      <div class="filter-bar">
        <el-input
          v-model="filters.keyword"
          :placeholder="t('tenant.searchPlaceholder')"
          clearable
          style="width: 240px"
          @keyup.enter="handleSearch"
        />
        <el-select
          v-model="filters.status"
          :placeholder="t('tenant.statusFilter')"
          clearable
          style="width: 160px"
        >
          <el-option
            v-for="item in statusOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <el-button type="primary" @click="handleSearch">{{ t('common.search') }}</el-button>
      </div>

      <el-table v-loading="loading" :data="tableData" border>
        <el-table-column prop="name" :label="t('tenant.name')" min-width="140">
          <template #default="{ row }">
            <span class="tenant-name-cell">
              <span v-if="row.status === 'pending'" class="pending-dot" title="待审核" />
              {{ row.name }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="code" :label="t('tenant.code')" width="120" />
        <el-table-column prop="contact_name" :label="t('tenant.contactName')" width="100" />
        <el-table-column prop="contact_phone" :label="t('tenant.contactPhone')" width="130" />
        <el-table-column :label="t('tenant.status')" width="110">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status).type">{{ statusTag(row.status).label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('tenant.appliedAt')" width="170">
          <template #default="{ row }">{{ formatDate(row.applied_at) }}</template>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item :label="t('tenant.name')" prop="name">
          <el-input v-model="form.name" @blur="checkField('name', form.name)" />
          <div class="field-hint">{{ t('tenant.nameHint') }}</div>
          <div v-if="fieldWarnings.name" class="field-warning">{{ fieldWarnings.name }}</div>
        </el-form-item>
        <el-form-item v-if="form.id" :label="t('tenant.code')">
          <el-input v-model="form.code" disabled />
          <div class="form-tip">{{ t('tenant.codeReadonlyTip') }}</div>
        </el-form-item>
        <el-form-item v-else :label="t('tenant.code')">
          <el-input :model-value="t('tenant.codeAutoGenerate')" disabled />
          <div class="form-tip">{{ t('tenant.codeAutoGenerateTip') }}</div>
        </el-form-item>
        <el-form-item :label="t('tenant.contactName')" prop="contact_name">
          <el-input v-model="form.contact_name" @blur="checkField('contact_name', form.contact_name)" />
        </el-form-item>
        <el-form-item :label="t('tenant.contactPhone')" prop="contact_phone">
          <el-input
            v-model="form.contact_phone"
            @blur="checkField('contact_phone', form.contact_phone)"
          />
          <div v-if="fieldErrors.contact_phone" class="field-error">{{ fieldErrors.contact_phone }}</div>
          <div v-else-if="fieldValid.contact_phone" class="field-valid">{{ t('tenant.phoneAvailable') }}</div>
        </el-form-item>
        <el-form-item :label="t('tenant.contactEmail')" prop="contact_email">
          <el-input v-model="form.contact_email" />
        </el-form-item>
        <el-form-item :label="t('tenant.address')">
          <el-input v-model="form.address" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item :label="t('tenant.department')">
          <el-select
            v-model="form.department"
            clearable
            filterable
            :placeholder="t('tenant.selectDepartment')"
            style="width: 100%"
          >
            <el-option
              v-for="dept in departments"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
          <div class="form-tip">{{ t('tenant.departmentTip') }}</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.stat-cards {
  margin-bottom: 16px;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  margin-top: 6px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.stats-pending {
  color: #e6a23c;
}

.stats-active {
  color: #67c23a;
}

.stats-suspended {
  color: #f56c6c;
}

.stat-pending-alert {
  border-color: #fde2a8;
  background: #fffbf0;
}

.pending-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-right: 6px;
  border-radius: 50%;
  background: #f56c6c;
  vertical-align: middle;
}

.tenant-name-cell {
  display: inline-flex;
  align-items: center;
}

.list-card {
  margin-top: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.field-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

.field-warning {
  margin-top: 4px;
  font-size: 12px;
  color: #e6a23c;
  line-height: 1.5;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.field-error {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 4px;
}

.field-valid {
  color: #67c23a;
  font-size: 12px;
  margin-top: 4px;
}

.field-warning {
  color: #e6a23c;
  font-size: 12px;
  margin-top: 4px;
}
</style>
