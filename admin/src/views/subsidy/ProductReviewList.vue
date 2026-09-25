<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSubsidyProducts, reviewSubsidyProduct } from '@/api/subsidy'
import { resolveImageUrl } from '@/utils/media'

const { t } = useI18n()
const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ status: 'pending', keyword: '' })

const STATUS_MAP = {
  pending: { label: '待审核', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' },
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getSubsidyProducts({
      page: pagination.page,
      page_size: pagination.pageSize,
      status: filters.status || undefined,
      keyword: filters.keyword || undefined,
    })
    tableData.value = res.data.results || []
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

async function handleApprove(row) {
  await ElMessageBox.confirm(t('subsidy.approveConfirm'), t('common.tip'), { type: 'warning' })
  await reviewSubsidyProduct(row.id, { action: 'approve' })
  ElMessage.success(t('subsidy.reviewSuccess'))
  fetchList()
}

async function handleReject(row) {
  const { value } = await ElMessageBox.prompt(t('subsidy.rejectReasonPlaceholder'), t('subsidy.reject'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    inputPattern: /.+/,
    inputErrorMessage: t('subsidy.rejectReasonRequired'),
  })
  await reviewSubsidyProduct(row.id, { action: 'reject', reject_reason: value })
  ElMessage.success(t('subsidy.reviewSuccess'))
  fetchList()
}

onMounted(fetchList)
</script>

<template>
  <div class="page-card">
    <div class="page-header">
      <h2>{{ t('subsidy.reviewTitle') }}</h2>
      <div class="filters">
        <el-select v-model="filters.status" style="width: 140px" @change="fetchList">
          <el-option label="待审核" value="pending" />
          <el-option label="已通过" value="approved" />
          <el-option label="已驳回" value="rejected" />
        </el-select>
        <el-input
          v-model="filters.keyword"
          :placeholder="t('subsidy.searchProduct')"
          clearable
          style="width: 220px"
          @keyup.enter="fetchList"
        />
        <el-button type="primary" @click="fetchList">{{ t('common.search') }}</el-button>
      </div>
    </div>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column :label="t('product.image')" width="80">
        <template #default="{ row }">
          <el-image :src="resolveImageUrl(row.product_image)" style="width: 48px; height: 48px" fit="cover" />
        </template>
      </el-table-column>
      <el-table-column prop="product_name" :label="t('product.name')" min-width="160" />
      <el-table-column prop="tenant_name" :label="t('tenant.name')" width="140" />
      <el-table-column prop="product_price" :label="t('product.price')" width="100" />
      <el-table-column prop="policy_name" :label="t('subsidy.policyName')" width="140" />
      <el-table-column prop="status" :label="t('common.status')" width="100">
        <template #default="{ row }">
          <el-tag :type="STATUS_MAP[row.status]?.type">{{ STATUS_MAP[row.status]?.label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="subsidy_amount" :label="t('subsidy.subsidyAmount')" width="100" />
      <el-table-column prop="reject_reason" :label="t('subsidy.rejectReason')" min-width="160" show-overflow-tooltip />
      <el-table-column :label="t('common.action')" width="180" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'pending'">
            <el-button link type="success" @click="handleApprove(row)">{{ t('subsidy.approve') }}</el-button>
            <el-button link type="danger" @click="handleReject(row)">{{ t('subsidy.reject') }}</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        layout="total, prev, pager, next"
        :total="pagination.total"
        @current-change="fetchList"
      />
    </div>
  </div>
</template>

<style scoped>
.page-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.page-header h2 {
  margin: 0;
  font-size: 18px;
}
.filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
