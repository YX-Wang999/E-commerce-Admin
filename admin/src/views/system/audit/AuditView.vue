<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { getAuditLogList } from '@/api/audit'
import { useAuthStore } from '@/stores/auth'
import { useRoleLabel } from '@/composables/useRoleLabel'

const { t, locale } = useI18n()
const authStore = useAuthStore()
const { roleLabels } = useRoleLabel()

function auditRoleText(row) {
  if (!row.user_role_codes?.length) {
    return row.user_role_labels || '-'
  }
  return roleLabels(
    row.user_role_codes.map((code, index) => ({
      code,
      name: (row.user_role_labels || '').split('、')[index] || code,
    })),
  )
}

const isDeptManager = computed(() => {
  const user = authStore.user
  if (!user) {
    return false
  }
  if (user.is_superuser) {
    return false
  }
  return user.roles?.some((role) => role.code === 'dept_manager') ?? false
})

const loading = ref(false)
const tableData = ref([])
const filters = reactive({
  username: '',
  module: '',
  action: '',
})
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const actionMap = computed(() => ({
  create: t('system.audit.actionCreate'),
  update: t('system.audit.actionUpdate'),
  delete: t('system.audit.actionDelete'),
  other: t('system.audit.actionOther'),
}))

async function fetchList() {
  loading.value = true
  try {
    const res = await getAuditLogList({
      page: pagination.page,
      page_size: pagination.pageSize,
      username: filters.username || undefined,
      module: filters.module || undefined,
      action: filters.action || undefined,
      locale: locale.value,
    })
    tableData.value = res.data.results || []
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

onMounted(fetchList)
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>{{ t('system.audit.title') }}</span>
        <el-alert
          v-if="isDeptManager"
          :title="t('system.audit.deptScopeHint')"
          type="info"
          :closable="false"
          show-icon
          class="scope-alert"
        />
      </div>
    </template>

    <el-form :inline="true" :model="filters" class="filter-form">
      <el-form-item :label="t('system.audit.username')">
        <el-input v-model="filters.username" clearable :placeholder="t('system.audit.username')" />
      </el-form-item>
      <el-form-item :label="t('system.audit.module')">
        <el-input v-model="filters.module" clearable :placeholder="t('system.audit.module')" />
      </el-form-item>
      <el-form-item :label="t('system.audit.actionFilter')">
        <el-select v-model="filters.action" clearable :placeholder="t('common.all')">
          <el-option :label="t('system.audit.actionCreate')" value="create" />
          <el-option :label="t('system.audit.actionUpdate')" value="update" />
          <el-option :label="t('system.audit.actionDelete')" value="delete" />
          <el-option :label="t('system.audit.actionOther')" value="other" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">{{ t('common.search') }}</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="tableData" border>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" :label="t('common.user')" width="120" />
      <el-table-column :label="t('system.audit.roles')" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">
          {{ auditRoleText(row) }}
        </template>
      </el-table-column>
      <el-table-column prop="module" :label="t('system.audit.module')" width="120" />
      <el-table-column :label="t('system.audit.action')" width="100">
        <template #default="{ row }">
          {{ actionMap[row.action] || row.action }}
        </template>
      </el-table-column>
      <el-table-column prop="request_method" :label="t('system.audit.method')" width="90" />
      <el-table-column prop="request_path" :label="t('system.audit.requestPath')" min-width="180" show-overflow-tooltip />
      <el-table-column prop="ip" :label="t('system.audit.ip')" width="140" />
      <el-table-column prop="created_at" :label="t('system.audit.time')" width="180" class-name="col-hide-md" />
    </el-table>

    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="fetchList"
      />
    </div>
  </el-card>
</template>

<style scoped>
.filter-form {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.scope-alert {
  margin-top: 4px;
}

.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
