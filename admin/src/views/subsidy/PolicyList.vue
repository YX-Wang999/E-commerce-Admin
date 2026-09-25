<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  createSubsidyPolicy,
  deleteSubsidyPolicy,
  getSubsidyPolicies,
  updateSubsidyPolicy,
} from '@/api/subsidy'

const { t } = useI18n()
const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const formRef = ref(null)
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const form = reactive({
  id: null,
  name: '',
  description: '',
  subsidy_type: 'percent',
  subsidy_value: 20,
  max_subsidy: 2000,
  is_active: true,
  start_time: '',
  end_time: '',
})

const dialogTitle = computed(() => (form.id ? t('subsidy.editPolicy') : t('subsidy.createPolicy')))

const rules = computed(() => ({
  name: [{ required: true, message: t('subsidy.nameRequired'), trigger: 'blur' }],
  subsidy_value: [{ required: true, message: t('subsidy.valueRequired'), trigger: 'blur' }],
}))

function resetForm() {
  Object.assign(form, {
    id: null,
    name: '',
    description: '',
    subsidy_type: 'percent',
    subsidy_value: 20,
    max_subsidy: 2000,
    is_active: true,
    start_time: '',
    end_time: '',
  })
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getSubsidyPolicies({ page: pagination.page, page_size: pagination.pageSize })
    tableData.value = res.data.results || []
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

function openEdit(row) {
  Object.assign(form, {
    id: row.id,
    name: row.name,
    description: row.description,
    subsidy_type: row.subsidy_type,
    subsidy_value: Number(row.subsidy_value),
    max_subsidy: row.max_subsidy != null ? Number(row.max_subsidy) : null,
    is_active: row.is_active,
    start_time: row.start_time || '',
    end_time: row.end_time || '',
  })
  dialogVisible.value = true
}

async function submitForm() {
  await formRef.value?.validate()
  const payload = {
    name: form.name,
    description: form.description,
    subsidy_type: form.subsidy_type,
    subsidy_value: form.subsidy_value,
    max_subsidy: form.subsidy_type === 'percent' ? form.max_subsidy : null,
    is_active: form.is_active,
    start_time: form.start_time || null,
    end_time: form.end_time || null,
  }
  if (form.id) {
    await updateSubsidyPolicy(form.id, payload)
    ElMessage.success(t('common.updateSuccess'))
  } else {
    await createSubsidyPolicy(payload)
    ElMessage.success(t('common.createSuccess'))
  }
  dialogVisible.value = false
  fetchList()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(t('subsidy.deletePolicyConfirm'), t('common.tip'), { type: 'warning' })
  await deleteSubsidyPolicy(row.id)
  ElMessage.success(t('common.deleteSuccess'))
  fetchList()
}

onMounted(fetchList)
</script>

<template>
  <div class="page-card">
    <div class="page-header">
      <h2>{{ t('subsidy.policyTitle') }}</h2>
      <el-button type="primary" :icon="Plus" @click="openCreate">{{ t('subsidy.createPolicy') }}</el-button>
    </div>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="name" :label="t('subsidy.policyName')" min-width="160" />
      <el-table-column prop="subsidy_type" :label="t('subsidy.subsidyType')" width="100">
        <template #default="{ row }">
          {{ row.subsidy_type === 'percent' ? t('subsidy.typePercent') : t('subsidy.typeFixed') }}
        </template>
      </el-table-column>
      <el-table-column prop="subsidy_value" :label="t('subsidy.subsidyValue')" width="120" />
      <el-table-column prop="max_subsidy" :label="t('subsidy.maxSubsidy')" width="120" />
      <el-table-column prop="is_active" :label="t('common.status')" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">
            {{ row.is_active ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('common.action')" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">{{ t('common.edit') }}</el-button>
          <el-button link type="danger" @click="handleDelete(row)">{{ t('common.delete') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        layout="total, prev, pager, next"
        :total="pagination.total"
        @current-change="fetchList"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="560px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <el-form-item :label="t('subsidy.policyName')" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item :label="t('subsidy.description')">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item :label="t('subsidy.subsidyType')">
          <el-radio-group v-model="form.subsidy_type">
            <el-radio value="percent">{{ t('subsidy.typePercent') }}</el-radio>
            <el-radio value="fixed">{{ t('subsidy.typeFixed') }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="t('subsidy.subsidyValue')" prop="subsidy_value">
          <el-input-number v-model="form.subsidy_value" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item v-if="form.subsidy_type === 'percent'" :label="t('subsidy.maxSubsidy')">
          <el-input-number v-model="form.max_subsidy" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item :label="t('common.status')">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        <el-form-item :label="t('subsidy.startTime')">
          <el-date-picker v-model="form.start_time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" />
        </el-form-item>
        <el-form-item :label="t('subsidy.endTime')">
          <el-date-picker v-model="form.end_time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitForm">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.page-header h2 {
  margin: 0;
  font-size: 18px;
}
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
