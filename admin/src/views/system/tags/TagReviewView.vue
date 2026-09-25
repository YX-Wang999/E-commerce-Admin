<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTenantTagConfigs, reviewTenantTagConfig } from '@/api/tags'

const { t } = useI18n()
const loading = ref(false)
const tableData = ref([])

async function fetchList() {
  loading.value = true
  try {
    const res = await getTenantTagConfigs({ page_size: 100 })
    tableData.value = res.data.results || res.data || []
  } finally {
    loading.value = false
  }
}

async function approve(row) {
  await reviewTenantTagConfig(row.id, { status: 'approved' })
  ElMessage.success(t('tags.reviewApproved'))
  fetchList()
}

async function reject(row) {
  const { value } = await ElMessageBox.prompt(t('tags.rejectReason'), t('common.tip'))
  await reviewTenantTagConfig(row.id, { status: 'rejected', reject_reason: value || '' })
  ElMessage.success(t('tags.reviewRejected'))
  fetchList()
}

onMounted(fetchList)
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <span>{{ t('tags.reviewTitle') }}</span>
    </template>
    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="tenant_name" :label="t('tags.tenantName')" min-width="120" />
      <el-table-column prop="tag_name" :label="t('tags.name')" width="120" />
      <el-table-column prop="status" :label="t('tags.reviewStatus')" width="100" />
      <el-table-column prop="reject_reason" :label="t('tags.rejectReason')" min-width="160" show-overflow-tooltip />
      <el-table-column :label="t('common.actions')" width="180" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending'" link type="success" @click="approve(row)">{{ t('tags.approve') }}</el-button>
          <el-button v-if="row.status === 'pending'" link type="danger" @click="reject(row)">{{ t('tags.reject') }}</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>
