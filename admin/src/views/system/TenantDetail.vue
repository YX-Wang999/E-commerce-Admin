<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  approveTenant,
  closeTenant,
  resumeTenant,
  suspendTenant,
} from '@/api/tenant'
import { getTenantTagConfigs } from '@/api/tags'
import { useTenantRoles } from '@/composables/useTenantRoles'
import { useTenantStore } from '@/stores/tenant'
import TenantChangeReviewPanel from '@/components/tenants/TenantChangeReviewPanel.vue'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const tenantStore = useTenantStore()
const { canApprove, canSuspend, canViewChanges } = useTenantRoles()

const activeTab = ref(
  route.query.tab === 'changes' ? 'changes' : route.query.tab === 'tags' ? 'tags' : 'overview',
)

watch(
  () => route.query.tab,
  (tab) => {
    if (tab === 'changes') activeTab.value = 'changes'
    else if (tab === 'tags') activeTab.value = 'tags'
    else activeTab.value = 'overview'
  },
)

const tagConfigs = ref([])
const tagLoading = ref(false)

const TAG_STATUS_LABELS = {
  pending: 'tags.statusPending',
  approved: 'tags.statusApproved',
  rejected: 'tags.statusRejected',
}

function tagStatusLabel(status) {
  const key = TAG_STATUS_LABELS[status]
  return key ? t(key) : status || '-'
}

async function loadTagConfigs() {
  if (!route.params.id) return
  tagLoading.value = true
  try {
    const res = await getTenantTagConfigs({ tenant: route.params.id, page_size: 100 })
    tagConfigs.value = res.data.results || res.data || []
  } finally {
    tagLoading.value = false
  }
}

watch(activeTab, (tab) => {
  if (tab === 'tags') loadTagConfigs()
})

const loading = ref(false)
const showSuspendDialog = ref(false)
const showCloseDialog = ref(false)
const showRestoreDialog = ref(false)

const suspendForm = reactive({
  reason: '',
  detail: '',
  notifyMerchant: true,
})

const closeForm = reactive({
  reason: '',
  detail: '',
})

const restoreForm = reactive({
  reason: '',
})

const suspendReasonOptions = [
  '违规商品',
  '售后不及时',
  '虚假宣传',
  '用户投诉过多',
  '其他',
]

const tenant = computed(() => tenantStore.currentTenant || {})
const stats = computed(() => tenant.value.stats || {})
const actionLogs = computed(() => tenant.value.action_logs || [])
const suspensionLogs = computed(() => tenant.value.suspension_logs || [])

const STATUS_META = {
  pending: { type: 'warning', labelKey: 'tenant.statusPending' },
  active: { type: 'success', labelKey: 'tenant.statusActive' },
  suspended: { type: 'warning', labelKey: 'tenant.statusSuspended' },
  closed: { type: 'danger', labelKey: 'tenant.statusClosed' },
}

const ACTION_LABELS = {
  approve: 'tenant.actionApprove',
  suspend: 'tenant.actionSuspend',
  resume: 'tenant.actionResume',
  create: 'tenant.actionCreate',
  delete: 'tenant.actionDelete',
  close: 'tenant.actionClose',
}

const SUSPENSION_ACTION_LABELS = {
  suspend: 'tenant.suspensionActionSuspend',
  restore: 'tenant.suspensionActionRestore',
  close: 'tenant.suspensionActionClose',
}

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

function statusTag(status) {
  if (!status) {
    return { type: 'info', label: '-' }
  }
  const meta = STATUS_META[status] || { type: 'info', labelKey: 'tenant.statusPending' }
  return { type: meta.type, label: t(meta.labelKey) }
}

function actionLabel(action) {
  const key = ACTION_LABELS[action]
  return key ? t(key) : action
}

function suspensionActionLabel(action) {
  const key = SUSPENSION_ACTION_LABELS[action]
  return key ? t(key) : action
}

async function loadDetail() {
  loading.value = true
  try {
    await tenantStore.fetchDetail(route.params.id)
  } catch {
    ElMessage.error(t('common.loadFailed'))
    router.push({ name: 'TenantList' })
  } finally {
    loading.value = false
  }
}

async function handleApprove() {
  await ElMessageBox.confirm(
    t('tenant.approveConfirm', { name: tenant.value.name }),
    t('common.tip'),
    { type: 'warning' },
  )
  await approveTenant(tenant.value.id)
  ElMessage.success(t('tenant.approveSuccess'))
  await loadDetail()
}

function resetSuspendForm() {
  suspendForm.reason = ''
  suspendForm.detail = ''
  suspendForm.notifyMerchant = true
}

function resetCloseForm() {
  closeForm.reason = ''
  closeForm.detail = ''
}

async function handleSuspend() {
  if (!suspendForm.reason) {
    ElMessage.warning(t('tenant.suspendReasonRequired'))
    return
  }
  await suspendTenant(tenant.value.id, {
    reason: suspendForm.reason,
    detail: suspendForm.detail,
    notify_merchant: suspendForm.notifyMerchant,
  })
  ElMessage.success(t('tenant.suspendSuccess'))
  showSuspendDialog.value = false
  resetSuspendForm()
  await loadDetail()
}

async function handleRestore() {
  await resumeTenant(tenant.value.id, {
    reason: restoreForm.reason || t('tenant.restoreDefaultReason'),
  })
  ElMessage.success(t('tenant.resumeSuccess'))
  showRestoreDialog.value = false
  restoreForm.reason = ''
  await loadDetail()
}

async function handleClose() {
  if (!closeForm.reason) {
    ElMessage.warning(t('tenant.closeReasonRequired'))
    return
  }
  await ElMessageBox.confirm(
    t('tenant.closeConfirm', { name: tenant.value.name }),
    t('common.tip'),
    { type: 'warning' },
  )
  await closeTenant(tenant.value.id, {
    reason: closeForm.reason,
    detail: closeForm.detail,
  })
  ElMessage.success(t('tenant.closeSuccess'))
  showCloseDialog.value = false
  resetCloseForm()
  await loadDetail()
}

onMounted(async () => {
  await loadDetail()
  if (route.query.action === 'suspend' && tenant.value.status === 'active') {
    showSuspendDialog.value = true
  }
})
onUnmounted(() => tenantStore.clearCurrent())
</script>

<template>
  <div v-loading="loading" class="tenant-detail">
    <div class="page-header">
      <div>
        <el-button link type="primary" @click="router.push({ name: 'TenantList' })">
          ← {{ t('tenant.backToList') }}
        </el-button>
        <h2>{{ tenant.name || t('tenant.detailTitle') }}</h2>
      </div>
      <div class="header-actions tenant-actions">
        <el-button
          v-if="canApprove && tenant.status === 'pending'"
          type="success"
          @click="handleApprove"
        >
          {{ t('tenant.approve') }}
        </el-button>
        <el-button
          v-if="canSuspend && tenant.status === 'active'"
          type="warning"
          @click="showSuspendDialog = true"
        >
          {{ t('tenant.suspendAccount') }}
        </el-button>
        <el-button
          v-if="canSuspend && tenant.status === 'suspended'"
          type="success"
          @click="showRestoreDialog = true"
        >
          {{ t('tenant.restoreAccount') }}
        </el-button>
        <el-button
          v-if="canSuspend && tenant.status !== 'closed'"
          type="danger"
          @click="showCloseDialog = true"
        >
          {{ t('tenant.closeAccount') }}
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="detail-tabs">
      <el-tab-pane :label="t('tenant.basicInfo')" name="overview">
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="6">
        <el-card shadow="never"><div class="stat-num">{{ stats.product_count ?? 0 }}</div><div>{{ t('tenant.productCount') }}</div></el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never"><div class="stat-num">{{ stats.order_count ?? 0 }}</div><div>{{ t('tenant.orderCount') }}</div></el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never"><div class="stat-num">{{ stats.customer_count ?? 0 }}</div><div>{{ t('tenant.customerCount') }}</div></el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="never"><div class="stat-num">{{ stats.conversation_count ?? 0 }}</div><div>{{ t('tenant.conversationCount') }}</div></el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" :header="t('tenant.basicInfo')">
          <el-descriptions :column="1" border>
            <el-descriptions-item :label="t('tenant.name')">{{ tenant.name }}</el-descriptions-item>
            <el-descriptions-item :label="t('tenant.code')">{{ tenant.code }}</el-descriptions-item>
            <el-descriptions-item :label="t('tenant.contactName')">{{ tenant.contact_name }}</el-descriptions-item>
            <el-descriptions-item :label="t('tenant.contactPhone')">{{ tenant.contact_phone }}</el-descriptions-item>
            <el-descriptions-item :label="t('tenant.contactEmail')">{{ tenant.contact_email }}</el-descriptions-item>
            <el-descriptions-item :label="t('tenant.address')">{{ tenant.address || '-' }}</el-descriptions-item>
            <el-descriptions-item :label="t('tenant.department')">{{ tenant.department_name || '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" :header="t('tenant.onboardInfo')">
          <el-descriptions :column="1" border>
            <el-descriptions-item :label="t('tenant.status')">
              <el-tag :type="statusTag(tenant.status).type">{{ statusTag(tenant.status).label }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item :label="t('tenant.appliedAt')">{{ formatDate(tenant.applied_at) }}</el-descriptions-item>
            <el-descriptions-item :label="t('tenant.approvedAt')">{{ formatDate(tenant.approved_at) }}</el-descriptions-item>
            <el-descriptions-item :label="t('tenant.approvedBy')">{{ tenant.approved_by_name || '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="log-card" :header="t('tenant.suspensionHistory')">
      <el-table :data="suspensionLogs" border empty-text="-">
        <el-table-column :label="t('tenant.actionType')" width="120">
          <template #default="{ row }">{{ suspensionActionLabel(row.action) }}</template>
        </el-table-column>
        <el-table-column prop="reason" :label="t('tenant.suspendReason')" min-width="180" show-overflow-tooltip />
        <el-table-column prop="operator_name" :label="t('tenant.operator')" width="120" />
        <el-table-column :label="t('tenant.actionTime')" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card shadow="never" class="log-card" :header="t('tenant.actionHistory')">
      <el-table :data="actionLogs" border empty-text="-">
        <el-table-column :label="t('tenant.actionType')" width="140">
          <template #default="{ row }">{{ actionLabel(row.action) }}</template>
        </el-table-column>
        <el-table-column prop="operator_name" :label="t('tenant.operator')" width="120" />
        <el-table-column prop="remark" :label="t('tenant.remark')" min-width="160" />
        <el-table-column :label="t('tenant.actionTime')" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>
      </el-tab-pane>

      <el-tab-pane v-if="canViewChanges" label="变更审核" name="changes" lazy>
        <TenantChangeReviewPanel
          v-if="route.params.id"
          :tenant-id="route.params.id"
          @reviewed="loadDetail"
        />
      </el-tab-pane>

      <el-tab-pane :label="t('tags.participationTab')" name="tags" lazy>
        <el-card v-loading="tagLoading" shadow="never">
          <el-table :data="tagConfigs" border empty-text="-">
            <el-table-column prop="tag_name" :label="t('tags.name')" width="140" />
            <el-table-column prop="tag_code" :label="t('tags.code')" width="140" />
            <el-table-column :label="t('tags.reviewStatus')" width="120">
              <template #default="{ row }">{{ tagStatusLabel(row.status) }}</template>
            </el-table-column>
            <el-table-column :label="t('common.status')" width="100">
              <template #default="{ row }">
                {{ row.is_participating ? t('tags.participating') : t('tags.notParticipating') }}
              </template>
            </el-table-column>
            <el-table-column prop="reject_reason" :label="t('tags.rejectReason')" min-width="160" show-overflow-tooltip />
            <el-table-column :label="t('tenant.actionTime')" width="180">
              <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="showSuspendDialog" :title="t('tenant.suspendDialogTitle')" width="520px">
      <el-form label-width="100px">
        <el-form-item :label="t('tenant.suspendReason')" required>
          <el-select v-model="suspendForm.reason" :placeholder="t('tenant.suspendReasonPlaceholder')" style="width: 100%">
            <el-option v-for="item in suspendReasonOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('tenant.suspendDetail')">
          <el-input v-model="suspendForm.detail" type="textarea" :rows="4" :placeholder="t('tenant.suspendDetailPlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('tenant.notifyMerchant')">
          <el-switch v-model="suspendForm.notifyMerchant" />
          <span class="form-tip">{{ t('tenant.notifyMerchantTip') }}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSuspendDialog = false">{{ t('common.cancel') }}</el-button>
        <el-button type="warning" @click="handleSuspend">{{ t('tenant.confirmSuspend') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showRestoreDialog" :title="t('tenant.restoreDialogTitle')" width="480px">
      <el-form label-width="100px">
        <el-form-item :label="t('tenant.restoreReason')">
          <el-input v-model="restoreForm.reason" type="textarea" :rows="3" :placeholder="t('tenant.restoreReasonPlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRestoreDialog = false">{{ t('common.cancel') }}</el-button>
        <el-button type="success" @click="handleRestore">{{ t('tenant.confirmRestore') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showCloseDialog" :title="t('tenant.closeDialogTitle')" width="520px">
      <el-form label-width="100px">
        <el-form-item :label="t('tenant.closeReason')" required>
          <el-input v-model="closeForm.reason" type="textarea" :rows="3" :placeholder="t('tenant.closeReasonPlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('tenant.suspendDetail')">
          <el-input v-model="closeForm.detail" type="textarea" :rows="3" :placeholder="t('tenant.closeDetailPlaceholder')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCloseDialog = false">{{ t('common.cancel') }}</el-button>
        <el-button type="danger" @click="handleClose">{{ t('tenant.confirmClose') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 8px 0 0;
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.stat-row {
  margin-bottom: 16px;
}

.stat-num {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 4px;
}

.log-card {
  margin-top: 16px;
}

.form-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}
</style>
