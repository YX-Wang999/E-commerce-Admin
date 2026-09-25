<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import SubsidyTag from '@shared/components/SubsidyTag.vue'
import {
  applySubsidy,
  exportFilingMaterials,
  getAvailableSubsidyProducts,
  getSubsidyApplications,
  getSubsidyOrders,
  updateSubsidyOrderCodes,
} from '@/api/subsidy'

const { t } = useI18n()
const activeTab = ref('filing')
const loading = ref(false)
const available = ref([])
const records = ref([])
const orders = ref([])
const selectedIds = ref([])
const statusFilter = ref('')
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const form = reactive({
  region: '浙江省',
  category: '手机',
})

const REGIONS = ['浙江省', '江苏省', '上海市', '广东省', '北京市']
const CATEGORIES = ['手机', '电脑', '平板', '家电', '数码配件']

const FILING_MAP = {
  not_submitted: { label: '未备案', type: 'info' },
  submitted: { label: '备案中', type: 'warning' },
  approved: { label: '已备案', type: 'success' },
  rejected: { label: '备案失败', type: 'danger' },
}

const GOV_MAP = {
  pending: { label: '待上报', type: 'info' },
  reported: { label: '已上报', type: 'warning' },
  verified: { label: '核验通过', type: 'success' },
  failed: { label: '核验失败', type: 'danger' },
}

const orderCodes = reactive({})

function onSelectionChange(rows) {
  selectedIds.value = rows.map((row) => row.id)
}

async function fetchAvailable() {
  loading.value = true
  try {
    const res = await getAvailableSubsidyProducts({ page: pagination.page, page_size: pagination.pageSize })
    available.value = res.data.results || []
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

async function fetchRecords() {
  loading.value = true
  try {
    const res = await getSubsidyApplications({
      page: pagination.page,
      page_size: pagination.pageSize,
      filing_status: statusFilter.value || undefined,
    })
    records.value = res.data.results || []
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

async function fetchOrders() {
  loading.value = true
  try {
    const res = await getSubsidyOrders({ page: pagination.page, page_size: pagination.pageSize })
    orders.value = res.data.results || []
    pagination.total = res.data.count || 0
    orders.value.forEach((row) => {
      if (!orderCodes[row.id]) {
        orderCodes[row.id] = { sn_code: row.sn_code || '', imei_code: row.imei_code || '' }
      }
    })
  } finally {
    loading.value = false
  }
}

function handleTabChange(name) {
  pagination.page = 1
  if (name === 'filing') fetchAvailable()
  else if (name === 'records') fetchRecords()
  else fetchOrders()
}

async function submitFiling() {
  if (!selectedIds.value.length) {
    ElMessage.warning('请选择参与商品')
    return
  }
  for (const productId of selectedIds.value) {
    await applySubsidy({
      product_id: productId,
      region: form.region,
      category: form.category,
    })
  }
  ElMessage.success('备案申请已提交，请向当地商务部门完成政府申报')
  selectedIds.value = []
  activeTab.value = 'records'
  fetchRecords()
}

async function handleExport(row) {
  await exportFilingMaterials(row.id)
  ElMessage.success('申报材料已导出')
}

function openGuide() {
  window.open('https://www.mofcom.gov.cn/', '_blank')
}

async function saveOrderCodes(row) {
  const codes = orderCodes[row.id] || {}
  await updateSubsidyOrderCodes(row.id, {
    sn_code: codes.sn_code || '',
    imei_code: codes.imei_code || '',
  })
  ElMessage.success('SN/IMEI 已保存')
  fetchOrders()
}

onMounted(fetchAvailable)
</script>

<template>
  <div class="subsidy-page">
    <h2>{{ t('seller.subsidyFilingTitle') }}</h2>
    <p class="page-desc">{{ t('seller.subsidyFilingDesc') }}</p>

    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane :label="t('seller.subsidyTabFiling')" name="filing">
        <div class="filing-form card">
          <h3>国补活动报名</h3>
          <el-form inline>
            <el-form-item label="活动地区">
              <el-select v-model="form.region" style="width: 140px">
                <el-option v-for="item in REGIONS" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
            <el-form-item label="补贴品类">
              <el-select v-model="form.category" style="width: 140px">
                <el-option v-for="item in CATEGORIES" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
          </el-form>
          <div class="form-actions">
            <el-button type="primary" :disabled="!selectedIds.length" @click="submitFiling">
              提交备案申请
            </el-button>
            <el-button @click="openGuide">查看备案指南</el-button>
          </div>
        </div>

        <el-table v-loading="loading" :data="available" border @selection-change="onSelectionChange">
          <el-table-column type="selection" width="48" />
          <el-table-column prop="name" label="商品" min-width="180" />
          <el-table-column prop="price" label="售价" width="100" />
          <el-table-column prop="filing_status_label" label="备案状态" width="120">
            <template #default="{ row }">
              <el-tag :type="FILING_MAP[row.filing_status]?.type || 'info'" size="small">
                {{ row.filing_status_label }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane :label="t('seller.subsidyTabRecords')" name="records">
        <el-select v-model="statusFilter" placeholder="备案状态" clearable style="width: 160px; margin-bottom: 12px" @change="fetchRecords">
          <el-option v-for="(item, key) in FILING_MAP" :key="key" :label="item.label" :value="key" />
        </el-select>
        <el-table v-loading="loading" :data="records" border>
          <el-table-column prop="product_name" label="商品" min-width="160" />
          <el-table-column prop="region" label="地区" width="100" />
          <el-table-column prop="category" label="品类" width="100" />
          <el-table-column label="备案状态" width="120">
            <template #default="{ row }">
              <el-tag :type="FILING_MAP[row.filing_status]?.type">{{ row.filing_status_label }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="filing_reject_reason" label="驳回原因" min-width="140" show-overflow-tooltip />
          <el-table-column label="操作" width="140">
            <template #default="{ row }">
              <el-button link type="primary" @click="handleExport(row)">导出申报材料</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="国补订单" name="orders">
        <el-table v-loading="loading" :data="orders" border>
          <el-table-column prop="order_no" label="订单号" width="180" />
          <el-table-column prop="product_name" label="商品" min-width="140" />
          <el-table-column label="上报状态" width="120">
            <template #default="{ row }">
              <el-tag :type="GOV_MAP[row.government_status]?.type">{{ row.government_status_label }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="SN码" width="160">
            <template #default="{ row }">
              <el-input v-model="orderCodes[row.id].sn_code" placeholder="SN码" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="IMEI码" width="180">
            <template #default="{ row }">
              <el-input v-model="orderCodes[row.id].imei_code" placeholder="IMEI码" size="small" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button link type="primary" @click="saveOrderCodes(row)">保存</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.subsidy-page {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}

.page-desc {
  margin: 0 0 16px;
  color: #909399;
  font-size: 13px;
}

.filing-form {
  margin-bottom: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.filing-form h3 {
  margin: 0 0 12px;
  font-size: 16px;
}

.form-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
</style>
