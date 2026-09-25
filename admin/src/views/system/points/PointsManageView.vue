<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  adjustPoints,
  getPointsAccounts,
  getPointsTransactions,
} from '@/api/points'
import { ACTION_COLUMN } from '@/config/table'

const { t } = useI18n()
const authStore = useAuthStore()

const activeTab = ref('accounts')
const loading = ref(false)
const adjustVisible = ref(false)
const adjustFormRef = ref(null)
const accountData = ref([])
const transactionData = ref([])
const accountPagination = reactive({ page: 1, pageSize: 20, total: 0 })
const txnPagination = reactive({ page: 1, pageSize: 20, total: 0 })
const accountFilters = reactive({ keyword: '' })
const txnFilters = reactive({ keyword: '', customer_id: '', trans_type: '' })

const adjustForm = reactive({
  customer_id: null,
  customer_name: '',
  amount: 0,
  description: '',
})

const roleCodes = computed(() => authStore.user?.roles?.map((item) => item.code) || [])
const isSuper = computed(() => Boolean(authStore.user?.is_superuser))
const canAdjust = computed(() => {
  if (isSuper.value) return true
  return roleCodes.value.some((code) => ['super_admin', 'ops_director'].includes(code))
})

const adjustRules = computed(() => ({
  amount: [{ required: true, message: t('points.adjustAmountRequired'), trigger: 'blur' }],
}))

const TYPE_OPTIONS = computed(() => [
  { label: t('points.typeSignIn'), value: 'earn_sign_in' },
  { label: t('points.typeOrder'), value: 'earn_order' },
  { label: t('points.typeReview'), value: 'earn_review' },
  { label: t('points.typeRedeem'), value: 'spend_redeem' },
  { label: t('points.typeAdjust'), value: 'adjust_admin' },
])

async function fetchAccounts() {
  loading.value = true
  try {
    const res = await getPointsAccounts({
      page: accountPagination.page,
      page_size: accountPagination.pageSize,
      keyword: accountFilters.keyword || undefined,
    })
    accountData.value = res.data.results || []
    accountPagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

async function fetchTransactions() {
  loading.value = true
  try {
    const res = await getPointsTransactions({
      page: txnPagination.page,
      page_size: txnPagination.pageSize,
      keyword: txnFilters.keyword || undefined,
      customer_id: txnFilters.customer_id || undefined,
      trans_type: txnFilters.trans_type || undefined,
    })
    transactionData.value = res.data.results || []
    txnPagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

function handleAccountSearch() {
  accountPagination.page = 1
  fetchAccounts()
}

function handleTxnSearch() {
  txnPagination.page = 1
  fetchTransactions()
}

function openAdjust(row) {
  adjustForm.customer_id = row.customer
  adjustForm.customer_name = row.customer_name
  adjustForm.amount = 0
  adjustForm.description = ''
  adjustVisible.value = true
}

function viewTransactions(row) {
  activeTab.value = 'transactions'
  txnFilters.customer_id = String(row.customer)
  txnFilters.keyword = ''
  handleTxnSearch()
}

async function handleAdjustSubmit() {
  await adjustFormRef.value.validate()
  await ElMessageBox.confirm(
    t('points.adjustConfirm', { name: adjustForm.customer_name, amount: adjustForm.amount }),
    t('common.tip'),
    { type: 'warning' },
  )
  await adjustPoints({
    customer_id: adjustForm.customer_id,
    amount: adjustForm.amount,
    description: adjustForm.description,
  })
  ElMessage.success(t('points.adjustSuccess'))
  adjustVisible.value = false
  fetchAccounts()
  if (activeTab.value === 'transactions') {
    fetchTransactions()
  }
}

function onTabChange(name) {
  if (name === 'accounts') {
    fetchAccounts()
  } else {
    fetchTransactions()
  }
}

onMounted(fetchAccounts)
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <span>{{ t('points.manageTitle') }}</span>
    </template>

    <p class="page-tip">{{ t('points.platformScopeTip') }}</p>

    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <el-tab-pane :label="t('points.accountTab')" name="accounts">
        <el-form :inline="true" class="filter-form">
          <el-form-item :label="t('common.keyword')">
            <el-input
              v-model="accountFilters.keyword"
              :placeholder="t('points.keywordPlaceholder')"
              clearable
              @keyup.enter="handleAccountSearch"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleAccountSearch">{{ t('common.search') }}</el-button>
          </el-form-item>
        </el-form>

        <el-table v-loading="loading" :data="accountData" border stripe>
          <el-table-column prop="customer_name" :label="t('customer.name')" width="120" />
          <el-table-column prop="customer_phone" :label="t('customer.phone')" width="130" />
          <el-table-column prop="balance" :label="t('points.balance')" width="110" />
          <el-table-column prop="total_earned" :label="t('points.totalEarned')" width="110" />
          <el-table-column prop="total_spent" :label="t('points.totalSpent')" width="110" />
          <el-table-column prop="updated_at" :label="t('points.updatedAt')" width="170" class-name="col-hide-md" />
          <el-table-column
            :label="t('common.actions')"
            :min-width="ACTION_COLUMN.standard"
            class-name="col-actions"
            fixed="right"
          >
            <template #default="{ row }">
              <el-button link type="primary" @click="viewTransactions(row)">{{ t('points.viewTransactions') }}</el-button>
              <el-button v-if="canAdjust" link type="warning" @click="openAdjust(row)">{{ t('points.adjust') }}</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-wrap">
          <el-pagination
            v-model:current-page="accountPagination.page"
            v-model:page-size="accountPagination.pageSize"
            :total="accountPagination.total"
            layout="total, prev, pager, next"
            background
            @current-change="fetchAccounts"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane :label="t('points.transactionTab')" name="transactions">
        <el-form :inline="true" class="filter-form">
          <el-form-item :label="t('common.keyword')">
            <el-input v-model="txnFilters.keyword" clearable @keyup.enter="handleTxnSearch" />
          </el-form-item>
          <el-form-item :label="t('points.type')">
            <el-select v-model="txnFilters.trans_type" clearable :placeholder="t('common.all')" style="width: 140px">
              <el-option v-for="item in TYPE_OPTIONS" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleTxnSearch">{{ t('common.search') }}</el-button>
          </el-form-item>
        </el-form>

        <el-table v-loading="loading" :data="transactionData" border stripe>
          <el-table-column prop="customer_name" :label="t('customer.name')" width="100" />
          <el-table-column prop="description" :label="t('points.description')" min-width="180" show-overflow-tooltip />
          <el-table-column :label="t('points.type')" width="110">
            <template #default="{ row }">{{ row.trans_type_label || row.trans_type }}</template>
          </el-table-column>
          <el-table-column :label="t('points.amount')" width="90">
            <template #default="{ row }">
              <span :class="row.amount >= 0 ? 'amount-plus' : 'amount-minus'">
                {{ row.amount >= 0 ? '+' : '' }}{{ row.amount }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="balance_after" :label="t('points.balanceAfter')" width="100" />
          <el-table-column prop="created_at" :label="t('points.createdAt')" width="170" />
        </el-table>

        <div class="pagination-wrap">
          <el-pagination
            v-model:current-page="txnPagination.page"
            v-model:page-size="txnPagination.pageSize"
            :total="txnPagination.total"
            layout="total, prev, pager, next"
            background
            @current-change="fetchTransactions"
          />
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-card>

  <el-dialog v-model="adjustVisible" :title="t('points.adjustTitle')" width="420px">
    <el-form ref="adjustFormRef" :model="adjustForm" :rules="adjustRules" label-width="90px">
      <el-form-item :label="t('customer.name')">
        <span>{{ adjustForm.customer_name }}</span>
      </el-form-item>
      <el-form-item :label="t('points.amount')" prop="amount">
        <el-input-number v-model="adjustForm.amount" :step="10" style="width: 100%" />
      </el-form-item>
      <el-form-item :label="t('common.remark')">
        <el-input v-model="adjustForm.description" type="textarea" :rows="3" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="adjustVisible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" @click="handleAdjustSubmit">{{ t('common.confirm') }}</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.filter-form {
  margin-bottom: 16px;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.amount-plus {
  color: #67c23a;
  font-weight: 600;
}
.amount-minus {
  color: #f56c6c;
  font-weight: 600;
}
.page-tip {
  margin: 0 0 12px;
  color: #909399;
  font-size: 13px;
}
</style>
