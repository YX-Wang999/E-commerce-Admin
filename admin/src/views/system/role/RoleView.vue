<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createRole,
  deleteRole,
  getMenuFlatList,
  getPermissionList,
  getRoleList,
  updateRole,
} from '@/api/role'
import { ACTION_COLUMN } from '@/config/table'
import { useRoleLabel } from '@/composables/useRoleLabel'

const { t } = useI18n()
const { roleLabel } = useRoleLabel()

const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const tableData = ref([])
const permissionOptions = ref([])
const menuOptions = ref([])
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const form = reactive({
  id: null,
  name: '',
  code: '',
  description: '',
  is_active: true,
  permission_ids: [],
  menu_ids: [],
})

const dialogTitle = computed(() => (form.id ? t('system.role.edit') : t('system.role.create')))

const rules = computed(() => ({
  name: [{ required: true, message: t('system.role.nameRequired'), trigger: 'blur' }],
  code: [{ required: true, message: t('system.role.codeRequired'), trigger: 'blur' }],
}))

async function fetchOptions() {
  const [permRes, menuRes] = await Promise.all([
    getPermissionList({ page_size: 200 }),
    getMenuFlatList(),
  ])
  permissionOptions.value = permRes.data.results || permRes.data || []
  menuOptions.value = menuRes.data || []
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getRoleList({
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    tableData.value = res.data.results || []
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.id = null
  form.name = ''
  form.code = ''
  form.description = ''
  form.is_active = true
  form.permission_ids = []
  form.menu_ids = []
}

function handleCreate() {
  resetForm()
  dialogVisible.value = true
}

function handleEdit(row) {
  form.id = row.id
  form.name = row.name
  form.code = row.code
  form.description = row.description
  form.is_active = row.is_active
  form.permission_ids = row.permissions?.map((item) => item.id) || []
  form.menu_ids = row.menus?.map((item) => item.id) || []
  dialogVisible.value = true
}

async function handleDelete(row) {
  await ElMessageBox.confirm(t('system.role.deleteConfirm', { name: row.name }), t('common.tip'), {
    type: 'warning',
  })
  await deleteRole(row.id)
  ElMessage.success(t('common.deleteSuccess'))
  fetchList()
}

async function handleSubmit() {
  await formRef.value.validate()
  const payload = {
    name: form.name,
    code: form.code,
    description: form.description,
    is_active: form.is_active,
    permission_ids: form.permission_ids,
    menu_ids: form.menu_ids,
  }
  if (form.id) {
    await updateRole(form.id, payload)
    ElMessage.success(t('common.updateSuccess'))
  } else {
    await createRole(payload)
    ElMessage.success(t('common.createSuccess'))
  }
  dialogVisible.value = false
  fetchList()
}

onMounted(async () => {
  await fetchOptions()
  await fetchList()
})
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>{{ t('system.role.title') }}</span>
        <el-button type="primary" @click="handleCreate">{{ t('system.role.create') }}</el-button>
      </div>
    </template>

    <el-table v-loading="loading" :data="tableData" border>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="code" :label="t('system.role.code')" />
      <el-table-column :label="t('system.role.name')">
        <template #default="{ row }">
          {{ roleLabel(row.code, row.name) }}
        </template>
      </el-table-column>
      <el-table-column prop="name" :label="t('system.roleNames.defaultName')" width="140" class-name="col-hide-md" />
      <el-table-column prop="description" :label="t('system.role.description')" />
      <el-table-column :label="t('common.status')" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">
            {{ row.is_active ? t('common.enabled') : t('common.disabled') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="t('common.actions')"
        :min-width="ACTION_COLUMN.system"
        class-name="col-actions"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button link type="primary" @click="handleEdit(row)">{{ t('common.edit') }}</el-button>
          <el-button link type="danger" @click="handleDelete(row)">{{ t('common.delete') }}</el-button>
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

  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="640px">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
      <el-form-item :label="t('system.role.name')" prop="name">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item :label="t('system.role.code')" prop="code">
        <el-input v-model="form.code" :disabled="Boolean(form.id)" />
      </el-form-item>
      <el-form-item :label="t('system.role.description')">
        <el-input v-model="form.description" type="textarea" />
      </el-form-item>
      <el-form-item :label="t('system.role.permissions')">
        <el-select
          v-model="form.permission_ids"
          multiple
          :placeholder="t('system.role.selectPermissions')"
          style="width: 100%"
        >
          <el-option
            v-for="item in permissionOptions"
            :key="item.id"
            :label="`${item.module} - ${item.name}`"
            :value="item.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('system.role.menus')">
        <el-select
          v-model="form.menu_ids"
          multiple
          :placeholder="t('system.role.selectMenus')"
          style="width: 100%"
        >
          <el-option v-for="item in menuOptions" :key="item.id" :label="item.title" :value="item.id" />
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
</style>
