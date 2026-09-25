<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  batchSortCategories,
  createCategory,
  deleteCategory,
  getCategoryFlat,
  getCategoryTree,
  updateCategory,
} from '@/api/product'
import { useCategoryRoles } from '@/composables/useCategoryRoles'
import { ACTION_COLUMN } from '@/config/table'

const { t } = useI18n()
const { canManageCategory } = useCategoryRoles()

const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const treeData = ref([])
const flatOptions = ref([])
const activeRootIndex = ref(0)

const form = reactive({
  id: null,
  name: '',
  parent: null,
  parentPath: [],
  sort_order: 0,
  is_active: true,
})

const rootCategories = computed(() =>
  [...treeData.value].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0)),
)

const activeRoot = computed(() => rootCategories.value[activeRootIndex.value] || null)

const currentTableData = computed(() => {
  if (!activeRoot.value) return []
  return [activeRoot.value]
})

const dialogTitle = computed(() => {
  if (form.id) return t('product.editCategory')
  if (form.parentPath.length) return t('product.createSubCategory')
  return t('product.createCategory')
})

const parentCascaderOptions = computed(() => buildCascaderOptions(flatOptions.value, form.id))

const rules = computed(() => ({
  name: [{ required: true, message: t('product.categoryNameRequired'), trigger: 'blur' }],
}))

function buildCascaderOptions(list, excludeId) {
  if (!list.length) return []
  const excludeIds = new Set()
  if (excludeId) {
    excludeIds.add(excludeId)
    collectDescendantIds(list, excludeId, excludeIds)
  }

  const nodes = list
    .filter((item) => !excludeIds.has(item.id))
    .map((item) => ({
      value: item.id,
      label: item.full_path || item.name,
      parent: item.parent,
    }))

  const map = new Map()
  nodes.forEach((node) => map.set(node.value, { ...node, children: [] }))
  const roots = []
  map.forEach((node) => {
    if (node.parent && map.has(node.parent)) {
      map.get(node.parent).children.push(node)
    } else if (!node.parent) {
      roots.push(node)
    }
  })

  const trim = (items) => items.map(({ value, label, children }) => ({
    value,
    label,
    children: children.length ? trim(children) : undefined,
  }))

  return trim(roots)
}

function collectDescendantIds(list, rootId, bucket) {
  list.forEach((item) => {
    if (item.parent === rootId) {
      bucket.add(item.id)
      collectDescendantIds(list, item.id, bucket)
    }
  })
}

function findPathByParentId(list, parentId) {
  if (!parentId) return []
  const target = list.find((item) => item.id === parentId)
  if (!target) return []
  const parentPath = target.parent ? findPathByParentId(list, target.parent) : []
  return [...parentPath, parentId]
}

async function fetchTree() {
  loading.value = true
  try {
    const [treeRes, flatRes] = await Promise.all([
      getCategoryTree(),
      getCategoryFlat(),
    ])
    treeData.value = treeRes.data || []
    flatOptions.value = flatRes.data || []
    if (activeRootIndex.value >= rootCategories.value.length) {
      activeRootIndex.value = 0
    }
  } finally {
    loading.value = false
  }
}

function selectRoot(index) {
  activeRootIndex.value = index
}

function resetForm() {
  form.id = null
  form.name = ''
  form.parent = null
  form.parentPath = []
  form.sort_order = 0
  form.is_active = true
}

function handleCreate(parentRow = null) {
  resetForm()
  if (parentRow) {
    form.parent = parentRow.id
    form.parentPath = findPathByParentId(flatOptions.value, parentRow.id)
  } else if (activeRoot.value) {
    form.parent = activeRoot.value.id
    form.parentPath = [activeRoot.value.id]
  }
  dialogVisible.value = true
}

function handleEdit(row) {
  Object.assign(form, {
    id: row.id,
    name: row.name,
    parent: row.parent,
    parentPath: findPathByParentId(flatOptions.value, row.parent),
    sort_order: row.sort_order,
    is_active: row.is_active,
  })
  dialogVisible.value = true
}

function onParentChange(value) {
  form.parentPath = value || []
  form.parent = value?.length ? value[value.length - 1] : null
}

async function handleSubmit() {
  await formRef.value.validate()
  const payload = {
    name: form.name,
    parent: form.parent,
    sort_order: form.sort_order,
    is_active: form.is_active,
  }
  if (form.id) {
    await updateCategory(form.id, payload)
    ElMessage.success(t('common.updateSuccess'))
  } else {
    await createCategory(payload)
    ElMessage.success(t('common.createSuccess'))
  }
  dialogVisible.value = false
  fetchTree()
}

async function handleDelete(row) {
  try {
    await deleteCategory(row.id)
    ElMessage.success(t('common.deleteSuccess'))
    fetchTree()
    return
  } catch (error) {
    const message = error?.message || error?.response?.data?.message || ''
    const hasChildren = message.includes('子分类')
    const hasProducts = message.includes('商品')
    if (!hasChildren && !hasProducts) {
      ElMessage.error(message || t('common.loadFailed'))
      return
    }

    if (hasProducts) {
      ElMessage.warning(message)
      return
    }

    await ElMessageBox.confirm(
      message,
      t('common.tip'),
      {
        type: 'warning',
        confirmButtonText: t('product.deleteCategoryCascade'),
        cancelButtonText: t('common.cancel'),
      },
    )
    await deleteCategory(row.id, { cascade: 1 })
    ElMessage.success(t('common.deleteSuccess'))
    fetchTree()
  }
}

async function handleSortChange(row) {
  if (!canManageCategory.value) return
  try {
    await batchSortCategories([{ id: row.id, sort_order: row.sort_order }])
    ElMessage.success(t('common.updateSuccess'))
    fetchTree()
  } catch {
    fetchTree()
  }
}

watch(rootCategories, (list) => {
  if (activeRootIndex.value >= list.length) {
    activeRootIndex.value = 0
  }
})

onMounted(fetchTree)
</script>

<template>
  <div v-loading="loading" class="category-page">
    <aside class="category-sidebar">
      <div
        v-for="(item, index) in rootCategories"
        :key="item.id"
        class="sidebar-item"
        :class="{ active: activeRootIndex === index }"
        @click="selectRoot(index)"
      >
        {{ item.name }}
      </div>
      <el-empty v-if="!loading && !rootCategories.length" :description="t('product.categoryNameRequired')" />
    </aside>

    <main class="category-main">
      <div class="main-header">
        <div class="main-title">
          <span v-if="activeRoot">{{ activeRoot.full_path || activeRoot.name }}</span>
          <span v-else>{{ t('product.categoryTitle') }}</span>
        </div>
        <el-button v-if="canManageCategory && activeRoot" type="primary" @click="handleCreate()">
          {{ t('product.createCategory') }}
        </el-button>
      </div>

      <el-table
        v-if="activeRoot"
        :data="currentTableData"
        row-key="id"
        border
        stripe
        default-expand-all
        :tree-props="{ children: 'children' }"
      >
        <el-table-column prop="name" :label="t('product.categoryName')" min-width="180" />
        <el-table-column prop="level" :label="t('product.categoryLevel')" width="80" align="center" />
        <el-table-column prop="parent_name" :label="t('product.parentCategory')" width="140">
          <template #default="{ row }">
            {{ row.parent_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" :label="t('product.sortOrder')" width="110" align="center">
          <template #default="{ row }">
            <el-input-number
              v-if="canManageCategory"
              v-model="row.sort_order"
              :min="0"
              size="small"
              controls-position="right"
              @change="handleSortChange(row)"
            />
            <span v-else>{{ row.sort_order }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('common.status')" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? t('common.enabled') : t('common.disabled') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          v-if="canManageCategory"
          :label="t('common.actions')"
          :min-width="ACTION_COLUMN.standard"
          class-name="col-actions"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">{{ t('common.edit') }}</el-button>
            <el-button link type="primary" @click="handleCreate(row)">{{ t('product.addSubCategory') }}</el-button>
            <el-button link type="danger" @click="handleDelete(row)">{{ t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-else-if="!loading" :description="t('product.categoryTitle')" />
    </main>
  </div>

  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="480px" destroy-on-close>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="96px">
      <el-form-item :label="t('product.categoryName')" prop="name">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item :label="t('product.parentCategory')">
        <el-cascader
          v-model="form.parentPath"
          :options="parentCascaderOptions"
          :props="{ checkStrictly: true, emitPath: true }"
          clearable
          filterable
          :placeholder="t('product.parentCategoryPlaceholder')"
          style="width: 100%"
          @change="onParentChange"
        />
      </el-form-item>
      <el-form-item :label="t('product.sortOrder')">
        <el-input-number v-model="form.sort_order" :min="0" />
      </el-form-item>
      <el-form-item :label="t('common.enabled')">
        <el-switch v-model="form.is_active" />
      </el-form-item>
      <p class="form-tip">{{ t('product.categoryPathAutoHint') }}</p>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" @click="handleSubmit">{{ t('common.confirm') }}</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.category-page {
  display: flex;
  min-height: calc(100vh - 120px);
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}

.category-sidebar {
  width: 120px;
  flex-shrink: 0;
  overflow-y: auto;
  background: #f7f8fa;
  border-right: 1px solid #ebeef5;
}

.sidebar-item {
  padding: 14px 10px;
  font-size: 13px;
  line-height: 1.35;
  color: #606266;
  text-align: center;
  word-break: break-all;
  cursor: pointer;
  border-bottom: 1px solid #eef0f3;
  transition: background 0.2s, color 0.2s;
}

.sidebar-item:hover {
  background: #eef5ff;
  color: #409eff;
}

.sidebar-item.active {
  background: #409eff;
  color: #fff;
}

.category-main {
  flex: 1;
  min-width: 0;
  padding: 16px;
}

.main-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.main-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.form-tip {
  margin: 0;
  padding-left: 96px;
  font-size: 12px;
  color: #909399;
}
</style>
