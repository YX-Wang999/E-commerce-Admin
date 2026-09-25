<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSubsidyFilings, syncSubsidyFiling } from '@/api/subsidy'
import { resolveImageUrl } from '@/utils/media'

const { t } = useI18n()
const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ filing_status: 'submitted', keyword: '' })

const STATUS_MAP = {
  not_submitted: { label: '未备案', type: 'info' },
  submitted: { label: '已提交备案', type: 'warning' },
  approved: { label: '已备案通过', type: 'success' },
  rejected: { label: '备案驳回', type: 'danger' },
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getSubsidyFilings({
      page: pagination.page,
      page_size: pagination.pageSize,
      filing_status: filters.filing_status || undefined,
      keyword: filters.keyword || undefined,
    })
    tableData.value = res.data.results || []
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

async function handleSync(row, filing_status) {
  if (filing_status === 'rejected') {
    const { value } = await ElMessageBox.prompt('请输入政府驳回原因', '同步备案驳回', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      inputPattern: /.+/,
      inputErrorMessage: '驳回原因不能为空',
    })
    await syncSubsidyFiling(row.id, { filing_status, filing_reject_reason: value })
  } else {
    await ElMessageBox.confirm(
      filing_status === 'approved' ? '确认同步政府「备案通过」状态？' : '确认同步状态？',
      '政府状态同步',
      { type: 'warning' },
    )
    await syncSubsidyFiling(row.id, { filing_status })
  }
  ElMessage.success('状态已同步')
  fetchList()
}

onMounted(fetchList)
</script>

<template>
  <div class="page-card">
    <div class="page-header">
      <div>
        <h2>{{ t('subsidy.monitorTitle') }}</h2>
        <p class="hint">{{ t('subsidy.monitorHint') }}</p>
      </div>
      <div class="filters">
        <el-select v-model="filters.filing_status" style="width: 160px" @change="fetchList">
          <el-option label="已提交备案" value="submitted" />
          <el-option label="已备案通过" value="approved" />
          <el-option label="备案驳回" value="rejected" />
          <el-option label="未备案" value="not_submitted" />
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
          <el-image v-if="row.product_image" :src="resolveImageUrl(row.product_image)" style="width: 48px; height: 48px" fit="cover" />
        </template>
      </el-table-column>
      <el-table-column prop="product_name" :label="t('product.name')" min-width="160" />
      <el-table-column prop="tenant_name" label="商家" width="120" />
      <el-table-column prop="region" label="活动地区" width="100" />
      <el-table-column prop="category" label="补贴品类" width="100" />
      <el-table-column prop="filing_status" label="备案状态" width="120">
        <template #default="{ row }">
          <el-tag :type="STATUS_MAP[row.filing_status]?.type || 'info'">
            {{ row.filing_status_label || STATUS_MAP[row.filing_status]?.label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="filing_submitted_at" label="提交时间" width="170" />
      <el-table-column prop="filing_reject_reason" label="驳回原因" min-width="140" show-overflow-tooltip />
      <el-table-column :label="t('common.action')" width="220" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.filing_status === 'submitted'"
            link
            type="success"
            @click="handleSync(row, 'approved')"
          >
            同步通过
          </el-button>
          <el-button
            v-if="row.filing_status === 'submitted'"
            link
            type="danger"
            @click="handleSync(row, 'rejected')"
          >
            同步驳回
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="fetchList"
      />
    </div>
  </div>
</template>

<style scoped>
.page-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0 0 4px;
  font-size: 18px;
}

.hint {
  margin: 0;
  font-size: 13px;
  color: #909399;
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
