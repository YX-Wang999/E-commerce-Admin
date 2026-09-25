<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createDepartment,
  deleteDepartment,
  getDepartmentTree,
  updateDepartment,
} from '@/api/department'
import { getUserList } from '@/api/user'
import { ACTION_COLUMN } from '@/config/table'

const { t } = useI18n()

const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const tableData = ref([])
const parentOptions = ref([])
const userOptions = ref([])

const form = reactive({
  id: null,
  name: '',
  code: '',
  parent: null,
  manager: null,
  is_active: true,
})

const dialogTitle = computed(() => (form.id ? t('system.department.edit') : t('system.department.create')))

const rules = computed(() => ({
  name: [{ required: true, message: t('system.department.nameRequired'), trigger: 'blur' }],
  code: [{ required: true, message: t('system.department.codeRequired'), trigger: 'blur' }],
}))

function flattenDepartments(departments, result = []) {
  departments.forEach((item) => {
    result.push(item)
    if (item.children?.length) {
      flattenDepartments(item.children, result)
    }
  })
  return result
}

async function fetchUsers() {
  const res = await getUserList({ page_size: 200 })
  userOptions.value = res.data.results || res.data || []
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getDepartmentTree()
    tableData.value = res.data || []
    parentOptions.value = flattenDepartments(res.data || [])
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.id = null
  form.name = ''
  form.code = ''
  form.parent = null
  form.manager = null
  form.is_active = true
}

function handleCreate() {
  resetForm()
  dialogVisible.value = true
}

function handleEdit(row) {
  form.id = row.id
  form.name = row.name
  form.code = row.code
  form.parent = row.parent || null
  form.manager = row.manager || null
  form.is_active = row.is_active
  dialogVisible.value = true
}

async function handleDelete(row) {
  await ElMessageBox.confirm(
    t('system.department.deleteConfirm', { name: row.name }),
    t('common.tip'),
    { type: 'warning' },
  )
  await deleteDepartment(row.id)
  ElMessage.success(t('common.deleteSuccess'))
  fetchList()
}

async function handleSubmit() {
  await formRef.value.validate()
  const payload = {
    name: form.name,
    code: form.code,
    parent: form.parent,
    manager: form.manager,
    is_active: form.is_active,
  }
  if (form.id) {
    await updateDepartment(form.id, payload)
    ElMessage.success(t('common.updateSuccess'))
  } else {
    await createDepartment(payload)
    ElMessage.success(t('common.createSuccess'))
  }
  dialogVisible.value = false
  fetchList()
}

onMounted(async () => {
  await fetchUsers()
  await fetchList()
})
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>{{ t('system.department.title') }}</span>
        <el-button type="primary" @click="handleCreate">{{ t('system.department.create') }}</el-button>
      </div>
    </template>

    <el-table
      v-loading="loading"
      :data="tableData"
      row-key="id"
      border
      default-expand-all
      :tree-props="{ children: 'children' }"
    >
      <el-table-column prop="name" :label="t('system.department.name')" min-width="160" />
      <el-table-column prop="code" :label="t('system.department.code')" width="120" />
      <el-table-column :label="t('system.department.manager')" min-width="120">
        <template #default="{ row }">
          {{ row.manager_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column :label="t('system.department.memberCount')" width="100">
        <template #default="{ row }">
          {{ row.member_count ?? 0 }}
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
  </el-card>

  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="560px">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item :label="t('system.department.name')" prop="name">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item :label="t('system.department.code')" prop="code">
        <el-input v-model="form.code" :disabled="Boolean(form.id)" />
      </el-form-item>
      <el-form-item :label="t('system.department.parent')">
        <el-select
          v-model="form.parent"
          clearable
          :placeholder="t('system.department.topLevel')"
          style="width: 100%"
        >
          <el-option
            v-for="item in parentOptions.filter((d) => d.id !== form.id)"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('system.department.manager')">
        <el-select
          v-model="form.manager"
          clearable
          filterable
          :placeholder="t('system.department.selectManager')"
          style="width: 100%"
        >
          <el-option
            v-for="item in userOptions"
            :key="item.id"
            :label="item.nickname || item.username"
            :value="item.id"
          />
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
</style>
