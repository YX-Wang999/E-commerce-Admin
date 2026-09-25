<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getComplaintList } from '@/api/complaint'
import { useComplaintBadgeStore } from '@/stores/complaintBadge'

const router = useRouter()
const { t } = useI18n()
const complaintBadgeStore = useComplaintBadgeStore()

const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ status: 'platform_reviewing', category: '', tenant_id: '', keyword: '' })

const STATUS_MAP = computed(() => ({
  pending: { label: t('complaint.statusPending'), type: 'warning' },
  merchant_processing: { label: t('complaint.statusMerchantProcessing'), type: '' },
  customer_review: { label: t('complaint.statusCustomerReview'), type: 'primary' },
  platform_reviewing: { label: t('complaint.statusPlatformReviewing'), type: 'danger' },
  resolved: { label: t('complaint.statusResolved'), type: 'success' },
  rejected: { label: t('complaint.statusRejected'), type: 'info' },
  closed: { label: t('complaint.statusClosed'), type: 'info' },
}))

async function fetchList() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      category: filters.category || undefined,
      tenant_id: filters.tenant_id || undefined,
      keyword: filters.keyword || undefined,
    }
    if (filters.status === '__all__') {
      params.all = '1'
    } else if (filters.status) {
      params.status = filters.status
    }
    const res = await getComplaintList(params)
    tableData.value = res.data.results || []
    pagination.total = res.data.count || 0
    await complaintBadgeStore.refresh()
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

function openDetail(row) {
  router.push({ name: 'ComplaintDetail', params: { id: row.id } })
}

onMounted(fetchList)
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <span>{{ t('complaint.listTitle') }}</span>
    </template>

    <el-form :inline="true" class="filter-form">
      <el-form-item :label="t('common.status')">
        <el-select v-model="filters.status" clearable style="width: 180px" @change="handleSearch">
          <el-option :label="t('complaint.statusPlatformReviewing')" value="platform_reviewing" />
          <el-option :label="t('complaint.filterAll')" value="__all__" />
          <el-option :label="t('complaint.statusPending')" value="pending" />
          <el-option :label="t('complaint.statusMerchantProcessing')" value="merchant_processing" />
          <el-option :label="t('complaint.statusResolved')" value="resolved" />
          <el-option :label="t('complaint.statusRejected')" value="rejected" />
          <el-option :label="t('complaint.statusClosed')" value="closed" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('complaint.category')">
        <el-select v-model="filters.category" clearable style="width: 150px">
          <el-option :label="t('complaint.categoryProductQuality')" value="product_quality" />
          <el-option :label="t('complaint.categoryShipping')" value="shipping" />
          <el-option :label="t('complaint.categoryRefund')" value="refund" />
          <el-option :label="t('complaint.categoryOther')" value="other" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('complaint.keyword')">
        <el-input v-model="filters.keyword" clearable @keyup.enter="handleSearch" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">{{ t('common.search') }}</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="complaint_no" :label="t('complaint.no')" min-width="150" />
      <el-table-column prop="customer_name" :label="t('complaint.customer')" width="110" />
      <el-table-column prop="tenant_name" :label="t('complaint.tenant')" width="120" />
      <el-table-column prop="order_no" :label="t('complaint.orderNo')" min-width="150" />
      <el-table-column prop="title" :label="t('complaint.title')" min-width="180" show-overflow-tooltip />
      <el-table-column :label="t('common.status')" width="120">
        <template #default="{ row }">
          <el-tag :type="STATUS_MAP[row.status]?.type || 'info'" size="small">
            {{ STATUS_MAP[row.status]?.label || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" :label="t('complaint.createdAt')" width="170" />
      <el-table-column :label="t('common.actions')" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">{{ t('common.detail') }}</el-button>
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
  </el-card>
</template>

<style scoped>
.filter-form { margin-bottom: 16px; }
.pagination { margin-top: 16px; justify-content: flex-end; }
</style>
