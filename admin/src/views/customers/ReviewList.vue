<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { deleteAdminReview, getAdminReviews } from '@/api/review'
import { resolveImageUrl } from '@/utils/media'
import TableActionMenu from '@/components/TableActionMenu.vue'
import { ACTION_COLUMN } from '@/config/table'

const { t } = useI18n()
const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ keyword: '' })

async function fetchList() {
  loading.value = true
  try {
    const res = await getAdminReviews({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
    })
    tableData.value = res.data.results || []
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(t('review.deleteConfirm'), t('common.tip'), { type: 'warning' })
  await deleteAdminReview(row.id)
  ElMessage.success(t('review.deleteSuccess'))
  fetchList()
}

function formatDate(value) {
  return value ? String(value).replace('T', ' ').slice(0, 16) : '-'
}

onMounted(fetchList)
</script>

<template>
  <div class="page-card">
    <div class="page-header">
      <h2>{{ t('review.manageTitle') }}</h2>
      <div class="filters">
        <el-input
          v-model="filters.keyword"
          :placeholder="t('review.searchProduct')"
          clearable
          style="width: 220px"
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" @click="handleSearch">{{ t('common.search') }}</el-button>
      </div>
    </div>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column :label="t('product.image')" width="80">
        <template #default="{ row }">
          <el-image
            v-if="row.product?.image"
            :src="resolveImageUrl(row.product.image)"
            style="width: 48px; height: 48px"
            fit="cover"
          />
        </template>
      </el-table-column>
      <el-table-column :label="t('product.name')" min-width="140">
        <template #default="{ row }">{{ row.product?.name || '-' }}</template>
      </el-table-column>
      <el-table-column :label="t('review.customer')" min-width="100">
        <template #default="{ row }">{{ row.customer?.nickname || '-' }}</template>
      </el-table-column>
      <el-table-column :label="t('review.rating')" width="120">
        <template #default="{ row }">
          <el-rate :model-value="row.rating" disabled />
        </template>
      </el-table-column>
      <el-table-column :label="t('review.content')" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">{{ row.content }}</template>
      </el-table-column>
      <el-table-column :label="t('review.stats')" width="140">
        <template #default="{ row }">
          👁 {{ row.view_count }} · 💬 {{ row.comment_count }} · 👍 {{ row.like_count }}
        </template>
      </el-table-column>
      <el-table-column :label="t('common.createdAt')" width="160">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column v-bind="ACTION_COLUMN">
        <template #default="{ row }">
          <TableActionMenu
            :actions="[
              { label: t('common.delete'), type: 'danger', onClick: () => handleDelete(row) },
            ]"
          />
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
        @size-change="fetchList"
      />
    </div>
  </div>
</template>
