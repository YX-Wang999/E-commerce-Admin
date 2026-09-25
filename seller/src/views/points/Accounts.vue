<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getSellerPointsAccounts } from '@/api/sellerPoints'

const router = useRouter()
const { t } = useI18n()

const loading = ref(false)
const keyword = ref('')
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

async function fetchList() {
  loading.value = true
  try {
    const res = await getSellerPointsAccounts({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value.trim() || undefined,
    })
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

function viewTransactions(row) {
  router.push({ name: 'SellerPointsTransactions', query: { customer_id: row.customer } })
}

function handlePageChange(value) {
  page.value = value
  fetchList()
}

onMounted(fetchList)
</script>

<template>
  <div class="page-card">
    <h2>{{ t('sellerPoints.accountsTitle') }}</h2>

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
      <el-table-column prop="customer_name" :label="t('sellerPoints.customerName')" min-width="120" />
      <el-table-column prop="customer_phone" :label="t('sellerPoints.customerPhone')" min-width="120" />
      <el-table-column prop="balance" :label="t('sellerPoints.balance')" width="100" />
      <el-table-column prop="total_earned" :label="t('sellerPoints.totalEarned')" width="100" />
      <el-table-column prop="total_spent" :label="t('sellerPoints.totalSpent')" width="100" />
      <el-table-column prop="expire_at" :label="t('sellerPoints.expireAt')" min-width="160" />
      <el-table-column :label="t('seller.actions')" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="viewTransactions(row)">
            {{ t('sellerPoints.viewTransactions') }}
          </el-button>
        </template>
      </el-table-column>
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
</style>
