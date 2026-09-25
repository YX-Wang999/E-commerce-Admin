<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getPointsMallOrders, shipPointsMallOrder } from '@/api/pointsMall'

const { t } = useI18n()
const loading = ref(false)
const submitting = ref(false)
const tableData = ref([])
const keyword = ref('')
const filterStatus = ref('')
const shipVisible = ref(false)
const shipForm = reactive({ id: null, logistics_company: '', logistics_no: '', remark: '' })

const statusOptions = computed(() => [
  { value: 'pending', label: t('pointsMall.orderPending') },
  { value: 'processing', label: t('pointsMall.orderProcessing') },
  { value: 'shipped', label: t('pointsMall.orderShipped') },
  { value: 'completed', label: t('pointsMall.orderCompleted') },
  { value: 'cancelled', label: t('pointsMall.orderCancelled') },
])

async function fetchList() {
  loading.value = true
  try {
    const res = await getPointsMallOrders({
      page_size: 100,
      keyword: keyword.value || undefined,
      status: filterStatus.value || undefined,
    })
    tableData.value = res.data.results || res.data || []
  } finally {
    loading.value = false
  }
}

function statusLabel(value) {
  return statusOptions.value.find((item) => item.value === value)?.label || value
}

function openShip(row) {
  shipForm.id = row.id
  shipForm.logistics_company = row.logistics_company || ''
  shipForm.logistics_no = row.logistics_no || ''
  shipForm.remark = row.remark || ''
  shipVisible.value = true
}

async function submitShip() {
  if (!shipForm.logistics_no.trim()) {
    ElMessage.warning(t('pointsMall.logisticsNoRequired'))
    return
  }
  submitting.value = true
  try {
    await shipPointsMallOrder(shipForm.id, {
      logistics_company: shipForm.logistics_company,
      logistics_no: shipForm.logistics_no,
      remark: shipForm.remark,
    })
    ElMessage.success(t('pointsMall.shipSuccess'))
    shipVisible.value = false
    await fetchList()
  } finally {
    submitting.value = false
  }
}

onMounted(fetchList)
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <span>{{ t('pointsMall.ordersTitle') }}</span>
    </template>

    <div class="toolbar">
      <el-input v-model="keyword" :placeholder="t('pointsMall.orderKeywordPlaceholder')" clearable style="width: 220px" @clear="fetchList" @keyup.enter="fetchList" />
      <el-select v-model="filterStatus" clearable :placeholder="t('common.status')" style="width: 140px" @change="fetchList">
        <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-button type="primary" @click="fetchList">{{ t('common.search') }}</el-button>
    </div>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="order_no" :label="t('pointsMall.orderNo')" width="170" />
      <el-table-column prop="item_name" :label="t('pointsMall.itemName')" min-width="120" />
      <el-table-column :label="t('pointsMall.customer')" min-width="120">
        <template #default="{ row }">{{ row.customer?.nickname || row.customer?.phone || '-' }}</template>
      </el-table-column>
      <el-table-column prop="points_spent" :label="t('pointsMall.pointsSpent')" width="100" />
      <el-table-column prop="quantity" :label="t('pointsMall.quantity')" width="80" />
      <el-table-column :label="t('common.status')" width="100">
        <template #default="{ row }">{{ statusLabel(row.status) }}</template>
      </el-table-column>
      <el-table-column prop="coupon_code" :label="t('pointsMall.couponCode')" width="120" />
      <el-table-column :label="t('common.actions')" width="100" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'pending' || row.status === 'processing'"
            link
            type="primary"
            @click="openShip(row)"
          >
            {{ t('pointsMall.ship') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="shipVisible" :title="t('pointsMall.shipTitle')" width="480px">
      <el-form label-width="100px">
        <el-form-item :label="t('pointsMall.logisticsCompany')">
          <el-input v-model="shipForm.logistics_company" />
        </el-form-item>
        <el-form-item :label="t('pointsMall.logisticsNo')" required>
          <el-input v-model="shipForm.logistics_no" />
        </el-form-item>
        <el-form-item :label="t('pointsMall.remark')">
          <el-input v-model="shipForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shipVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="submitting" @click="submitShip">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<style scoped>
.toolbar { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
</style>
