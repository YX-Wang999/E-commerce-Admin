<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useMenuTitle } from '@/i18n'
import { createMenu, deleteMenu, getMenuTree, getPermissionList, updateMenu } from '@/api/menu'
import { ACTION_COLUMN } from '@/config/table'

const { t } = useI18n()
const translateMenuTitle = useMenuTitle()

const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const tableData = ref([])
const permissionOptions = ref([])
const parentOptions = ref([])

const form = reactive({
  id: null,
  parent: null,
  title: '',
  name: '',
  path: '',
  component: '',
  icon: '',
  menu_type: 'menu',
  permission: null,
  sort_order: 0,
  is_visible: true,
  is_active: true,
})

const dialogTitle = computed(() => (form.id ? t('system.menu.edit') : t('system.menu.create')))

const rules = computed(() => ({
  title: [{ required: true, message: t('system.menu.titleRequired'), trigger: 'blur' }],
  name: [{ required: true, message: t('system.menu.nameRequired'), trigger: 'blur' }],
}))

const menuTypeOptions = computed(() => [
  { label: t('system.menu.typeDirectory'), value: 'directory' },
  { label: t('system.menu.typeMenu'), value: 'menu' },
  { label: t('system.menu.typeButton'), value: 'button' },
])

function flattenMenus(menus, result = []) {
  menus.forEach((item) => {
    result.push(item)
    if (item.children?.length) {
      flattenMenus(item.children, result)
    }
  })
  return result
}

async function fetchOptions() {
  const permRes = await getPermissionList({ page_size: 200 })
  permissionOptions.value = permRes.data.results || permRes.data || []
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getMenuTree()
    tableData.value = res.data || []
    parentOptions.value = flattenMenus(res.data || [])
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.id = null
  form.parent = null
  form.title = ''
  form.name = ''
  form.path = ''
  form.component = ''
  form.icon = ''
  form.menu_type = 'menu'
  form.permission = null
  form.sort_order = 0
  form.is_visible = true
  form.is_active = true
}

function handleCreate() {
  resetForm()
  dialogVisible.value = true
}

function handleEdit(row) {
  form.id = row.id
  form.parent = row.parent || null
  form.title = row.title
  form.name = row.name
  form.path = row.path
  form.component = row.component
  form.icon = row.icon
  form.menu_type = row.menu_type
  form.permission = row.permission || null
  form.sort_order = row.sort_order
  form.is_visible = row.is_visible
  form.is_active = row.is_active
  dialogVisible.value = true
}

async function handleDelete(row) {
  await ElMessageBox.confirm(t('system.menu.deleteConfirm', { name: row.title }), t('common.tip'), {
    type: 'warning',
  })
  await deleteMenu(row.id)
  ElMessage.success(t('common.deleteSuccess'))
  fetchList()
}

async function handleSubmit() {
  await formRef.value.validate()
  const payload = { ...form }
  delete payload.id
  if (form.id) {
    await updateMenu(form.id, payload)
    ElMessage.success(t('common.updateSuccess'))
  } else {
    await createMenu(payload)
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
        <span>{{ t('system.menu.title') }}</span>
        <el-button type="primary" @click="handleCreate">{{ t('system.menu.create') }}</el-button>
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
      <el-table-column prop="title" :label="t('system.menu.menuTitle')" />
      <el-table-column prop="name" :label="t('system.menu.routeName')" />
      <el-table-column prop="path" :label="t('system.menu.path')" />
      <el-table-column prop="icon" :label="t('system.menu.icon')" width="100" />
      <el-table-column prop="menu_type" :label="t('system.menu.type')" width="100" />
      <el-table-column prop="sort_order" :label="t('product.sortOrder')" width="80" />
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

  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="640px">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
      <el-form-item :label="t('system.menu.parentMenu')">
        <el-select
          v-model="form.parent"
          clearable
          :placeholder="t('system.menu.topMenu')"
          style="width: 100%"
        >
          <el-option
            v-for="item in parentOptions"
            :key="item.id"
            :label="translateMenuTitle(item.path, item.title)"
            :value="item.id"
            :disabled="item.id === form.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('system.menu.menuTitle')" prop="title">
        <el-input v-model="form.title" />
      </el-form-item>
      <el-form-item :label="t('system.menu.routeName')" prop="name">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item :label="t('system.menu.path')">
        <el-input v-model="form.path" />
      </el-form-item>
      <el-form-item :label="t('system.menu.component')">
        <el-input v-model="form.component" />
      </el-form-item>
      <el-form-item :label="t('system.menu.icon')">
        <el-input v-model="form.icon" :placeholder="t('system.menu.iconPlaceholder')" />
      </el-form-item>
      <el-form-item :label="t('system.menu.type')">
        <el-select v-model="form.menu_type" style="width: 100%">
          <el-option
            v-for="item in menuTypeOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('system.role.permissions')">
        <el-select v-model="form.permission" clearable :placeholder="t('common.optional')" style="width: 100%">
          <el-option
            v-for="item in permissionOptions"
            :key="item.id"
            :label="`${item.module} - ${item.name}`"
            :value="item.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('product.sortOrder')">
        <el-input-number v-model="form.sort_order" :min="0" />
      </el-form-item>
      <el-form-item :label="t('system.menu.visible')">
        <el-switch v-model="form.is_visible" />
      </el-form-item>
      <el-form-item :label="t('common.enabled')">
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
