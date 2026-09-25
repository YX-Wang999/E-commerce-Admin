<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getSellerTags, updateSellerTagConfig } from '@/api/tags'

const { t } = useI18n()
const loading = ref(false)
const tableData = ref([])

async function fetchList() {
  loading.value = true
  try {
    const res = await getSellerTags()
    tableData.value = res.data || []
  } finally {
    loading.value = false
  }
}

async function toggleParticipate(row) {
  const next = !row.participating
  const res = await updateSellerTagConfig({ tag_id: row.id, is_participating: next })
  ElMessage.success(res.message || t('common.updateSuccess'))
  fetchList()
}

onMounted(fetchList)
</script>

<template>
  <div class="page-card">
    <div class="page-header">
      <h2>{{ t('seller.promoTagsTitle') }}</h2>
      <p>{{ t('seller.promoTagsTip') }}</p>
    </div>
    <el-table v-loading="loading" :data="tableData" stripe>
      <el-table-column prop="name" :label="t('seller.tagName')" min-width="120" />
      <el-table-column prop="category_name" :label="t('seller.tagCategory')" width="120" />
      <el-table-column :label="t('seller.tagPreview')" width="120">
        <template #default="{ row }">
          <span class="tag-chip" :style="{ background: row.color, color: row.text_color }">{{ row.name }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="config_status" :label="t('seller.tagStatus')" width="100" />
      <el-table-column :label="t('seller.actions')" width="140">
        <template #default="{ row }">
          <el-button link type="primary" @click="toggleParticipate(row)">
            {{ row.participating ? t('seller.tagLeave') : t('seller.tagJoin') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.page-header h2 {
  margin: 0 0 6px;
  font-size: 18px;
}
.page-header p {
  margin: 0 0 16px;
  color: #909399;
  font-size: 13px;
}
.tag-chip {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
</style>
