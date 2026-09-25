<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { translateInventoryType } from '@/i18n'
import {
  createProduct,
  deleteProduct,
  getBrandList,
  getCategoryList,
  getInventoryLogs,
  getProductList,
  offSaleProduct,
  onSaleProduct,
  updateProduct,
} from '@/api/product'
import { uploadImage } from '@/api/upload'
import { batchUpdateProductTags, getProductTagConfigs, getTags } from '@/api/tags'
import { resolveImageUrl } from '@/utils/media'
import ProductMallPreview from '@/components/products/ProductMallPreview.vue'

const { t } = useI18n()
const authStore = useAuthStore()

const loading = ref(false)
const uploading = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const tableData = ref([])
const categoryOptions = ref([])
const brandOptions = ref([])
const allTags = ref([])
const selectedTagIds = ref([])
const initialTagIds = ref([])
const previewVisible = ref(false)
const previewProduct = ref(null)
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ keyword: '', status: '', category: '' })

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
const MAX_SIZE = 2 * 1024 * 1024
const MAX_PRODUCT_TAGS = 3

const form = reactive({
  id: null,
  name: '',
  category: null,
  brand: null,
  price: 0,
  stock: 0,
  description: '',
  image: '',
  gallery: [],
  status: 'draft',
})

const editingTenant = ref(null)

const rules = computed(() => ({
  name: [{ required: true, message: t('product.nameRequired'), trigger: 'blur' }],
  category: [{ required: true, message: t('product.categoryRequired'), trigger: 'change' }],
  brand: [{ required: true, message: t('product.brandRequired'), trigger: 'change' }],
  price: [{ required: true, message: t('product.priceRequired'), trigger: 'blur' }],
}))

const STATUS_MAP = computed(() => ({
  draft: { label: t('product.statusDraft'), type: 'info' },
  on_sale: { label: t('product.statusOnSale'), type: 'success' },
  off_sale: { label: t('product.statusOffSale'), type: 'warning' },
}))

const dialogTitle = computed(() => (form.id ? t('product.edit') : t('product.create')))

const logDialogTitle = computed(() => t('product.inventoryLogTitle', { name: logProductName.value }))

const CHANGE_TYPE_TAG = {
  stock_in: 'success',
  gain: 'success',
  return_in: 'success',
  stock_out: 'danger',
  loss: 'danger',
  order_deduct: 'danger',
  transfer: 'primary',
}

const logLoading = ref(false)
const logDialogVisible = ref(false)
const logProductName = ref('')
const logTableData = ref([])
const logPagination = reactive({ page: 1, pageSize: 10, total: 0 })
const currentLogProductId = ref(null)

const canViewInventoryLog = computed(() => {
  const user = authStore.user
  if (!user) {
    return false
  }
  if (user.is_superuser) {
    return true
  }
  const roleCodes = user.roles?.map((item) => item.code) || []
  return roleCodes.some((code) => ['super_admin', 'ops_manager', 'warehouse_manager'].includes(code))
})

const imagePreviewUrl = computed(() => resolveImageUrl(form.image))

const editableTags = computed(() => allTags.value.filter((tag) => tag.can_product_use && tag.is_active))

const previewShopName = computed(() => {
  if (!previewProduct.value) return ''
  return previewProduct.value.tenant_name || t('product.platformOwned')
})

function beforeUpload(file) {
  if (!ALLOWED_TYPES.includes(file.type)) {
    ElMessage.error(t('product.imageTypeError'))
    return false
  }
  if (file.size > MAX_SIZE) {
    ElMessage.error(t('product.imageSizeError'))
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
    const res = await uploadImage(options.file)
    form.image = res.data.url
    ElMessage.success(t('product.uploadSuccess'))
  } catch {
    ElMessage.error(t('product.uploadFailed'))
  } finally {
    uploading.value = false
  }
}

function handleRemoveImage() {
  form.image = ''
}

async function fetchOptions() {
  try {
    const [catRes, brandRes, tagRes] = await Promise.all([
      getCategoryList({ page_size: 100 }),
      getBrandList({ page_size: 100 }),
      getTags({ page_size: 100, is_active: true }),
    ])
    categoryOptions.value = catRes.data.results || catRes.data || []
    brandOptions.value = brandRes.data.results || brandRes.data || []
    allTags.value = tagRes.data.results || tagRes.data || []
    if (!allTags.value.length) {
      ElMessage.warning(t('tags.emptyTagLibrary'))
    }
  } catch (error) {
    allTags.value = []
    ElMessage.error(error?.message || t('tags.loadFailed'))
  }
}

async function loadProductTags(productId) {
  const res = await getProductTagConfigs({ product_id: productId, page_size: 50 })
  const rows = res.data?.results || res.data || []
  const activeIds = rows.filter((row) => row.is_active).map((row) => row.tag)
  selectedTagIds.value = [...activeIds]
  initialTagIds.value = [...activeIds]
}

async function syncProductTags(productId) {
  await batchUpdateProductTags(productId, [...selectedTagIds.value])
  initialTagIds.value = [...selectedTagIds.value]
}

watch(selectedTagIds, (ids) => {
  if (ids.length > MAX_PRODUCT_TAGS) {
    selectedTagIds.value = ids.slice(0, MAX_PRODUCT_TAGS)
    ElMessage.warning(t('tags.productTagsMax', { max: MAX_PRODUCT_TAGS }))
  }
})

async function openPreview(row) {
  const tagRes = await getProductTagConfigs({ product_id: row.id, page_size: 50 })
  const configs = (tagRes.data?.results || tagRes.data || []).filter((item) => item.is_active)
  const tagMap = Object.fromEntries(allTags.value.map((tag) => [tag.id, tag]))
  const promo_tags = configs.map((cfg) => {
    const tag = tagMap[cfg.tag] || {}
    return {
      code: cfg.tag_code || tag.code,
      name: cfg.tag_name || tag.name,
      color: tag.color || '#FF6B35',
      text_color: tag.text_color || '#FFFFFF',
      icon: tag.icon || '',
    }
  })
  previewProduct.value = { ...row, promo_tags }
  previewVisible.value = true
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getProductList({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
      category: filters.category || undefined,
      all_tenants: '1',
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
  form.category = null
  form.brand = null
  form.price = 0
  form.stock = 0
  form.description = ''
  form.image = ''
  form.gallery = []
  form.status = 'draft'
  selectedTagIds.value = []
  initialTagIds.value = []
}

function handleCreate() {
  resetForm()
  editingTenant.value = null
  dialogVisible.value = true
}

function handleEdit(row) {
  Object.assign(form, {
    id: row.id,
    name: row.name,
    category: row.category,
    brand: row.brand,
    price: Number(row.price),
    stock: row.stock,
    description: row.description,
    image: row.image || '',
    gallery: row.gallery || [],
    status: row.status,
  })
  editingTenant.value = row.tenant_name
    ? { name: row.tenant_name, code: row.tenant_code, logo: row.tenant_logo }
    : null
  loadProductTags(row.id)
  dialogVisible.value = true
}

async function handleSubmit() {
  await formRef.value.validate()
  const payload = {
    name: form.name,
    category: form.category,
    brand: form.brand,
    price: form.price,
    stock: form.stock,
    description: form.description,
    image: form.image,
    gallery: form.gallery,
    status: form.status,
  }
  try {
    if (form.id) {
      await updateProduct(form.id, payload)
      await syncProductTags(form.id)
      ElMessage.success(t('product.updateSuccess'))
    } else {
      const res = await createProduct(payload)
      const savedId = res.data?.id
      if (savedId) {
        await syncProductTags(savedId)
      }
      ElMessage.success(t('product.createSuccess'))
    }
    dialogVisible.value = false
    fetchList()
  } catch (error) {
    ElMessage.error(error?.message || t('common.requestFailed'))
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(
    t('product.deleteConfirm', { name: row.name }),
    t('common.tip'),
    { type: 'warning' },
  )
  await deleteProduct(row.id)
  ElMessage.success(t('product.deleteSuccess'))
  fetchList()
}

async function handleOnSale(row) {
  await onSaleProduct(row.id)
  ElMessage.success(t('product.onSaleSuccess'))
  fetchList()
}

async function handleOffSale(row) {
  await offSaleProduct(row.id)
  ElMessage.success(t('product.offSaleSuccess'))
  fetchList()
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

function getChangeTypeTag(type) {
  return CHANGE_TYPE_TAG[type] || 'info'
}

async function fetchInventoryLogs() {
  if (!currentLogProductId.value) {
    return
  }
  logLoading.value = true
  try {
    const res = await getInventoryLogs({
      product_id: currentLogProductId.value,
      page: logPagination.page,
      page_size: logPagination.pageSize,
    })
    logTableData.value = res.data.results || []
    logPagination.total = res.data.count || 0
  } finally {
    logLoading.value = false
  }
}

function handleInventoryLog(row) {
  currentLogProductId.value = row.id
  logProductName.value = row.name
  logPagination.page = 1
  logDialogVisible.value = true
  fetchInventoryLogs()
}

onMounted(async () => {
  await fetchOptions()
  await fetchList()
})
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>{{ t('product.listTitle') }}</span>
        <el-button type="primary" :icon="Plus" @click="handleCreate">{{ t('product.create') }}</el-button>
      </div>
    </template>

    <el-form :inline="true" class="filter-form">
      <el-form-item :label="t('common.keyword')">
        <el-input
          v-model="filters.keyword"
          :placeholder="t('product.name')"
          clearable
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item :label="t('common.status')">
        <el-select
          v-model="filters.status"
          :placeholder="t('common.all')"
          clearable
          style="width: 120px"
        >
          <el-option :label="t('product.statusDraft')" value="draft" />
          <el-option :label="t('product.statusOnSale')" value="on_sale" />
          <el-option :label="t('product.statusOffSale')" value="off_sale" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('product.category')">
        <el-select
          v-model="filters.category"
          :placeholder="t('common.all')"
          clearable
          style="width: 140px"
        >
          <el-option v-for="item in categoryOptions" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">{{ t('common.search') }}</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column :label="t('product.image')" width="90" align="center">
        <template #default="{ row }">
          <el-image
            v-if="row.image"
            :key="row.image"
            :src="resolveImageUrl(row.image)"
            class="product-thumb"
            fit="cover"
          />
          <span v-else class="no-image">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="name" :label="t('product.name')" min-width="160" show-overflow-tooltip />
      <el-table-column prop="tenant_name" :label="t('product.tenantName')" width="120" show-overflow-tooltip class-name="col-hide-md">
        <template #default="{ row }">
          {{ row.tenant_name || t('product.platformOwned') }}
        </template>
      </el-table-column>
      <el-table-column prop="category_name" :label="t('product.category')" width="100" class-name="col-hide-md" />
      <el-table-column prop="brand_name" :label="t('product.brand')" width="100" class-name="col-hide-md" />
      <el-table-column prop="price" :label="t('product.price')" width="100" />
      <el-table-column prop="stock" :label="t('product.stock')" width="80" />
      <el-table-column :label="t('common.status')" width="90">
        <template #default="{ row }">
          <el-tag :type="STATUS_MAP[row.status]?.type || 'info'" size="small">
            {{ STATUS_MAP[row.status]?.label || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="t('common.actions')"
        width="300"
        class-name="col-actions"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button link type="primary" @click="handleEdit(row)">{{ t('common.edit') }}</el-button>
          <el-button link type="info" @click="openPreview(row)">{{ t('product.previewMall') }}</el-button>
          <el-button
            v-if="row.status !== 'on_sale'"
            link
            type="success"
            @click="handleOnSale(row)"
          >
            {{ t('product.onSale') }}
          </el-button>
          <el-button v-else link type="warning" @click="handleOffSale(row)">
            {{ t('product.offSale') }}
          </el-button>
          <el-button v-if="canViewInventoryLog" link type="info" @click="handleInventoryLog(row)">
            {{ t('product.inventoryLog') }}
          </el-button>
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

  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px" destroy-on-close>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item v-if="form.id" :label="t('product.tenantName')">
        <span v-if="editingTenant">{{ editingTenant.name }}</span>
        <span v-else>{{ t('product.platformOwned') }}</span>
      </el-form-item>
      <el-form-item :label="t('product.name')" prop="name">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item :label="t('product.category')" prop="category">
        <el-select v-model="form.category" :placeholder="t('product.categoryRequired')" style="width: 100%">
          <el-option v-for="item in categoryOptions" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('product.brand')" prop="brand">
        <el-select v-model="form.brand" :placeholder="t('product.brandRequired')" style="width: 100%">
          <el-option v-for="item in brandOptions" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('product.price')" prop="price">
        <el-input-number v-model="form.price" :min="0" :precision="2" style="width: 100%" />
      </el-form-item>
      <el-form-item :label="t('product.stock')">
        <el-input-number v-model="form.stock" :min="0" style="width: 100%" />
      </el-form-item>
      <el-form-item :label="t('product.mainImage')">
        <div class="upload-wrap">
          <el-upload
            class="image-uploader"
            :show-file-list="false"
            accept=".jpg,.jpeg,.png,.gif,.webp"
            :http-request="handleUpload"
            :disabled="uploading"
          >
            <el-image
              v-if="imagePreviewUrl"
              :src="imagePreviewUrl"
              class="upload-preview"
              fit="cover"
            />
            <el-icon v-else class="upload-icon">
              <Plus />
            </el-icon>
          </el-upload>
          <div class="upload-actions">
            <el-button
              v-if="form.image"
              link
              type="danger"
              @click="handleRemoveImage"
            >
              {{ t('product.removeImage') }}
            </el-button>
            <span class="upload-tip">{{ t('product.uploadTip') }}</span>
          </div>
        </div>
      </el-form-item>
      <el-form-item :label="t('product.description')">
        <el-input v-model="form.description" type="textarea" :rows="3" />
      </el-form-item>
      <el-form-item :label="t('product.promoTags')">
        <p v-if="editableTags.length" class="tag-tip">{{ t('product.promoTagsTip') }}</p>
        <p v-else class="tag-tip tag-tip--warn">{{ t('tags.emptyTagLibrary') }}</p>
        <el-checkbox-group v-if="editableTags.length" v-model="selectedTagIds">
          <el-checkbox v-for="tag in editableTags" :key="tag.id" :value="tag.id">
            <span class="tag-chip" :style="{ background: tag.color, color: tag.text_color }">
              {{ tag.icon ? `${tag.icon} ` : '' }}{{ tag.name }}
            </span>
          </el-checkbox>
        </el-checkbox-group>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" @click="handleSubmit">{{ t('common.confirm') }}</el-button>
    </template>
  </el-dialog>

  <el-dialog
    v-model="previewVisible"
    :title="t('product.previewMall')"
    width="420px"
    destroy-on-close
  >
    <ProductMallPreview
      v-if="previewProduct"
      :product="previewProduct"
      :shop-name="previewShopName"
      :image-url="resolveImageUrl(previewProduct.image)"
    />
  </el-dialog>

  <el-dialog
    v-model="logDialogVisible"
    :title="logDialogTitle"
    width="760px"
    destroy-on-close
  >
    <el-table v-loading="logLoading" :data="logTableData" border stripe size="small">
      <el-table-column prop="created_at" :label="t('product.changeTime')" width="170" />
      <el-table-column :label="t('product.changeType')" width="110">
        <template #default="{ row }">
          <el-tag :type="getChangeTypeTag(row.change_type)" size="small">
            {{ translateInventoryType(row.change_type, row.change_type_label) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="before_quantity" :label="t('product.beforeQty')" width="80" align="center" />
      <el-table-column prop="after_quantity" :label="t('product.afterQty')" width="80" align="center" />
      <el-table-column prop="changed_by_name" :label="t('product.operator')" width="100" />
      <el-table-column prop="remark" :label="t('common.remark')" min-width="140" show-overflow-tooltip />
    </el-table>
    <el-pagination
      v-model:current-page="logPagination.page"
      v-model:page-size="logPagination.pageSize"
      :total="logPagination.total"
      layout="total, prev, pager, next"
      class="pagination"
      @current-change="fetchInventoryLogs"
    />
  </el-dialog>
</template>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.filter-form {
  margin-bottom: 16px;
}
.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
.product-thumb {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  vertical-align: middle;
}
.no-image {
  color: var(--el-text-color-placeholder);
}
.upload-wrap {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.image-uploader :deep(.el-upload) {
  border: 1px dashed var(--el-border-color);
  border-radius: 6px;
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.2s;
}
.image-uploader :deep(.el-upload:hover) {
  border-color: var(--el-color-primary);
}
.upload-icon {
  font-size: 28px;
  color: var(--el-text-color-secondary);
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.upload-preview {
  width: 120px;
  height: 120px;
  display: block;
}
.upload-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.upload-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
}

.tag-tip {
  margin: 0 0 8px;
  font-size: 12px;
  color: #909399;
}

.tag-tip--warn {
  color: #e6a23c;
}

.tag-chip {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
</style>
