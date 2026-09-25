<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adjustSellerPoints, getSellerPointsTransactions } from '@/api/sellerPoints'

const route = useRoute()
const { t } = useI18n()

const loading = ref(false)
const keyword = ref('')
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const customerId = ref(route.query.customer_id ? Number(route.query.customer_id) : null)

async function fetchList() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value.trim() || undefined,
    }
    if (customerId.value) {
      params.customer_id = customerId.value
    }
    const res = await getSellerPointsTransactions(params)
    list.value = res.data?.results || res.data || []
    total.value = res.data?.count || list.value.length
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  fetchList()
}

function handlePageChange(value) {
  page.value = value
  fetchList()
}

async function handleAdjust() {
  try {
    const { value: customerIdInput } = await ElMessageBox.prompt(
      t('sellerPoints.adjustCustomerId'),
      t('sellerPoints.adjustTitle'),
      { inputPattern: /^\d+$/, inputErrorMessage: t('sellerPoints.adjustCustomerIdInvalid') },
    )
    const { value: amountInput } = await ElMessageBox.prompt(
      t('sellerPoints.adjustAmountHint'),
      t('sellerPoints.adjustTitle'),
      { inputPattern: /^-?\d+$/, inputErrorMessage: t('sellerPoints.adjustAmountInvalid') },
    )
    await adjustSellerPoints({
      customer_id: Number(customerIdInput),
      amount: Number(amountInput),
      description: t('sellerPoints.adjustDefaultDesc'),
    })
    ElMessage.success(t('sellerPoints.adjustSuccess'))
    await fetchList()
  } catch {
    // cancelled or failed
  }
}

onMounted(fetchList)
</script>

<template>
  <div class="page-card">
    <div class="page-header">
      <h2>{{ t('sellerPoints.transactionsTitle') }}</h2>
      <el-button type="primary" plain @click="handleAdjust">{{ t('sellerPoints.adjustPoints') }}</el-button>
    </div>

    <div class="toolbar">
      <el-input
        v-model="keyword"
        clearable
        :placeholder="t('sellerPoints.searchUserPlaceholder')"
        style="width: 260px"
        @keyup.enter="handleSearch"
      />
      <el-button type="primary" @click="handleSearch">{{ t('seller.query') }}</el-button>
    </div>

    <el-table v-loading="loading" :data="list" stripe>
      <el-table-column prop="customer_name" :label="t('sellerPoints.customerName')" min-width="100" />
      <el-table-column prop="amount" :label="t('sellerPoints.changeAmount')" width="90">
        <template #default="{ row }">
          <span :class="row.amount >= 0 ? 'text-earn' : 'text-spend'">
            {{ row.amount >= 0 ? '+' : '' }}{{ row.amount }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="trans_type_display" :label="t('sellerPoints.changeType')" width="110" />
      <el-table-column prop="description" :label="t('sellerPoints.description')" min-width="160" show-overflow-tooltip />
      <el-table-column prop="balance_after" :label="t('sellerPoints.balanceAfter')" width="100" />
      <el-table-column prop="created_at" :label="t('seller.createTime')" min-width="160" />
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        layout="total, prev, pager, next"
        :total="total"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.page-header h2 {
  margin: 0;
}

.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.text-earn {
  color: #67c23a;
}

.text-spend {
  color: #f56c6c;
}
</style>
