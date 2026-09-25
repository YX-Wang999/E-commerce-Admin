<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createSetting, deleteSetting, getSettingList, updateSetting } from '@/api/system'
import RoleNamesTab from '@/views/system/setting/RoleNamesTab.vue'
import { ACTION_COLUMN } from '@/config/table'

const { t } = useI18n()

const activeTab = ref('general')
const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const tableData = ref([])
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const form = reactive({
  id: null,
  key: '',
  value: '',
  value_type: 'string',
  description: '',
})

const dialogTitle = computed(() => (form.id ? t('system.setting.edit') : t('system.setting.create')))

const rules = computed(() => ({
  key: [{ required: true, message: t('system.setting.keyRequired'), trigger: 'blur' }],
}))

const valueTypeOptions = computed(() => [
  { label: t('system.setting.typeString'), value: 'string' },
  { label: t('system.setting.typeNumber'), value: 'number' },
  { label: t('system.setting.typeBoolean'), value: 'boolean' },
  { label: t('system.setting.typeFile'), value: 'file' },
])

async function fetchList() {
  loading.value = true
  try {
    const res = await getSettingList({
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    tableData.value = (res.data.results || []).filter((row) => row.key !== 'role_display_names')
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.id = null
  form.key = ''
  form.value = ''
  form.value_type = 'string'
  form.description = ''
}

function handleCreate() {
  resetForm()
  dialogVisible.value = true
}

function handleEdit(row) {
  form.id = row.id
  form.key = row.key
  form.value = row.value
  form.value_type = row.value_type
  form.description = row.description
  dialogVisible.value = true
}

async function handleDelete(row) {
  await ElMessageBox.confirm(t('system.setting.deleteConfirm', { key: row.key }), t('common.tip'), {
    type: 'warning',
  })
  await deleteSetting(row.id)
  ElMessage.success(t('common.deleteSuccess'))
  fetchList()
}

async function handleSubmit() {
  await formRef.value.validate()
  const payload = {
    key: form.key,
    value: form.value,
    value_type: form.value_type,
    description: form.description,
  }
  if (form.id) {
    await updateSetting(form.id, payload)
    ElMessage.success(t('common.updateSuccess'))
  } else {
    await createSetting(payload)
    ElMessage.success(t('common.createSuccess'))
  }
  dialogVisible.value = false
  fetchList()
}

onMounted(fetchList)
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <span>{{ t('system.setting.title') }}</span>
    </template>

    <el-tabs v-model="activeTab">
      <el-tab-pane :label="t('system.setting.generalTab')" name="general">
        <div class="tab-toolbar">
          <el-button type="primary" @click="handleCreate">{{ t('system.setting.create') }}</el-button>
        </div>

        <el-table v-loading="loading" :data="tableData" border>
          <el-table-column prop="key" :label="t('system.setting.configKey')" />
          <el-table-column prop="value" :label="t('system.setting.configValue')" show-overflow-tooltip />
          <el-table-column prop="value_type" :label="t('system.setting.configType')" width="100" />
          <el-table-column prop="description" :label="t('system.setting.description')" />
          <el-table-column prop="updated_at" :label="t('system.setting.updatedAt')" width="180" />
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
      </el-tab-pane>

      <el-tab-pane :label="t('system.roleNames.tab')" name="roleNames" lazy>
        <RoleNamesTab />
      </el-tab-pane>
    </el-tabs>
  </el-card>

  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
      <el-form-item :label="t('system.setting.configKey')" prop="key">
        <el-input v-model="form.key" :disabled="Boolean(form.id)" />
      </el-form-item>
      <el-form-item :label="t('system.setting.configValue')">
        <el-input v-model="form.value" type="textarea" />
      </el-form-item>
      <el-form-item :label="t('system.setting.configType')">
        <el-select v-model="form.value_type" style="width: 100%">
          <el-option
            v-for="item in valueTypeOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('system.setting.description')">
        <el-input v-model="form.description" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" @click="handleSubmit">{{ t('common.confirm') }}</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.tab-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
