<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getCategoryList } from '@/api/products'

const { t } = useI18n()
const loading = ref(false)
const tableData = ref([])

async function fetchList() {
  loading.value = true
  try {
    const res = await getCategoryList()
    tableData.value = res.data || []
  } finally {
    loading.value = false
  }
}

onMounted(fetchList)
</script>

<template>
  <div class="page-card">
    <div class="page-head">
      <h2>{{ t('seller.menuCategories') }}</h2>
      <el-button @click="fetchList">{{ t('seller.refresh') }}</el-button>
    </div>
    <el-table v-loading="loading" :data="tableData" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" :label="t('seller.category')" min-width="160" />
      <el-table-column prop="parent_name" :label="t('seller.parentCategory')" min-width="140" />
      <el-table-column prop="sort_order" :label="t('seller.sortOrder')" width="100" />
    </el-table>
    <p class="page-tip">{{ t('seller.categoryReadonlyTip') }}</p>
  </div>
</template>

<style scoped>
.page-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.page-head h2 {
  margin: 0;
  font-size: 18px;
}
.page-tip {
  margin: 16px 0 0;
  color: #909399;
  font-size: 13px;
}
</style>
