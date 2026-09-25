<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  createPointsMallItem,
  deletePointsMallItem,
  getPointsMallItems,
  getPointsMallStats,
  updatePointsMallItem,
} from '@/api/pointsMall'

const { t } = useI18n()
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const editingId = ref(null)
const tableData = ref([])
const stats = ref(null)
const keyword = ref('')
const filterType = ref('')
const filterStatus = ref('')

const form = reactive({
  name: '',
  image: '',
  description: '',
  item_type: 'physical',
  points_required: 100,
  stock: 0,
  per_user_limit: 1,
  requires_address: false,
  is_hot: false,
  is_limited_time: false,
  end_at: '',
  status: 'draft',
  sort_order: 0,
})

const typeOptions = computed(() => [
  { value: 'physical', label: t('pointsMall.typePhysical') },
  { value: 'coupon', label: t('pointsMall.typeCoupon') },
  { value: 'benefit', label: t('pointsMall.typeBenefit') },
  { value: 'lottery', label: t('pointsMall.typeLottery') },
])

const statusOptions = computed(() => [
  { value: 'draft', label: t('pointsMall.statusDraft') },
  { value: 'on_sale', label: t('pointsMall.statusOnSale') },
  { value: 'off_sale', label: t('pointsMall.statusOffSale') },
])

async function fetchList() {
  loading.value = true
  try {
    const [listRes, statsRes] = await Promise.all([
      getPointsMallItems({
        page_size: 100,
        keyword: keyword.value || undefined,
        item_type: filterType.value || undefined,
        status: filterStatus.value || undefined,
      }),
      getPointsMallStats(),
    ])
    tableData.value = listRes.data.results || listRes.data || []
    stats.value = statsRes.data || null
  } finally {
    loading.value = false
  }
}

function resetForm() {
  editingId.value = null
  Object.assign(form, {
    name: '',
    image: '',
    description: '',
    item_type: 'physical',
    points_required: 100,
    stock: 0,
    per_user_limit: 1,
    requires_address: false,
    is_hot: false,
    is_limited_time: false,
    end_at: '',
    status: 'draft',
    sort_order: 0,
  })
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    image: row.image || '',
    description: row.description || '',
    item_type: row.item_type,
    points_required: row.points_required,
    stock: row.stock,
    per_user_limit: row.per_user_limit,
    requires_address: row.requires_address,
    is_hot: row.is_hot,
    is_limited_time: row.is_limited_time,
    end_at: row.end_at || '',
    status: row.status,
    sort_order: row.sort_order || 0,
  })
  dialogVisible.value = true
}

async function submitForm() {
  if (!form.name.trim()) {
    ElMessage.warning(t('pointsMall.nameRequired'))
    return
  }
  submitting.value = true
  try {
    const payload = {
      ...form,
      requires_address: form.item_type === 'physical' ? form.requires_address : false,
      end_at: form.end_at || null,
    }
    if (editingId.value) {
      await updatePointsMallItem(editingId.value, payload)
      ElMessage.success(t('common.updateSuccess'))
    } else {
      await createPointsMallItem(payload)
      ElMessage.success(t('common.createSuccess'))
    }
    dialogVisible.value = false
    await fetchList()
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(t('pointsMall.offShelfConfirm', { name: row.name }), t('common.confirm'))
  await deletePointsMallItem(row.id)
  ElMessage.success(t('common.updateSuccess'))
  await fetchList()
}

function typeLabel(value) {
  return typeOptions.value.find((item) => item.value === value)?.label || value
}

function statusLabel(value) {
  return statusOptions.value.find((item) => item.value === value)?.label || value
}

onMounted(fetchList)
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>{{ t('pointsMall.itemsTitle') }}</span>
        <el-button type="primary" :icon="Plus" @click="openCreate">{{ t('common.create') }}</el-button>
      </div>
    </template>

    <div v-if="stats" class="stats-row">
      <el-statistic :title="t('pointsMall.statOrders')" :value="stats.order_count" />
      <el-statistic :title="t('pointsMall.statPoints')" :value="stats.points_spent" />
      <el-statistic :title="t('pointsMall.statOnSale')" :value="stats.item_count" />
    </div>

    <div class="toolbar">
      <el-input v-model="keyword" :placeholder="t('pointsMall.keywordPlaceholder')" clearable style="width: 220px" @clear="fetchList" @keyup.enter="fetchList" />
      <el-select v-model="filterType" clearable :placeholder="t('pointsMall.filterType')" style="width: 140px" @change="fetchList">
        <el-option v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-select v-model="filterStatus" clearable :placeholder="t('common.status')" style="width: 140px" @change="fetchList">
        <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-button type="primary" @click="fetchList">{{ t('common.search') }}</el-button>
    </div>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="name" :label="t('pointsMall.itemName')" min-width="140" />
      <el-table-column :label="t('pointsMall.itemType')" width="100">
        <template #default="{ row }">{{ typeLabel(row.item_type) }}</template>
      </el-table-column>
      <el-table-column prop="points_required" :label="t('pointsMall.pointsRequired')" width="100" />
      <el-table-column prop="stock" :label="t('pointsMall.stock')" width="80" />
      <el-table-column prop="exchanged_count" :label="t('pointsMall.exchangedCount')" width="100" />
      <el-table-column :label="t('pointsMall.endAt')" width="170">
        <template #default="{ row }">{{ row.end_at ? row.end_at.replace('T', ' ').slice(0, 16) : '-' }}</template>
      </el-table-column>
      <el-table-column :label="t('common.status')" width="100">
        <template #default="{ row }">{{ statusLabel(row.status) }}</template>
      </el-table-column>
      <el-table-column :label="t('common.actions')" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">{{ t('common.edit') }}</el-button>
          <el-button v-if="row.status !== 'off_sale'" link type="danger" @click="handleDelete(row)">{{ t('pointsMall.offShelf') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingId ? t('common.edit') : t('common.create')" width="560px">
      <el-form label-width="110px">
        <el-form-item :label="t('pointsMall.itemName')" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item :label="t('pointsMall.itemType')">
          <el-select v-model="form.item_type" style="width: 100%">
            <el-option v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('pointsMall.pointsRequired')">
          <el-input-number v-model="form.points_required" :min="1" />
        </el-form-item>
        <el-form-item :label="t('pointsMall.stock')">
          <el-input-number v-model="form.stock" :min="0" />
        </el-form-item>
        <el-form-item :label="t('pointsMall.perUserLimit')">
          <el-input-number v-model="form.per_user_limit" :min="1" />
        </el-form-item>
        <el-form-item :label="t('common.status')">
          <el-select v-model="form.status" style="width: 100%">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('pointsMall.description')">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item :label="t('pointsMall.imageUrl')">
          <el-input v-model="form.image" />
        </el-form-item>
        <el-form-item :label="t('pointsMall.flags')">
          <el-checkbox v-model="form.is_hot">{{ t('pointsMall.hot') }}</el-checkbox>
          <el-checkbox v-model="form.is_limited_time">{{ t('pointsMall.limitedTime') }}</el-checkbox>
          <el-checkbox v-if="form.item_type === 'physical'" v-model="form.requires_address">{{ t('pointsMall.requiresAddress') }}</el-checkbox>
        </el-form-item>
        <el-form-item :label="t('pointsMall.endAt')">
          <el-date-picker
            v-model="form.end_at"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss"
            :placeholder="t('pointsMall.endAtPlaceholder')"
            style="width: 100%"
            clearable
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<style scoped>
.card-header { display: flex; align-items: center; justify-content: space-between; }
.stats-row { display: flex; gap: 32px; margin-bottom: 16px; }
.toolbar { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
</style>
