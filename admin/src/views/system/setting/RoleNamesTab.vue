<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { useRoleDisplayStore } from '@/stores/roleDisplay'

const { t } = useI18n()
const roleDisplayStore = useRoleDisplayStore()

const loading = ref(false)
const saving = ref(false)
const items = ref([])
const editLocale = ref('zh-CN')

const localeTabs = computed(() => [
  { value: 'zh-CN', label: t('locale.zhCN') },
  { value: 'en-US', label: t('locale.enUS') },
  { value: 'ja-JP', label: t('locale.jaJP') },
])

const form = reactive({})

function resetFormFromItems(rows) {
  Object.keys(form).forEach((key) => delete form[key])
  rows.forEach((row) => {
    form[row.code] = {
      'zh-CN': row.custom_names?.['zh-CN'] || '',
      'en-US': row.custom_names?.['en-US'] || '',
      'ja-JP': row.custom_names?.['ja-JP'] || '',
    }
  })
}

async function loadData() {
  loading.value = true
  try {
    const data = await roleDisplayStore.fetchFull()
    items.value = data?.items || []
    resetFormFromItems(items.value)
  } finally {
    loading.value = false
  }
}

function previewName(row) {
  const custom = form[row.code]?.[editLocale.value]?.trim()
  if (custom) return custom
  return row.default_names?.[editLocale.value] || row.default_name
}

async function handleSave() {
  saving.value = true
  try {
    await roleDisplayStore.saveCustom({ ...form })
    ElMessage.success(t('system.roleNames.saveSuccess'))
    await loadData()
  } finally {
    saving.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div v-loading="loading" class="role-names-panel">
    <p class="hint">{{ t('system.roleNames.hint') }}</p>

    <div class="locale-toolbar">
      <span class="toolbar-label">{{ t('system.roleNames.editLocale') }}</span>
      <el-radio-group v-model="editLocale" size="small">
        <el-radio-button v-for="item in localeTabs" :key="item.value" :value="item.value">
          {{ item.label }}
        </el-radio-button>
      </el-radio-group>
    </div>

    <el-table :data="items" border stripe>
      <el-table-column prop="code" :label="t('system.role.code')" width="160" />
      <el-table-column :label="t('system.roleNames.defaultName')" min-width="140">
        <template #default="{ row }">
          {{ row.default_names?.[editLocale] || row.default_name }}
        </template>
      </el-table-column>
      <el-table-column :label="t('system.roleNames.customName')" min-width="220">
        <template #default="{ row }">
          <el-input
            v-model="form[row.code][editLocale]"
            :placeholder="t('system.roleNames.customPlaceholder')"
            clearable
          />
        </template>
      </el-table-column>
      <el-table-column :label="t('system.roleNames.preview')" min-width="140">
        <template #default="{ row }">
          <el-tag type="info">{{ previewName(row) }}</el-tag>
        </template>
      </el-table-column>
    </el-table>

    <div class="actions">
      <el-button type="primary" :loading="saving" @click="handleSave">
        {{ t('common.save') }}
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.role-names-panel {
  padding-top: 4px;
}
.hint {
  margin: 0 0 16px;
  color: #909399;
  font-size: 13px;
  line-height: 1.6;
}
.locale-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.toolbar-label {
  font-size: 14px;
  color: #606266;
}
.actions {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
