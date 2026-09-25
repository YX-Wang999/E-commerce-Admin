<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getComplaintList } from '@/api/complaints'
import { useComplaintBadgeStore } from '@/stores/complaintBadge'

const emit = defineEmits(['updated'])

const router = useRouter()
const { t } = useI18n()
const complaintBadgeStore = useComplaintBadgeStore()

const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ status: '' })

const STATUS_MAP = computed(() => ({
  pending: { label: t('seller.complaintStatusPending'), type: 'warning' },
  merchant_processing: { label: t('seller.complaintStatusProcessing'), type: '' },
  customer_review: { label: t('seller.complaintStatusReview'), type: 'primary' },
  platform_reviewing: { label: t('seller.complaintStatusPlatform'), type: 'danger' },
  resolved: { label: t('seller.complaintStatusResolved'), type: 'success' },
  rejected: { label: t('seller.complaintStatusRejected'), type: 'info' },
  closed: { label: t('seller.complaintStatusClosed'), type: 'info' },
}))

async function fetchList() {
  loading.value = true
  try {
    const res = await getComplaintList({
      page: pagination.page,
      page_size: pagination.pageSize,
      status: filters.status || undefined,
    })
    tableData.value = res.data.results || []
    pagination.total = res.data.count || 0
    await complaintBadgeStore.refresh()
    emit('updated')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

function goDetail(row) {
  router.push({ name: 'RefundDetail', params: { id: row.id } })
}

onMounted(fetchList)
</script>

<template>
  <div class="page-wrap">
    <el-form :inline="true" class="filter-form">
      <el-form-item :label="t('seller.status')">
        <el-select v-model="filters.status" clearable style="width: 160px" @change="handleSearch">
          <el-option :label="t('seller.complaintStatusPending')" value="pending" />
          <el-option :label="t('seller.complaintStatusProcessing')" value="merchant_processing" />
          <el-option :label="t('seller.complaintStatusReview')" value="customer_review" />
          <el-option :label="t('seller.complaintStatusPlatform')" value="platform_reviewing" />
          <el-option :label="t('seller.complaintStatusResolved')" value="resolved" />
        </el-select>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="tableData" border stripe @row-click="goDetail">
      <el-table-column prop="complaint_no" :label="t('seller.complaintNo')" min-width="150" />
      <el-table-column prop="customer_name" :label="t('seller.customer')" width="120" />
      <el-table-column prop="order_no" :label="t('seller.orderNo')" min-width="150" />
      <el-table-column prop="title" :label="t('seller.complaintTitle')" min-width="180" show-overflow-tooltip />
      <el-table-column :label="t('seller.status')" width="120">
        <template #default="{ row }">
          <el-tag :type="STATUS_MAP[row.status]?.type || 'info'" size="small">
            {{ STATUS_MAP[row.status]?.label || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" :label="t('seller.createTime')" width="170" />
      <el-table-column :label="t('seller.actions')" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click.stop="goDetail(row)">
            {{ row.status === 'pending' || row.status === 'merchant_processing' ? t('seller.handle') : t('seller.detail') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :total="pagination.total"
      layout="total, prev, pager, next"
      class="pagination"
      @current-change="fetchList"
    />
  </div>
</template>

<style scoped>
.page-wrap { padding: 4px 0; }
.page-header { margin-bottom: 16px; }
.filter-form { margin-bottom: 16px; }
.pagination { margin-top: 16px; justify-content: flex-end; }
</style>
