<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  createProduct,
  getBrandList,
  getCategoryList,
  getProductList,
  toggleProduct,
  updateProduct,
} from '@/api/products'
import { batchUpdateProductTags, getProductTagConfigs, getSellerTags } from '@/api/tags'
import { uploadImage } from '@/api/upload'
import { resolveImageUrl } from '@/utils/media'
import { useAuthStore } from '@/stores/auth'
import ProductMallPreview from '@/components/products/ProductMallPreview.vue'

const { t } = useI18n()
const authStore = useAuthStore()
const loading = ref(false)
const uploading = ref(false)
const dialogVisible = ref(false)
const previewVisible = ref(false)
const previewProduct = ref(null)
const submitting = ref(false)
const formRef = ref(null)
const tableData = ref([])
const categoryOptions = ref([])
const brandOptions = ref([])
const allTags = ref([])
const selectedTagIds = ref([])
const initialTagIds = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ keyword: '', status: '' })

const form = reactive({
  id: null,
  name: '',
  category: null,
  brand: null,
  price: 0,
  stock: 0,
  description: '',
  image: '',
  status: 'draft',
})

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
const MAX_SIZE = 2 * 1024 * 1024
const MAX_PRODUCT_TAGS = 3

const statusMap = computed(() => ({
  draft: { label: t('seller.draft'), type: 'info' },
  on_sale: { label: t('seller.onSale'), type: 'success' },
  off_sale: { label: t('seller.offSale'), type: 'warning' },
}))

const rules = computed(() => ({
  name: [{ required: true, message: t('seller.nameRequired'), trigger: 'blur' }],
  category: [{ required: true, message: t('seller.categoryRequired'), trigger: 'change' }],
  brand: [{ required: true, message: t('seller.brandRequired'), trigger: 'change' }],
  price: [{ required: true, message: t('seller.priceRequired'), trigger: 'blur' }],
}))

const dialogTitle = computed(() => (form.id ? t('seller.editProduct') : t('seller.createProduct')))

const editableTags = computed(() =>
  allTags.value.filter((tag) => {
    if (!tag.can_product_use) return false
    if (tag.category_type === 'platform' && tag.requires_approval) {
      return tag.participating
    }
    return true
  }),
)

const imagePreviewUrl = computed(() => resolveImageUrl(form.image))

const shopName = computed(() => authStore.tenant?.name || '')

function openPreview(row) {
  loadPreviewProduct(row)
}

async function loadPreviewProduct(row) {
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
    })
    tableData.value = res.data?.results || []
    pagination.total = res.data?.count || 0
  } finally {
    loading.value = false
  }
}

async function loadOptions() {
  try {
    const [catRes, brandRes, tagRes] = await Promise.all([
      getCategoryList(),
      getBrandList(),
      getSellerTags(),
    ])
    categoryOptions.value = catRes.data || []
    brandOptions.value = brandRes.data || []
    allTags.value = tagRes.data || []
  } catch (error) {
    allTags.value = []
    ElMessage.error(error?.message || t('seller.productTagsLoadFailed'))
  }
}

async function loadProductTags(productId) {
  const res = await getProductTagConfigs({ product_id: productId, page_size: 100 })
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
    ElMessage.warning(t('seller.productTagsMax', { max: MAX_PRODUCT_TAGS }))
  }
})

function handleSearch() {
  pagination.page = 1
  fetchList()
}

function handlePageChange(page) {
  pagination.page = page
  fetchList()
}

function resetForm() {
  form.id = null
  form.name = ''
  form.category = categoryOptions.value[0]?.id || null
  form.brand = brandOptions.value[0]?.id || null
  form.price = 0
  form.stock = 0
  form.description = ''
  form.image = ''
  form.status = 'draft'
  selectedTagIds.value = []
  initialTagIds.value = []
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

async function openEdit(row) {
  form.id = row.id
  form.name = row.name
  form.category = row.category
  form.brand = row.brand
  form.price = Number(row.price)
  form.stock = Number(row.stock)
  form.description = row.description || ''
  form.image = row.image || ''
  form.status = row.status
  await loadProductTags(row.id)
  dialogVisible.value = true
}

async function handleSubmit() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    const payload = {
      name: form.name,
      category: form.category,
      brand: form.brand,
      price: form.price,
      stock: form.stock,
      description: form.description,
      image: form.image,
      status: form.status,
    }
    let savedId = form.id
    if (form.id) {
      await updateProduct(form.id, payload)
      ElMessage.success(t('seller.productUpdated'))
    } else {
      const res = await createProduct(payload)
      savedId = res.data?.id || savedId
      ElMessage.success(t('seller.productCreated'))
    }
    if (savedId) {
      try {
        await syncProductTags(savedId)
      } catch (error) {
        ElMessage.error(error?.message || t('seller.productTagsSaveFailed'))
      }
    }
    dialogVisible.value = false
    await fetchList()
  } finally {
    submitting.value = false
  }
}

async function handleToggle(row) {
  const nextStatus = row.status === 'on_sale' ? 'off_sale' : 'on_sale'
  await toggleProduct(row.id, nextStatus)
  ElMessage.success(t('seller.statusUpdated'))
  await fetchList()
}

async function handleUpload(options) {
  const file = options.file
  if (!ALLOWED_TYPES.includes(file.type)) {
    ElMessage.error('Invalid image type')
    return
  }
  if (file.size > MAX_SIZE) {
    ElMessage.error('Image too large (max 2MB)')
    return
  }
  uploading.value = true
  try {
    const res = await uploadImage(file)
    form.image = res.data?.url || res.data?.path || ''
  } finally {
    uploading.value = false
  }
}

onMounted(async () => {
  await loadOptions()
  fetchList()
})
</script>

<template>
  <el-card shadow="never" class="product-list-card">
    <template #header>
      <div class="card-header">
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>
          {{ t('seller.addProduct') }}
        </el-button>
      </div>
    </template>

    <el-form inline @submit.prevent="handleSearch">
      <el-form-item :label="t('seller.keyword')">
        <el-input v-model="filters.keyword" :placeholder="t('seller.productKeywordPlaceholder')" clearable @keyup.enter="handleSearch" />
      </el-form-item>
      <el-form-item :label="t('seller.status')">
        <el-select v-model="filters.status" clearable :placeholder="t('seller.all')" style="width: 140px">
          <el-option :label="t('seller.onSale')" value="on_sale" />
          <el-option :label="t('seller.offSale')" value="off_sale" />
          <el-option :label="t('seller.draft')" value="draft" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">{{ t('seller.query') }}</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="tableData" stripe>
      <el-table-column :label="t('seller.productImage')" width="80">
        <template #default="{ row }">
          <el-image
            v-if="row.image"
            :src="resolveImageUrl(row.image)"
            fit="cover"
            style="width: 48px; height: 48px; border-radius: 4px"
          />
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="name" :label="t('seller.productName')" min-width="160" show-overflow-tooltip />
      <el-table-column prop="price" :label="t('seller.price')" width="100" />
      <el-table-column prop="stock" :label="t('seller.stock')" width="90">
        <template #default="{ row }">
          <span>{{ row.stock }}</span>
          <el-tag v-if="row.stock <= 10" type="danger" size="small" class="stock-tag">{{ t('seller.stockWarning') }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('seller.status')" width="100">
        <template #default="{ row }">
          <el-tag :type="statusMap[row.status]?.type || 'info'" size="small">
            {{ statusMap[row.status]?.label || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" :label="t('seller.createTime')" width="170">
        <template #default="{ row }">
          {{ row.created_at ? String(row.created_at).replace('T', ' ').slice(0, 19) : '-' }}
        </template>
      </el-table-column>
      <el-table-column :label="t('seller.actions')" width="240" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="openEdit(row)">{{ t('common.edit') }}</el-button>
          <el-button type="info" link @click="openPreview(row)">{{ t('seller.previewMall') }}</el-button>
          <el-button
            v-if="row.status === 'on_sale'"
            type="warning"
            link
            @click="handleToggle(row)"
          >
            {{ t('seller.toggleOffSale') }}
          </el-button>
          <el-button v-else type="success" link @click="handleToggle(row)">
            {{ t('seller.toggleOnSale') }}
          </el-button>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="560px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item :label="t('seller.productName')" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item :label="t('seller.category')" prop="category">
          <el-select v-model="form.category" filterable style="width: 100%">
            <el-option v-for="item in categoryOptions" :key="item.id" :label="item.full_path || item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('seller.brand')" prop="brand">
          <el-select v-model="form.brand" filterable style="width: 100%">
            <el-option v-for="item in brandOptions" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('seller.price')" prop="price">
          <el-input-number v-model="form.price" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('seller.stock')">
          <el-input-number v-model="form.stock" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('seller.description')">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item :label="t('seller.productImage')">
          <div class="image-field">
            <el-upload :show-file-list="false" :http-request="handleUpload" accept="image/*">
              <el-button :loading="uploading">{{ t('seller.uploadImage') }}</el-button>
            </el-upload>
            <el-image v-if="imagePreviewUrl" :src="imagePreviewUrl" fit="cover" class="preview-image" />
          </div>
        </el-form-item>
        <el-form-item :label="t('seller.status')">
          <el-select v-model="form.status" style="width: 100%">
            <el-option :label="t('seller.draft')" value="draft" />
            <el-option :label="t('seller.onSale')" value="on_sale" />
            <el-option :label="t('seller.offSale')" value="off_sale" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('seller.productTags')">
          <p v-if="editableTags.length" class="tag-tip">{{ t('seller.productTagsTip') }}</p>
          <p v-else class="tag-tip tag-tip--warn">{{ t('seller.productTagsEmpty') }}</p>
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
        <el-button type="primary" :loading="submitting" @click="handleSubmit">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="previewVisible"
      :title="t('seller.mallPreviewTitle')"
      width="420px"
      destroy-on-close
    >
      <ProductMallPreview
        v-if="previewProduct"
        :product="previewProduct"
        :shop-name="shopName"
        :image-url="resolveImageUrl(previewProduct.image)"
      />
    </el-dialog>
  </el-card>
</template>

<style scoped>
.card-header {
  display: flex;
  justify-content: flex-end;
}

.product-list-card :deep(.el-card__header) {
  padding: 12px 20px;
}

.pager {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.stock-tag {
  margin-left: 6px;
}

.tag-tip {
  margin: 0 0 8px;
  color: #909399;
  font-size: 12px;
  line-height: 1.4;
}

.tag-chip {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.image-field {
  display: flex;
  align-items: center;
  gap: 12px;
}

.preview-image {
  width: 72px;
  height: 72px;
  border-radius: 6px;
}
</style>
