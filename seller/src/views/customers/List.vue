<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getCustomerDetail, getCustomerList } from '@/api/customers'

const router = useRouter()
const { t } = useI18n()
const loading = ref(false)
const detailLoading = ref(false)
const drawerVisible = ref(false)
const tableData = ref([])
const customerDetail = ref(null)
const customerOrders = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ keyword: '' })

const statusMap = computed(() => ({
  pending: t('order.statusPending'),
  paid: t('order.statusPaid'),
  shipped: t('order.statusShipped'),
  completed: t('order.statusCompleted'),
  cancelled: t('order.statusCancelled'),
  refunding: t('order.statusRefunding'),
}))

async function fetchList() {
  loading.value = true
  try {
    const res = await getCustomerList({
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

function handlePageChange(page) {
  pagination.page = page
  fetchList()
}

async function openDetail(row) {
  drawerVisible.value = true
  detailLoading.value = true
  customerDetail.value = null
  customerOrders.value = []
  try {
    const res = await getCustomerDetail(row.id)
    customerDetail.value = res.data.customer
    customerOrders.value = res.data.orders || []
  } finally {
    detailLoading.value = false
  }
}

function goOrder(row) {
  router.push({ name: 'OrderDetail', params: { id: row.id } })
}

onMounted(fetchList)
</script>

<template>
  <div class="page-card">
    <div class="page-header">
      <h2>{{ t('seller.customers') }}</h2>
    </div>

    <el-form inline @submit.prevent="handleSearch">
      <el-form-item :label="t('seller.keyword')">
        <el-input
          v-model="filters.keyword"
          :placeholder="t('seller.customerKeywordPlaceholder')"
          clearable
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">{{ t('seller.query') }}</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="tableData" stripe>
      <el-table-column prop="nickname" :label="t('seller.nickname')" min-width="120" />
      <el-table-column prop="phone" :label="t('seller.phoneLabel')" width="140" />
      <el-table-column prop="order_count" :label="t('seller.orderCount')" width="100" />
      <el-table-column prop="created_at" :label="t('seller.registerTime')" width="170">
        <template #default="{ row }">
          {{ row.created_at ? String(row.created_at).replace('T', ' ').slice(0, 19) : '-' }}
        </template>
      </el-table-column>
      <el-table-column :label="t('seller.actions')" width="100" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="openDetail(row)">{{ t('seller.viewCustomer') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="pagination.page"
        :page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>

    <el-drawer v-model="drawerVisible" :title="t('seller.customerOrders')" size="520px">
      <div v-loading="detailLoading">
        <template v-if="customerDetail">
          <el-descriptions :column="1" border size="small" class="customer-info">
            <el-descriptions-item :label="t('seller.nickname')">{{ customerDetail.nickname || '-' }}</el-descriptions-item>
            <el-descriptions-item :label="t('seller.phoneLabel')">{{ customerDetail.phone || '-' }}</el-descriptions-item>
            <el-descriptions-item :label="t('seller.emailLabel')">{{ customerDetail.email || '-' }}</el-descriptions-item>
          </el-descriptions>

          <h4 class="orders-title">{{ t('seller.customerOrders') }}</h4>
          <el-table :data="customerOrders" size="small" @row-click="goOrder">
            <el-table-column prop="order_no" :label="t('order.orderNo')" min-width="140" />
            <el-table-column prop="total_amount" :label="t('seller.amount')" width="90" />
            <el-table-column :label="t('seller.status')" width="90">
              <template #default="{ row }">{{ statusMap[row.status] || row.status }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!customerOrders.length" :description="t('seller.noOrders')" />
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.pager {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.customer-info {
  margin-bottom: 16px;
}

.orders-title {
  margin: 0 0 12px;
  font-size: 15px;
}
</style>
