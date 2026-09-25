<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  createMemberLevel,
  deleteMemberLevel,
  getMemberLevels,
  updateMemberLevel,
} from '@/api/membership'

const { t } = useI18n()
const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const formRef = ref(null)
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const form = reactive({
  id: null,
  level: 1,
  name: '',
  min_points: 0,
  discount_rate: 100,
  points_multiplier: 1,
  description: '',
  sort_order: 0,
  is_active: true,
})

const dialogTitle = computed(() => (form.id ? t('membership.editLevel') : t('membership.createLevel')))

const rules = computed(() => ({
  level: [{ required: true, message: t('membership.levelRequired'), trigger: 'blur' }],
  name: [{ required: true, message: t('membership.nameRequired'), trigger: 'blur' }],
  min_points: [{ required: true, message: t('membership.minPointsRequired'), trigger: 'blur' }],
  discount_rate: [{ required: true, message: t('membership.discountRequired'), trigger: 'blur' }],
  points_multiplier: [{ required: true, message: t('membership.multiplierRequired'), trigger: 'blur' }],
}))

function resetForm() {
  Object.assign(form, {
    id: null,
    level: 1,
    name: '',
    min_points: 0,
    discount_rate: 100,
    points_multiplier: 1,
    description: '',
    sort_order: 0,
    is_active: true,
  })
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getMemberLevels({ page: pagination.page, page_size: pagination.pageSize })
    tableData.value = res.data.results || res.data || []
    pagination.total = res.data.count || tableData.value.length
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
    level: row.level,
    name: row.name,
    min_points: row.min_points,
    discount_rate: row.discount_rate,
    points_multiplier: Number(row.points_multiplier),
    description: row.description || '',
    sort_order: row.sort_order || 0,
    is_active: row.is_active,
  })
  dialogVisible.value = true
}

async function submitForm() {
  await formRef.value?.validate()
  const payload = {
    level: form.level,
    name: form.name,
    min_points: form.min_points,
    discount_rate: form.discount_rate,
    points_multiplier: form.points_multiplier,
    description: form.description,
    sort_order: form.sort_order,
    is_active: form.is_active,
  }
  if (form.id) {
    await updateMemberLevel(form.id, payload)
    ElMessage.success(t('common.updateSuccess'))
  } else {
    await createMemberLevel(payload)
    ElMessage.success(t('common.createSuccess'))
  }
  dialogVisible.value = false
  fetchList()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(t('membership.deleteConfirm'), t('common.tip'), { type: 'warning' })
  await deleteMemberLevel(row.id)
  ElMessage.success(t('common.deleteSuccess'))
  fetchList()
}

onMounted(fetchList)
</script>

<template>
  <div class="page-card">
    <div class="page-header">
      <div>
        <h2>{{ t('membership.listTitle') }}</h2>
        <p class="subtitle">{{ t('membership.listSubtitle') }}</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreate">{{ t('membership.createLevel') }}</el-button>
    </div>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="level" :label="t('membership.levelValue')" width="90" align="center" />
      <el-table-column prop="name" :label="t('membership.levelName')" min-width="120" />
      <el-table-column prop="min_points" :label="t('membership.minPoints')" width="120" align="right" />
      <el-table-column prop="discount_rate" :label="t('membership.discountRate')" width="110" align="center">
        <template #default="{ row }">{{ row.discount_rate }}%</template>
      </el-table-column>
      <el-table-column prop="points_multiplier" :label="t('membership.pointsMultiplier')" width="120" align="center">
        <template #default="{ row }">{{ row.points_multiplier }}x</template>
      </el-table-column>
      <el-table-column prop="description" :label="t('membership.description')" min-width="160" show-overflow-tooltip />
      <el-table-column prop="is_active" :label="t('common.status')" width="90">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">
            {{ row.is_active ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('common.action')" width="160" fixed="right">
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
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="fetchList"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item :label="t('membership.levelValue')" prop="level">
          <el-input-number v-model="form.level" :min="1" :max="99" />
        </el-form-item>
        <el-form-item :label="t('membership.levelName')" prop="name">
          <el-input v-model="form.name" maxlength="32" />
        </el-form-item>
        <el-form-item :label="t('membership.minPoints')" prop="min_points">
          <el-input-number v-model="form.min_points" :min="0" :step="100" />
        </el-form-item>
        <el-form-item :label="t('membership.discountRate')" prop="discount_rate">
          <el-input-number v-model="form.discount_rate" :min="1" :max="100" />
        </el-form-item>
        <el-form-item :label="t('membership.pointsMultiplier')" prop="points_multiplier">
          <el-input-number v-model="form.points_multiplier" :min="1" :max="10" :step="0.1" :precision="2" />
        </el-form-item>
        <el-form-item :label="t('membership.sortOrder')">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
        <el-form-item :label="t('membership.description')">
          <el-input v-model="form.description" type="textarea" :rows="2" maxlength="255" />
        </el-form-item>
        <el-form-item :label="t('common.status')">
          <el-switch v-model="form.is_active" />
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
  padding: 4px;
}
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}
.page-header h2 {
  margin: 0;
  font-size: 18px;
}
.subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  color: #909399;
}
.pager {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
