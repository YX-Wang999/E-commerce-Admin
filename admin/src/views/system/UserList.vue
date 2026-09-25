<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { translateActivationStatus } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { getRoleList } from '@/api/role'
import { getDepartmentFlatList } from '@/api/department'
import { createUser, deleteUser, getUserList, resetPassword, sendActivation, updateUser } from '@/api/user'
import { useRoleLabel } from '@/composables/useRoleLabel'
import { ACTION_COLUMN } from '@/config/table'

const { t, locale } = useI18n()
const authStore = useAuthStore()
const { roleLabels, roleOptionLabel } = useRoleLabel()

const loading = ref(false)
const dialogVisible = ref(false)
const resetDialogVisible = ref(false)
const resetLoading = ref(false)
const activationDialogVisible = ref(false)
const activationUserId = ref(null)
const activationResult = ref(null)
const formRef = ref(null)
const resetFormRef = ref(null)
const tableData = ref([])
const roleOptions = ref([])
const departmentOptions = ref([])
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const form = reactive({
  id: null,
  username: '',
  password: '',
  nickname: '',
  email: '',
  phone: '',
  is_active: true,
  role_ids: [],
  department: null,
})

const resetForm = reactive({
  userId: null,
  username: '',
  new_password: '',
  confirm_password: '',
})

const dialogTitle = computed(() => (form.id ? t('system.user.edit') : t('system.user.create')))

const rules = computed(() => ({
  username: [{ required: true, message: t('login.usernameRequired'), trigger: 'blur' }],
  password: [{ required: true, message: t('login.passwordRequired'), trigger: 'blur' }],
}))

const resetRules = computed(() => {
  const validateResetConfirm = (_rule, value, callback) => {
    if (value !== resetForm.new_password) {
      callback(new Error(t('password.mismatch')))
      return
    }
    callback()
  }

  return {
    new_password: [
      { required: true, message: t('password.newRequired'), trigger: 'blur' },
      { min: 6, message: t('password.minLength'), trigger: 'blur' },
    ],
    confirm_password: [
      { required: true, message: t('password.confirmRequired'), trigger: 'blur' },
      { validator: validateResetConfirm, trigger: 'blur' },
    ],
  }
})

const isAdmin = computed(() => {
  const user = authStore.user
  if (!user) {
    return false
  }
  if (user.is_superuser) {
    return true
  }
  return user.roles?.some((role) => ['admin', 'super_admin'].includes(role.code)) ?? false
})

const activationLinkUrl = computed(() => {
  if (!activationResult.value?.uid || !activationResult.value?.token) {
    return ''
  }
  const { uid, token } = activationResult.value
  return `http://localhost:5173/activate?uid=${uid}&token=${encodeURIComponent(token)}`
})

const ACTIVATION_TAG_TYPES = {
  none: 'info',
  pending: 'warning',
  activated: 'success',
  expired: 'danger',
  failed: 'danger',
}

function getActivationTagType(status) {
  return ACTIVATION_TAG_TYPES[status] || 'info'
}

function formatDateTime(value) {
  if (!value) {
    return '-'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleString(locale.value, { hour12: false })
}

async function fetchRoles() {
  const res = await getRoleList({ page_size: 100 })
  roleOptions.value = res.data.results || res.data || []
}

async function fetchDepartments() {
  const res = await getDepartmentFlatList()
  departmentOptions.value = res.data || []
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getUserList({
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    tableData.value = res.data.results || []
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

function resetFormFields() {
  form.id = null
  form.username = ''
  form.password = ''
  form.nickname = ''
  form.email = ''
  form.phone = ''
  form.is_active = true
  form.role_ids = []
  form.department = null
}

function handleCreate() {
  resetFormFields()
  dialogVisible.value = true
}

function handleEdit(row) {
  form.id = row.id
  form.username = row.username
  form.password = ''
  form.nickname = row.nickname
  form.email = row.email
  form.phone = row.phone
  form.is_active = row.is_active
  form.role_ids = row.roles?.map((item) => item.id) || []
  form.department = row.department || null
  dialogVisible.value = true
}

function handleResetPassword(row) {
  resetForm.userId = row.id
  resetForm.username = row.username
  resetForm.new_password = ''
  resetForm.confirm_password = ''
  resetDialogVisible.value = true
}

async function handleDelete(row) {
  await ElMessageBox.confirm(t('system.user.deleteConfirm', { name: row.username }), t('common.tip'), {
    type: 'warning',
  })
  await deleteUser(row.id)
  ElMessage.success(t('common.deleteSuccess'))
  fetchList()
}

async function handleSubmit() {
  await formRef.value.validate()
  const payload = {
    nickname: form.nickname,
    email: form.email,
    phone: form.phone,
    is_active: form.is_active,
    role_ids: form.role_ids,
    department: form.department,
  }
  if (form.id) {
    if (form.password) {
      payload.password = form.password
    }
    await updateUser(form.id, payload)
    ElMessage.success(t('common.updateSuccess'))
  } else {
    await createUser({
      username: form.username,
      password: form.password,
      ...payload,
    })
    ElMessage.success(t('common.createSuccess'))
  }
  dialogVisible.value = false
  fetchList()
}

async function handleResetSubmit() {
  await resetFormRef.value.validate()
  resetLoading.value = true
  try {
    await resetPassword(resetForm.userId, {
      new_password: resetForm.new_password,
    })
    ElMessage.success(t('system.user.resetSuccess'))
    resetDialogVisible.value = false
  } finally {
    resetLoading.value = false
  }
}

async function handleSendActivation(row) {
  if (!row.email) {
    ElMessage.warning(t('system.user.noEmailWarning'))
    return
  }
  await ElMessageBox.confirm(
    t('system.user.sendActivationConfirm', { username: row.username, email: row.email }),
    t('common.tip'),
    { type: 'info' },
  )
  activationUserId.value = row.id
  try {
    const res = await sendActivation(row.id)
    activationResult.value = res.data
    activationDialogVisible.value = true
    ElMessage.success(t('system.user.activationSent'))
    fetchList()
  } finally {
    activationUserId.value = null
  }
}

async function copyActivationLink() {
  if (!activationLinkUrl.value) {
    return
  }
  await navigator.clipboard.writeText(activationLinkUrl.value)
  ElMessage.success(t('system.user.linkCopied'))
}

onMounted(async () => {
  await Promise.all([fetchRoles(), fetchDepartments()])
  await fetchList()
})
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>{{ t('system.user.title') }}</span>
        <el-button type="primary" @click="handleCreate">{{ t('system.user.create') }}</el-button>
      </div>
    </template>

    <el-table v-loading="loading" :data="tableData" border>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" :label="t('system.user.username')" />
      <el-table-column prop="nickname" :label="t('system.user.nickname')" />
      <el-table-column prop="phone" :label="t('system.user.phone')" class-name="col-hide-md" />
      <el-table-column :label="t('system.user.roles')">
        <template #default="{ row }">
          {{ roleLabels(row.roles) }}
        </template>
      </el-table-column>
      <el-table-column :label="t('system.user.department')" min-width="120">
        <template #default="{ row }">
          {{ row.department_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column :label="t('system.user.activationStatus')" width="140">
        <template #default="{ row }">
          <el-tag :type="getActivationTagType(row.activation_status)">
            {{ translateActivationStatus(row.activation_status, row.activation_status_label) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('system.user.lastSentAt')" width="180" class-name="col-hide-md">
        <template #default="{ row }">
          {{ formatDateTime(row.last_activation_sent_at) }}
        </template>
      </el-table-column>
      <el-table-column :label="t('common.status')" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">
            {{ row.is_active ? t('common.enabled') : t('common.disabled') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="t('common.actions')"
        :min-width="isAdmin ? ACTION_COLUMN.userAdmin : ACTION_COLUMN.userBasic"
        class-name="col-actions"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button link type="primary" @click="handleEdit(row)">{{ t('common.edit') }}</el-button>
          <el-button
            v-if="isAdmin"
            link
            type="success"
            :loading="activationUserId === row.id"
            @click="handleSendActivation(row)"
          >
            {{ t('system.user.sendActivation') }}
          </el-button>
          <el-button v-if="isAdmin" link type="warning" @click="handleResetPassword(row)">
            {{ t('system.user.resetPassword') }}
          </el-button>
          <el-button link type="danger" :disabled="row.is_superuser" @click="handleDelete(row)">
            {{ t('common.delete') }}
          </el-button>
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
      />
    </div>
  </el-card>

  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
      <el-form-item :label="t('system.user.username')" prop="username">
        <el-input v-model="form.username" :disabled="Boolean(form.id)" />
      </el-form-item>
      <el-form-item :label="t('system.user.password')" :prop="form.id ? '' : 'password'">
        <el-input
          v-model="form.password"
          type="password"
          show-password
          :placeholder="form.id ? t('system.user.passwordOptional') : ''"
        />
      </el-form-item>
      <el-form-item :label="t('system.user.nickname')">
        <el-input v-model="form.nickname" />
      </el-form-item>
      <el-form-item :label="t('system.user.email')">
        <el-input v-model="form.email" />
      </el-form-item>
      <el-form-item :label="t('system.user.phone')">
        <el-input v-model="form.phone" />
      </el-form-item>
      <el-form-item :label="t('system.user.department')">
        <el-select
          v-model="form.department"
          clearable
          filterable
          :placeholder="t('system.user.selectDepartment')"
          style="width: 100%"
        >
          <el-option
            v-for="item in departmentOptions"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('system.user.roles')">
        <el-select v-model="form.role_ids" multiple :placeholder="t('system.user.selectRoles')" style="width: 100%">
          <el-option v-for="item in roleOptions" :key="item.id" :label="roleOptionLabel(item)" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('common.status')">
        <el-switch v-model="form.is_active" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" @click="handleSubmit">{{ t('common.confirm') }}</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="resetDialogVisible" :title="t('system.user.resetPasswordTitle')" width="480px">
    <el-form ref="resetFormRef" :model="resetForm" :rules="resetRules" label-width="100px">
      <el-form-item :label="t('system.user.username')">
        <el-input v-model="resetForm.username" disabled />
      </el-form-item>
      <el-form-item :label="t('password.newPassword')" prop="new_password">
        <el-input
          v-model="resetForm.new_password"
          type="password"
          show-password
          :placeholder="t('password.newRequired')"
        />
      </el-form-item>
      <el-form-item :label="t('password.confirmPassword')" prop="confirm_password">
        <el-input
          v-model="resetForm.confirm_password"
          type="password"
          show-password
          :placeholder="t('password.confirmRequired')"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="resetDialogVisible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" :loading="resetLoading" @click="handleResetSubmit">{{ t('common.confirm') }}</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="activationDialogVisible" :title="t('system.user.activationLinkTitle')" width="640px">
    <el-descriptions v-if="activationResult" :column="1" border>
      <el-descriptions-item :label="t('system.user.recipientEmail')">
        {{ activationResult.email }}
      </el-descriptions-item>
      <el-descriptions-item label="UID">
        {{ activationResult.uid }}
      </el-descriptions-item>
      <el-descriptions-item label="Token">
        <span class="token-text">{{ activationResult.token }}</span>
      </el-descriptions-item>
      <el-descriptions-item :label="t('system.user.validHours')">
        {{ activationResult.expires_in_hours }} {{ t('system.user.hoursUnit') }}
      </el-descriptions-item>
      <el-descriptions-item :label="t('system.user.activationLink')">
        <el-input :model-value="activationLinkUrl" readonly>
          <template #append>
            <el-button @click="copyActivationLink">{{ t('system.user.copyLink') }}</el-button>
          </template>
        </el-input>
      </el-descriptions-item>
    </el-descriptions>
    <template #footer>
      <el-button type="primary" @click="activationDialogVisible = false">{{ t('common.close') }}</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.token-text {
  word-break: break-all;
}
</style>
