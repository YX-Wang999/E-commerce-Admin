<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  createAnnouncement,
  deleteAnnouncement,
  getAnnouncementList,
  offlineAnnouncement,
  publishAnnouncement,
  updateAnnouncement,
} from '@/api/announcement'
import { getDepartmentFlatList } from '@/api/department'
import { getRoleList } from '@/api/role'
import { useRoleLabel } from '@/composables/useRoleLabel'
import TableActionMenu from '@/components/TableActionMenu.vue'
import { ACTION_COLUMN } from '@/config/table'

const { t } = useI18n()
const authStore = useAuthStore()
const { roleOptionLabel } = useRoleLabel()

const loading = ref(false)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const formRef = ref(null)
const tableData = ref([])
const roleOptions = ref([])
const departmentOptions = ref([])
const currentRow = ref(null)
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ keyword: '', status: '', priority: '' })

const form = reactive({
  id: null,
  title: '',
  content: '',
  type: 'notice',
  priority: 'normal',
  scope: 'all',
  target_role_ids: [],
  target_department_ids: [],
  is_pinned: false,
  publishNow: false,
  effective_at: '',
  expires_at: '',
})

const roleCodes = computed(() => authStore.user?.roles?.map((item) => item.code) || [])
const isSuper = computed(() => Boolean(authStore.user?.is_superuser))
const canWrite = computed(() => {
  if (isSuper.value) return true
  return roleCodes.value.some((code) => ['super_admin', 'ops_director'].includes(code))
})

const dialogTitle = computed(() =>
  form.id ? t('announcement.edit') : t('announcement.create'),
)

const STATUS_MAP = computed(() => ({
  draft: { label: t('announcement.statusDraft'), type: 'info' },
  published: { label: t('announcement.statusPublished'), type: 'success' },
  offline: { label: t('announcement.statusOffline'), type: 'warning' },
}))

const PRIORITY_MAP = computed(() => ({
  urgent: { label: t('announcement.priorityUrgent'), type: 'danger' },
  important: { label: t('announcement.priorityImportant'), type: 'warning' },
  normal: { label: t('announcement.priorityNormal'), type: 'info' },
}))

const rules = computed(() => ({
  title: [{ required: true, message: t('announcement.titleRequired'), trigger: 'blur' }],
  content: [{ required: true, message: t('announcement.contentRequired'), trigger: 'blur' }],
  type: [{ required: true, message: t('announcement.typeRequired'), trigger: 'change' }],
  effective_at: [{ required: true, message: t('announcement.effectiveRequired'), trigger: 'change' }],
  expires_at: [{ required: true, message: t('announcement.expiresRequired'), trigger: 'change' }],
}))

async function fetchOptions() {
  const [roleRes, deptRes] = await Promise.all([
    getRoleList({ page_size: 100 }),
    getDepartmentFlatList(),
  ])
  roleOptions.value = roleRes.data.results || roleRes.data || []
  departmentOptions.value = deptRes.data || []
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getAnnouncementList({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
      priority: filters.priority || undefined,
    })
    tableData.value = res.data.results || []
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.id = null
  form.title = ''
  form.content = ''
  form.type = 'notice'
  form.priority = 'normal'
  form.scope = 'all'
  form.target_role_ids = []
  form.target_department_ids = []
  form.is_pinned = false
  form.publishNow = false
  form.effective_at = ''
  form.expires_at = ''
}

function handleCreate() {
  resetForm()
  dialogVisible.value = true
}

function handleEdit(row) {
  if (row.status === 'published') {
    ElMessage.warning(t('announcement.offlineBeforeEdit'))
    return
  }
  Object.assign(form, {
    id: row.id,
    title: row.title,
    content: row.content,
    type: row.type || row.announce_type,
    priority: row.priority,
    scope: row.scope,
    target_role_ids: row.target_role_ids || [],
    target_department_ids: row.target_department_ids || [],
    is_pinned: row.is_pinned,
    effective_at: row.effective_at,
    expires_at: row.expires_at,
  })
  dialogVisible.value = true
}

function openDetail(row) {
  currentRow.value = row
  detailVisible.value = true
}

async function handleSubmit() {
  await formRef.value.validate()
  const payload = {
    title: form.title,
    content: form.content,
    type: form.type,
    priority: form.priority,
    scope: form.scope,
    target_role_ids: form.scope === 'role' ? form.target_role_ids : [],
    target_department_ids: form.scope === 'department' ? form.target_department_ids : [],
    is_pinned: form.is_pinned,
    effective_at: form.effective_at,
    expires_at: form.expires_at,
    status: form.publishNow ? 'published' : 'draft',
  }
  if (form.id) {
    await updateAnnouncement(form.id, payload)
    ElMessage.success(t('common.updateSuccess'))
    if (form.publishNow) {
      await publishAnnouncement(form.id)
      ElMessage.success(t('announcement.publishSuccess'))
    }
  } else {
    const res = await createAnnouncement(payload)
    ElMessage.success(form.publishNow ? t('announcement.publishSuccess') : t('common.createSuccess'))
    if (!form.publishNow && res.data?.id) {
      // created as draft only
    }
  }
  dialogVisible.value = false
  fetchList()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(
    t('announcement.deleteConfirm', { title: row.title }),
    t('common.tip'),
    { type: 'warning' },
  )
  await deleteAnnouncement(row.id)
  ElMessage.success(t('common.deleteSuccess'))
  fetchList()
}

async function handlePublish(row) {
  await ElMessageBox.confirm(
    t('announcement.publishConfirm', { title: row.title }),
    t('common.tip'),
    { type: 'warning' },
  )
  await publishAnnouncement(row.id)
  ElMessage.success(t('announcement.publishSuccess'))
  fetchList()
}

async function handleOffline(row) {
  await ElMessageBox.confirm(
    t('announcement.offlineConfirm', { title: row.title }),
    t('common.tip'),
    { type: 'warning' },
  )
  await offlineAnnouncement(row.id)
  ElMessage.success(t('announcement.offlineSuccess'))
  fetchList()
}

function buildActions(row) {
  const actions = [{ label: t('common.detail'), onClick: () => openDetail(row) }]
  if (!canWrite.value) return actions
  if (row.status !== 'published') {
    actions.push({ label: t('common.edit'), type: 'primary', onClick: () => handleEdit(row) })
    actions.push({ label: t('announcement.publish'), type: 'success', onClick: () => handlePublish(row) })
  }
  if (row.status === 'published') {
    actions.push({ label: t('announcement.offline'), type: 'warning', onClick: () => handleOffline(row) })
  }
  if (row.status !== 'published') {
    actions.push({
      label: t('common.delete'),
      type: 'danger',
      danger: true,
      onClick: () => handleDelete(row),
    })
  }
  return actions
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

onMounted(async () => {
  await fetchOptions()
  fetchList()
})
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>{{ t('announcement.listTitle') }}</span>
        <el-button v-if="canWrite" type="primary" @click="handleCreate">
          {{ t('announcement.create') }}
        </el-button>
      </div>
    </template>

    <el-form :inline="true" class="filter-form">
      <el-form-item :label="t('common.keyword')">
        <el-input
          v-model="filters.keyword"
          :placeholder="t('announcement.keywordPlaceholder')"
          clearable
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item :label="t('common.status')">
        <el-select v-model="filters.status" :placeholder="t('common.all')" clearable style="width: 120px">
          <el-option :label="t('announcement.statusDraft')" value="draft" />
          <el-option :label="t('announcement.statusPublished')" value="published" />
          <el-option :label="t('announcement.statusOffline')" value="offline" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('announcement.priority')">
        <el-select v-model="filters.priority" :placeholder="t('common.all')" clearable style="width: 120px">
          <el-option :label="t('announcement.priorityUrgent')" value="urgent" />
          <el-option :label="t('announcement.priorityImportant')" value="important" />
          <el-option :label="t('announcement.priorityNormal')" value="normal" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">{{ t('common.search') }}</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="title" :label="t('announcement.title')" min-width="180" show-overflow-tooltip />
      <el-table-column :label="t('announcement.type')" width="100">
        <template #default="{ row }">{{ row.type_label || row.type }}</template>
      </el-table-column>
      <el-table-column :label="t('announcement.priority')" width="90">
        <template #default="{ row }">
          <el-tag :type="PRIORITY_MAP[row.priority]?.type || 'info'" size="small">
            {{ row.priority_label || PRIORITY_MAP[row.priority]?.label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('common.status')" width="90">
        <template #default="{ row }">
          <el-tag :type="STATUS_MAP[row.status]?.type || 'info'" size="small">
            {{ row.status_label || STATUS_MAP[row.status]?.label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="publisher_name" :label="t('announcement.publisher')" width="100" />
      <el-table-column prop="published_at" :label="t('announcement.publishedAt')" width="170" class-name="col-hide-md" />
      <el-table-column
        :label="t('common.actions')"
        :min-width="ACTION_COLUMN.promotion"
        class-name="col-actions"
        fixed="right"
      >
        <template #default="{ row }">
          <TableActionMenu :actions="buildActions(row)" />
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        background
        @current-change="fetchList"
        @size-change="handleSearch"
      />
    </div>
  </el-card>

  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="640px" destroy-on-close>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item :label="t('announcement.title')" prop="title">
        <el-input v-model="form.title" maxlength="100" show-word-limit />
      </el-form-item>
      <el-form-item :label="t('announcement.type')" prop="type">
        <el-select v-model="form.type" style="width: 100%">
          <el-option :label="t('announcement.typeMaintenance')" value="maintenance" />
          <el-option :label="t('announcement.typeUpdate')" value="update" />
          <el-option :label="t('announcement.typeNotice')" value="notice" />
          <el-option :label="t('announcement.typeDaily')" value="daily" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('announcement.priority')">
        <el-select v-model="form.priority" style="width: 100%">
          <el-option :label="t('announcement.priorityNormal')" value="normal" />
          <el-option :label="t('announcement.priorityImportant')" value="important" />
          <el-option :label="t('announcement.priorityUrgent')" value="urgent" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('announcement.scope')">
        <el-select v-model="form.scope" style="width: 100%">
          <el-option :label="t('announcement.scopeAll')" value="all" />
          <el-option :label="t('announcement.scopeRole')" value="role" />
          <el-option :label="t('announcement.scopeDepartment')" value="department" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="form.scope === 'role'" :label="t('announcement.targetRoles')">
        <el-select v-model="form.target_role_ids" multiple filterable style="width: 100%">
          <el-option v-for="item in roleOptions" :key="item.id" :label="roleOptionLabel(item)" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item v-if="form.scope === 'department'" :label="t('announcement.targetDepartments')">
        <el-select v-model="form.target_department_ids" multiple filterable style="width: 100%">
          <el-option v-for="item in departmentOptions" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('announcement.pinned')">
        <el-switch v-model="form.is_pinned" />
      </el-form-item>
      <el-form-item v-if="!form.id" label="保存并发布">
        <el-switch v-model="form.publishNow" />
        <span class="form-tip">开启后创建时立即发布（含置顶设置），并推送实时提醒</span>
      </el-form-item>
      <el-form-item :label="t('announcement.effectiveAt')" prop="effective_at">
        <el-date-picker
          v-model="form.effective_at"
          type="datetime"
          value-format="YYYY-MM-DDTHH:mm:ss"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item :label="t('announcement.expiresAt')" prop="expires_at">
        <el-date-picker
          v-model="form.expires_at"
          type="datetime"
          value-format="YYYY-MM-DDTHH:mm:ss"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item :label="t('announcement.content')" prop="content">
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="6"
          :placeholder="t('announcement.contentPlaceholder')"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" @click="handleSubmit">{{ t('common.save') }}</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="detailVisible" :title="t('announcement.detailTitle')" width="640px">
    <template v-if="currentRow">
      <el-descriptions :column="2" border>
        <el-descriptions-item :label="t('announcement.title')" :span="2">{{ currentRow.title }}</el-descriptions-item>
        <el-descriptions-item :label="t('announcement.type')">{{ currentRow.type_label }}</el-descriptions-item>
        <el-descriptions-item :label="t('announcement.priority')">{{ currentRow.priority_label }}</el-descriptions-item>
        <el-descriptions-item :label="t('announcement.scope')">{{ currentRow.scope_label }}</el-descriptions-item>
        <el-descriptions-item :label="t('common.status')">{{ currentRow.status_label }}</el-descriptions-item>
        <el-descriptions-item :label="t('announcement.publisher')">{{ currentRow.publisher_name || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="t('announcement.publishedAt')">{{ currentRow.published_at || '-' }}</el-descriptions-item>
      </el-descriptions>
      <div class="detail-content" v-html="currentRow.content" />
    </template>
    <template #footer>
      <el-button @click="detailVisible = false">{{ t('common.close') }}</el-button>
    </template>
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

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.detail-content {
  margin-top: 16px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
  line-height: 1.6;
}
</style>
