<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Picture } from '@element-plus/icons-vue'
import { createBrand, deleteBrand, getBrandList, updateBrand } from '@/api/product'
import { ACTION_COLUMN } from '@/config/table'
import { uploadImage } from '@/api/upload'
import { resolveImageUrl } from '@/utils/media'

const { t } = useI18n()

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/jpg']
const MAX_SIZE = 2 * 1024 * 1024

const loading = ref(false)
const uploading = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const tableData = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const form = reactive({
  id: null,
  name: '',
  logo: '',
  logo_url: '',
  is_active: true,
})

const dialogTitle = computed(() => (form.id ? t('product.editBrand') : t('product.createBrand')))

const logoPreviewUrl = computed(() => resolveImageUrl(form.logo || form.logo_url))

const rules = computed(() => ({
  name: [{ required: true, message: t('product.brandNameRequired'), trigger: 'blur' }],
}))

function beforeUpload(file) {
  if (!ALLOWED_TYPES.includes(file.type)) {
    ElMessage.error(t('product.brandLogoTypeError'))
    return false
  }
  if (file.size > MAX_SIZE) {
    ElMessage.error(t('product.brandLogoSizeError'))
    return false
  }
  return true
}

async function handleUpload(options) {
  if (!beforeUpload(options.file)) {
    return
  }
  uploading.value = true
  try {
    const res = await uploadImage(options.file, 'brands')
    form.logo = res.data.url
    form.logo_url = res.data.url
    ElMessage.success(t('product.uploadSuccess'))
  } catch {
    ElMessage.error(t('product.uploadFailed'))
  } finally {
    uploading.value = false
  }
}

function handleRemoveLogo() {
  form.logo = ''
  form.logo_url = ''
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getBrandList({
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    tableData.value = res.data.results || []
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.id = null
  form.name = ''
  form.logo = ''
  form.logo_url = ''
  form.is_active = true
}

function handleCreate() {
  resetForm()
  dialogVisible.value = true
}

function handleEdit(row) {
  Object.assign(form, {
    id: row.id,
    name: row.name,
    logo: row.logo || '',
    logo_url: row.logo_url || '',
    is_active: row.is_active,
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  await formRef.value.validate()
  const payload = {
    name: form.name,
    logo: form.logo,
    logo_url: form.logo_url || null,
    is_active: form.is_active,
  }
  if (form.id) {
    await updateBrand(form.id, payload)
    ElMessage.success(t('common.updateSuccess'))
  } else {
    await createBrand(payload)
    ElMessage.success(t('common.createSuccess'))
  }
  dialogVisible.value = false
  fetchList()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(t('product.deleteBrandConfirm', { name: row.name }), t('common.tip'), {
    type: 'warning',
  })
  await deleteBrand(row.id)
  ElMessage.success(t('common.deleteSuccess'))
  fetchList()
}

onMounted(fetchList)
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>{{ t('product.brandTitle') }}</span>
        <el-button type="primary" @click="handleCreate">{{ t('product.createBrand') }}</el-button>
      </div>
    </template>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column :label="t('product.brandLogo')" width="100" align="center">
        <template #default="{ row }">
          <el-image
            v-if="row.logo_display"
            :src="resolveImageUrl(row.logo_display)"
            class="brand-logo-thumb"
            fit="contain"
          />
          <div v-else class="brand-logo-placeholder">
            <el-icon><Picture /></el-icon>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="name" :label="t('product.brandName')" min-width="160" />
      <el-table-column :label="t('common.status')" width="90">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? t('common.enabled') : t('common.disabled') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="t('common.actions')"
        :min-width="ACTION_COLUMN.basic"
        class-name="col-actions"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button link type="primary" @click="handleEdit(row)">{{ t('common.edit') }}</el-button>
          <el-button link type="danger" @click="handleDelete(row)">{{ t('common.delete') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :total="pagination.total"
      layout="total, prev, pager, next"
      class="pagination"
      @current-change="fetchList"
    />
  </el-card>

  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="480px" destroy-on-close>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
      <el-form-item :label="t('product.brandName')" prop="name">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item :label="t('product.brandLogo')">
        <div class="upload-wrap">
          <el-upload
            class="logo-uploader"
            :show-file-list="false"
            accept=".jpg,.jpeg,.png"
            :http-request="handleUpload"
            :disabled="uploading"
          >
            <el-image
              v-if="logoPreviewUrl"
              :src="logoPreviewUrl"
              class="upload-preview"
              fit="contain"
            />
            <el-icon v-else class="upload-icon">
              <Plus />
            </el-icon>
          </el-upload>
          <div class="upload-actions">
            <el-button
              v-if="form.logo || form.logo_url"
              link
              type="danger"
              @click="handleRemoveLogo"
            >
              {{ t('product.removeImage') }}
            </el-button>
            <span class="upload-tip">{{ t('product.brandLogoUploadTip') }}</span>
          </div>
        </div>
      </el-form-item>
      <el-form-item :label="t('product.logoUrl')">
        <el-input
          v-model="form.logo_url"
          :placeholder="t('product.brandLogoUrlHint')"
          clearable
        />
      </el-form-item>
      <el-form-item :label="t('common.enabled')">
        <el-switch v-model="form.is_active" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" :loading="uploading" @click="handleSubmit">{{ t('common.confirm') }}</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

.brand-logo-thumb {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  border: 1px solid var(--el-border-color-lighter);
}

.brand-logo-placeholder {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 4px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-placeholder);
  font-size: 20px;
}

.upload-wrap {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.logo-uploader :deep(.el-upload) {
  width: 120px;
  height: 120px;
  border: 1px dashed var(--el-border-color);
  border-radius: 8px;
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.2s;
}

.logo-uploader :deep(.el-upload:hover) {
  border-color: var(--el-color-primary);
}

.upload-preview {
  width: 120px;
  height: 120px;
}

.upload-icon {
  width: 120px;
  height: 120px;
  font-size: 28px;
  color: var(--el-text-color-secondary);
}

.upload-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 4px;
}

.upload-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
  max-width: 220px;
}
</style>
