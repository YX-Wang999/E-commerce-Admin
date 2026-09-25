<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getTags, updateTag } from '@/api/tags'

const { t } = useI18n()
const loading = ref(false)
const tableData = ref([])

async function fetchList() {
  loading.value = true
  try {
    const res = await getTags({ page_size: 100 })
    tableData.value = res.data.results || res.data || []
  } finally {
    loading.value = false
  }
}

async function toggleActive(row) {
  await updateTag(row.id, { is_active: row.is_active })
  ElMessage.success(t('common.updateSuccess'))
}

onMounted(fetchList)
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <span>{{ t('tags.manageTitle') }}</span>
    </template>
    <p class="page-tip">{{ t('tags.manageTip') }}</p>
    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="name" :label="t('tags.name')" width="120" />
      <el-table-column prop="code" :label="t('tags.code')" width="140" />
      <el-table-column prop="category_name" :label="t('tags.category')" width="120" />
      <el-table-column :label="t('tags.color')" width="100">
        <template #default="{ row }">
          <span class="color-chip" :style="{ background: row.color, color: row.text_color }">{{ row.name }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="priority" :label="t('tags.priority')" width="90" />
      <el-table-column :label="t('common.status')" width="100">
        <template #default="{ row }">
          <el-switch v-model="row.is_active" @change="toggleActive(row)" />
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<style scoped>
.page-tip {
  margin: 0 0 12px;
  color: #909399;
  font-size: 13px;
}
.color-chip {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
</style>
