<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  createSuperDiscount,
  deleteSuperDiscount,
  getSuperDiscountList,
  updateSuperDiscount,
} from '@/api/promotion'

const { t } = useI18n()
const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const formRef = ref(null)
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const form = reactive({
  id: null,
  title: '超级立减',
  promo_text: '',
  amount: 15,
  button_text: '立即领取',
  link_url: '/coupons',
  is_active: true,
  start_time: '',
  end_time: '',
})

const dialogTitle = computed(() => (form.id ? t('superDiscount.edit') : t('superDiscount.create')))

const rules = computed(() => ({
  title: [{ required: true, message: t('superDiscount.titleRequired'), trigger: 'blur' }],
  promo_text: [{ required: true, message: t('superDiscount.promoTextRequired'), trigger: 'blur' }],
  amount: [{ required: true, message: t('superDiscount.amountRequired'), trigger: 'blur' }],
  button_text: [{ required: true, message: t('superDiscount.buttonTextRequired'), trigger: 'blur' }],
}))

function resetForm() {
  Object.assign(form, {
    id: null,
    title: '超级立减',
    promo_text: '',
    amount: 15,
    button_text: '立即领取',
    link_url: '/coupons',
    is_active: true,
    start_time: '',
    end_time: '',
  })
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getSuperDiscountList({ page: pagination.page, page_size: pagination.pageSize })
    tableData.value = res.data.results || []
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

function openEdit(row) {
  Object.assign(form, {
    id: row.id,
    title: row.title,
    promo_text: row.promo_text,
    amount: Number(row.amount),
    button_text: row.button_text,
    link_url: row.link_url || '',
    is_active: row.is_active,
    start_time: row.start_time || '',
    end_time: row.end_time || '',
  })
  dialogVisible.value = true
}

async function submitForm() {
  await formRef.value?.validate()
  const payload = {
    title: form.title,
    promo_text: form.promo_text,
    amount: form.amount,
    button_text: form.button_text,
    link_url: form.link_url || '',
    is_active: form.is_active,
    start_time: form.start_time || null,
    end_time: form.end_time || null,
  }
  if (form.id) {
    await updateSuperDiscount(form.id, payload)
    ElMessage.success(t('common.updateSuccess'))
  } else {
    await createSuperDiscount(payload)
    ElMessage.success(t('common.createSuccess'))
  }
  dialogVisible.value = false
  fetchList()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(t('superDiscount.deleteConfirm'), t('common.tip'), { type: 'warning' })
  await deleteSuperDiscount(row.id)
  ElMessage.success(t('common.deleteSuccess'))
  fetchList()
}

onMounted(fetchList)
</script>

<template>
  <div class="page-card">
    <div class="page-header">
      <h2>{{ t('superDiscount.listTitle') }}</h2>
      <el-button type="primary" :icon="Plus" @click="openCreate">{{ t('superDiscount.create') }}</el-button>
    </div>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="title" :label="t('superDiscount.title')" min-width="120" />
      <el-table-column prop="promo_text" :label="t('superDiscount.promoText')" min-width="160" show-overflow-tooltip />
      <el-table-column prop="amount" :label="t('superDiscount.amount')" width="100">
        <template #default="{ row }">¥{{ row.amount }}</template>
      </el-table-column>
      <el-table-column prop="button_text" :label="t('superDiscount.buttonText')" width="120" />
      <el-table-column prop="link_url" :label="t('superDiscount.linkUrl')" min-width="140" show-overflow-tooltip />
      <el-table-column prop="is_active" :label="t('common.status')" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">
            {{ row.is_active ? t('common.enabled') : t('common.disabled') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="start_time" :label="t('superDiscount.startTime')" width="170" />
      <el-table-column prop="end_time" :label="t('superDiscount.endTime')" width="170" />
      <el-table-column :label="t('common.action')" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">{{ t('common.edit') }}</el-button>
          <el-button link type="danger" @click="handleDelete(row)">{{ t('common.delete') }}</el-button>
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
        @size-change="fetchList"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item :label="t('superDiscount.title')" prop="title">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item :label="t('superDiscount.promoText')" prop="promo_text">
          <el-input v-model="form.promo_text" maxlength="128" show-word-limit />
        </el-form-item>
        <el-form-item :label="t('superDiscount.amount')" prop="amount">
          <el-input-number v-model="form.amount" :min="0.01" :precision="2" :step="1" />
        </el-form-item>
        <el-form-item :label="t('superDiscount.buttonText')" prop="button_text">
          <el-input v-model="form.button_text" maxlength="32" />
        </el-form-item>
        <el-form-item :label="t('superDiscount.linkUrl')">
          <el-input v-model="form.link_url" placeholder="/coupons" />
        </el-form-item>
        <el-form-item :label="t('common.status')">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        <el-form-item :label="t('superDiscount.startTime')">
          <el-date-picker
            v-model="form.start_time"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('superDiscount.endTime')">
          <el-date-picker
            v-model="form.end_time"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitForm">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
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
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
  font-size: 18px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
