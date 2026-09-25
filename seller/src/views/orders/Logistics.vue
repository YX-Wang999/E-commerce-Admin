<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getOrderList } from '@/api/orders'

const router = useRouter()
const { t } = useI18n()
const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ keyword: '', status: 'shipped' })

const statusMap = computed(() => ({
  shipped: { label: t('order.statusShipped'), type: 'warning' },
  completed: { label: t('order.statusCompleted'), type: 'success' },
}))

async function fetchList() {
  loading.value = true
  try {
    const res = await getOrderList({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
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

function handlePageChange(page) {
  pagination.page = page
  fetchList()
}

function openDetail(row) {
  router.push({ name: 'OrderDetail', params: { id: row.id } })
}

onMounted(fetchList)
</script>

<template>
  <div class="page-card">
    <div class="page-head">
      <h2>{{ t('seller.menuLogistics') }}</h2>
      <el-button @click="fetchList">{{ t('seller.refresh') }}</el-button>
    </div>

    <el-form inline class="filter-form">
      <el-form-item :label="t('seller.keyword')">
        <el-input v-model="filters.keyword" clearable :placeholder="t('seller.orderKeywordPlaceholder')" />
      </el-form-item>
      <el-form-item :label="t('seller.status')">
        <el-select v-model="filters.status" clearable style="width: 140px">
          <el-option :label="t('order.statusShipped')" value="shipped" />
          <el-option :label="t('order.statusCompleted')" value="completed" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">{{ t('seller.query') }}</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="tableData" stripe>
      <el-table-column prop="order_no" :label="t('seller.orderNo')" min-width="160" />
      <el-table-column prop="customer_name" :label="t('seller.customer')" width="120" />
      <el-table-column prop="status" :label="t('seller.status')" width="100">
        <template #default="{ row }">
          <el-tag :type="statusMap[row.status]?.type || 'info'" size="small">
            {{ statusMap[row.status]?.label || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="logistics_no" :label="t('seller.trackingNumber')" min-width="160" />
      <el-table-column prop="logistics?.express_company" :label="t('seller.expressCompany')" min-width="120">
        <template #default="{ row }">
          {{ row.logistics?.express_company || '—' }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" :label="t('seller.orderTime')" width="170" />
      <el-table-column :label="t('seller.actions')" width="90" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">{{ t('seller.detail') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="pagination.page"
        :page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
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
.filter-form {
  margin-bottom: 16px;
}
.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
