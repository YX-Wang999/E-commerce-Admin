<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { createPointsRule, getPointsRules, updatePointsRule } from '@/api/points'

const { t } = useI18n()

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const activeTab = ref('earn')
const earnRules = ref([])
const redeemRules = ref([])

const form = reactive({
  code: '',
  name: '',
  rule_type: 'earn',
  current_value: 0,
  min_value: null,
  max_value: null,
  description: '',
  is_active: true,
})

const tableData = computed(() => (activeTab.value === 'earn' ? earnRules.value : redeemRules.value))

const formRules = computed(() => ({
  code: [{ required: true, message: t('points.ruleCodeRequired'), trigger: 'blur' }],
  name: [{ required: true, message: t('points.ruleNameRequired'), trigger: 'blur' }],
  current_value: [{ required: true, message: t('points.currentValueRequired'), trigger: 'change' }],
}))

function ruleBounds(row) {
  const min = row.min_value != null ? Number(row.min_value) : undefined
  const max = row.max_value != null ? Number(row.max_value) : undefined
  return { min, max }
}

function formatValue(row) {
  const value = Number(row.current_value ?? row.points_value ?? 0)
  if (row.code === 'redeem_max_rate') {
    return `${value}%`
  }
  if (row.code === 'order_rate') {
    return t('points.orderRateDisplay', { value })
  }
  if (row.code === 'redeem_rate') {
    return t('points.redeemRateDisplay', { value })
  }
  return String(value)
}

async function fetchList() {
  loading.value = true
  try {
    const [earnRes, redeemRes] = await Promise.all([
      getPointsRules({ page_size: 100, rule_type: 'earn' }),
      getPointsRules({ page_size: 100, rule_type: 'redeem' }),
    ])
    earnRules.value = earnRes.data.results || earnRes.data || []
    redeemRules.value = redeemRes.data.results || redeemRes.data || []
  } finally {
    loading.value = false
  }
}

function openCreate() {
  form.code = ''
  form.name = ''
  form.rule_type = activeTab.value
  form.current_value = 0
  form.min_value = null
  form.max_value = null
  form.description = ''
  form.is_active = true
  dialogVisible.value = true
}

async function handleCreate() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    await createPointsRule({
      code: form.code.trim(),
      name: form.name.trim(),
      rule_type: form.rule_type,
      default_value: form.current_value,
      current_value: form.current_value,
      min_value: form.min_value,
      max_value: form.max_value,
      description: form.description.trim(),
      is_active: form.is_active,
    })
    ElMessage.success(t('points.ruleCreated'))
    dialogVisible.value = false
    await fetchList()
  } finally {
    submitting.value = false
  }
}

async function toggleActive(row) {
  await updatePointsRule(row.id, { is_active: row.is_active })
  ElMessage.success(t('common.updateSuccess'))
}

async function saveValue(row) {
  const { min, max } = ruleBounds(row)
  const payload = { current_value: row.current_value }
  await updatePointsRule(row.id, payload)
  row.points_value = Number(row.current_value)
  ElMessage.success(t('common.updateSuccess'))
}

function onValueChange(row) {
  const { min, max } = ruleBounds(row)
  const value = Number(row.current_value)
  if (min != null && value < min) {
    row.current_value = min
  }
  if (max != null && value > max) {
    row.current_value = max
  }
  saveValue(row)
}

onMounted(fetchList)
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>{{ t('points.rulesTitle') }}</span>
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>
          {{ t('points.createRule') }}
        </el-button>
      </div>
    </template>
    <p class="page-tip">{{ t('points.platformScopeTip') }}</p>

    <el-tabs v-model="activeTab">
      <el-tab-pane :label="t('points.ruleTypeEarn')" name="earn" />
      <el-tab-pane :label="t('points.ruleTypeRedeem')" name="redeem" />
    </el-tabs>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="code" :label="t('points.ruleCode')" width="140" show-overflow-tooltip />
      <el-table-column prop="name" :label="t('points.ruleName')" min-width="120" show-overflow-tooltip />
      <el-table-column prop="description" :label="t('points.ruleDesc')" min-width="180" show-overflow-tooltip />
      <el-table-column :label="t('points.currentValue')" width="160">
        <template #default="{ row }">
          <el-input-number
            v-model="row.current_value"
            :min="ruleBounds(row).min ?? 0"
            :max="ruleBounds(row).max ?? undefined"
            :step="row.code === 'order_rate' ? 0.1 : 1"
            :precision="row.code === 'order_rate' ? 1 : 0"
            size="small"
            @change="onValueChange(row)"
          />
        </template>
      </el-table-column>
      <el-table-column :label="t('points.valueRange')" width="120">
        <template #default="{ row }">
          <span v-if="row.min_value != null || row.max_value != null">
            {{ row.min_value ?? '—' }} ~ {{ row.max_value ?? '—' }}
          </span>
          <span v-else>—</span>
        </template>
      </el-table-column>
      <el-table-column :label="t('points.displayValue')" width="140">
        <template #default="{ row }">
          {{ formatValue(row) }}
        </template>
      </el-table-column>
      <el-table-column :label="t('common.status')" width="100">
        <template #default="{ row }">
          <el-switch v-model="row.is_active" @change="toggleActive(row)" />
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="t('points.createRule')" width="520px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item :label="t('points.ruleType')">
          <el-radio-group v-model="form.rule_type">
            <el-radio value="earn">{{ t('points.ruleTypeEarn') }}</el-radio>
            <el-radio value="redeem">{{ t('points.ruleTypeRedeem') }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="t('points.ruleCode')" prop="code">
          <el-input v-model="form.code" :placeholder="t('points.ruleCodePlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('points.ruleName')" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item :label="t('points.currentValue')" prop="current_value">
          <el-input-number v-model="form.current_value" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('points.minValue')">
          <el-input-number v-model="form.min_value" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('points.maxValue')">
          <el-input-number v-model="form.max_value" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('points.ruleDesc')">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item :label="t('common.status')">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCreate">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.page-tip {
  margin: 0 0 12px;
  color: #909399;
  font-size: 13px;
}
</style>
