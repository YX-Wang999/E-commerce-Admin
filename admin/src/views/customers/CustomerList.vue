<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCustomerList, updateCustomer, deleteCustomer } from '@/api/customer'
import { getCustomerMembership } from '@/api/membership'
import { ACTION_COLUMN } from '@/config/table'

const { t } = useI18n()

const LEVEL_LABELS = {
  normal: 'customer.levelNormal',
  silver: 'customer.levelSilver',
  gold: 'customer.levelGold',
  platinum: 'customer.levelPlatinum',
  diamond: 'customer.levelDiamond',
}

const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const filters = reactive({ keyword: '', level: '' })
const togglingId = ref(null)
const membershipVisible = ref(false)
const membershipLoading = ref(false)
const membershipData = ref(null)

const levelOptions = computed(() => [
  { label: t('customer.levelNormal'), value: 'normal' },
  { label: t('customer.levelSilver'), value: 'silver' },
  { label: t('customer.levelGold'), value: 'gold' },
  { label: t('customer.levelPlatinum'), value: 'platinum' },
  { label: t('customer.levelDiamond'), value: 'diamond' },
])

function levelLabel(level) {
  const key = LEVEL_LABELS[level]
  return key ? t(key) : level
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getCustomerList({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      level: filters.level || undefined,
    })
    tableData.value = res.data.results || []
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

async function openMembership(row) {
  membershipVisible.value = true
  membershipLoading.value = true
  membershipData.value = null
  try {
    const res = await getCustomerMembership(row.id)
    membershipData.value = res.data
  } catch {
    membershipVisible.value = false
  } finally {
    membershipLoading.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      t('customer.deleteConfirm', { name: row.nickname || row.name || row.phone }),
      t('common.tip'),
      { type: 'warning' },
    )
  } catch {
    return
  }
  try {
    await deleteCustomer(row.id)
    ElMessage.success(t('customer.deleteSuccess'))
    fetchList()
  } catch {
    // 错误信息已由 request 拦截器展示
  }
}

async function handleToggleActive(row) {
  const disabling = row.is_active
  const confirmKey = disabling ? 'customer.disableConfirm' : 'customer.enableConfirm'
  try {
    await ElMessageBox.confirm(
      t(confirmKey, { name: row.nickname || row.name || row.phone }),
      t('common.tip'),
      { type: 'warning' },
    )
  } catch {
    return
  }

  togglingId.value = row.id
  try {
    await updateCustomer(row.id, { is_active: !row.is_active })
    row.is_active = !row.is_active
    ElMessage.success(t('customer.updateSuccess'))
  } catch {
    // 错误信息已由 request 拦截器展示
  } finally {
    togglingId.value = null
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
        <div>
          <span>{{ t('customer.listTitle') }}</span>
          <p class="subtitle">{{ t('customer.listSubtitle') }}</p>
          <p class="hint">{{ t('customer.noDeleteHint') }}</p>
        </div>
      </div>
    </template>

    <el-form :inline="true" class="filter-form">
      <el-form-item :label="t('common.keyword')">
        <el-input
          v-model="filters.keyword"
          :placeholder="t('customer.keywordPlaceholder')"
          clearable
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item :label="t('customer.level')">
        <el-select v-model="filters.level" clearable :placeholder="t('common.pleaseSelect')" style="width: 140px">
          <el-option v-for="item in levelOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">{{ t('common.search') }}</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="nickname" :label="t('customer.nickname')" width="110" show-overflow-tooltip />
      <el-table-column prop="phone" :label="t('customer.phone')" width="130" />
      <el-table-column prop="email" :label="t('customer.email')" min-width="160" show-overflow-tooltip />
      <el-table-column :label="t('customer.memberLevelName')" width="110">
        <template #default="{ row }">
          <el-tag size="small">{{ row.member_level_name || levelLabel(row.level) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="growth_points" :label="t('customer.growthPoints')" width="90" align="right" />
      <el-table-column prop="points" :label="t('customer.points')" width="90" align="right" />
      <el-table-column :label="t('common.status')" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? t('customer.statusNormal') : t('common.disabled') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="registered_at" :label="t('customer.registeredAt')" width="170" />
      <el-table-column
        :label="t('common.actions')"
        :min-width="ACTION_COLUMN.basic + 40"
        class-name="col-actions"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button link type="primary" @click="openMembership(row)">{{ t('customer.viewMembership') }}</el-button>
          <el-button
            link
            :type="row.is_active ? 'warning' : 'success'"
            :loading="togglingId === row.id"
            @click="handleToggleActive(row)"
          >
            {{ row.is_active ? t('customer.disable') : t('customer.enable') }}
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

    <el-dialog
      v-model="membershipVisible"
      :title="t('customer.membershipDetail')"
      width="720px"
      destroy-on-close
    >
      <div v-loading="membershipLoading">
        <template v-if="membershipData">
          <el-descriptions :column="2" border size="small" class="membership-summary">
            <el-descriptions-item :label="t('customer.memberLevelName')">
              {{ membershipData.summary?.current_level?.name }}
            </el-descriptions-item>
            <el-descriptions-item :label="t('customer.growthPoints')">
              {{ membershipData.summary?.growth_points }}
            </el-descriptions-item>
            <el-descriptions-item :label="t('customer.checkinStreak')">
              {{ membershipData.summary?.checkin_streak }} {{ t('common.day') || '天' }}
            </el-descriptions-item>
            <el-descriptions-item :label="t('customer.totalCheckins')">
              {{ membershipData.summary?.total_checkins }}
            </el-descriptions-item>
          </el-descriptions>

          <h4 class="log-title">{{ t('customer.growthLogs') }}</h4>
          <el-table :data="membershipData.growth_logs || []" border stripe size="small" max-height="320">
            <el-table-column prop="created_at" :label="t('customer.logTime')" width="170" />
            <el-table-column prop="log_type_label" :label="t('customer.logType')" width="100" />
            <el-table-column prop="amount" :label="t('customer.logAmount')" width="80" align="right" />
            <el-table-column prop="balance_after" :label="t('customer.logBalance')" width="90" align="right" />
            <el-table-column prop="description" :label="t('customer.logDescription')" min-width="160" show-overflow-tooltip />
          </el-table>
        </template>
      </div>
    </el-dialog>
  </el-card>
</template>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  color: #909399;
  font-weight: normal;
}
.hint {
  margin: 4px 0 0;
  font-size: 12px;
  color: #c0c4cc;
  font-weight: normal;
}
.filter-form {
  margin-bottom: 16px;
}
.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
.membership-summary {
  margin-bottom: 16px;
}
.log-title {
  margin: 0 0 8px;
  font-size: 14px;
  color: #303133;
}
</style>
