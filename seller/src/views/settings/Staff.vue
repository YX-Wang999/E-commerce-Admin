<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createStaff, deleteStaff, getStaffList } from '@/api/staff'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const authStore = useAuthStore()
const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const submitting = ref(false)

const form = reactive({
  user: '',
  role: 'staff',
})

const roleMap = computed(() => ({
  owner: t('seller.staffRoleOwner'),
  manager: t('seller.staffRoleManager'),
  staff: t('seller.staffRoleStaff'),
}))

async function fetchList() {
  loading.value = true
  try {
    const res = await getStaffList()
    tableData.value = res.data || []
  } finally {
    loading.value = false
  }
}

function openDialog() {
  form.user = ''
  form.role = 'staff'
  dialogVisible.value = true
}

async function handleCreate() {
  if (!form.user) {
    ElMessage.warning(t('seller.enterUserId'))
    return
  }
  submitting.value = true
  try {
    await createStaff({ user: Number(form.user), role: form.role })
    ElMessage.success(t('seller.staffAdded'))
    dialogVisible.value = false
    await fetchList()
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row) {
  if (row.role === 'owner') {
    ElMessage.warning(t('seller.cannotRemoveOwner'))
    return
  }
  try {
    await ElMessageBox.confirm(
      t('seller.removeStaffConfirm', { name: row.user?.username || row.user }),
      t('common.tip'),
      {
        type: 'warning',
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
      },
    )
    await deleteStaff(row.id)
    ElMessage.success(t('seller.staffRemoved'))
    await fetchList()
  } catch {
    // cancelled or handled
  }
}

onMounted(fetchList)
</script>

<template>
  <div class="page-card">
    <div class="page-header">
      <h2>{{ t('seller.staff') }}</h2>
      <el-button v-if="authStore.isManager()" type="primary" @click="openDialog">{{ t('seller.addStaff') }}</el-button>
    </div>

    <el-table v-loading="loading" :data="tableData" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column :label="t('seller.username')" min-width="140">
        <template #default="{ row }">
          {{ row.user?.username || row.user }}
        </template>
      </el-table-column>
      <el-table-column :label="t('seller.nickname')" min-width="120">
        <template #default="{ row }">
          {{ row.user?.nickname || '-' }}
        </template>
      </el-table-column>
      <el-table-column :label="t('seller.role')" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ roleMap[row.role] || row.role }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('seller.status')" width="90">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? t('seller.active') : t('seller.inactive') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column v-if="authStore.isManager()" :label="t('seller.actions')" width="100" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.role !== 'owner'"
            type="danger"
            link
            @click="handleDelete(row)"
          >
            {{ t('seller.removeStaff') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="t('seller.addStaffTitle')" width="420px">
      <el-form label-width="90px">
        <el-form-item :label="t('seller.userId')">
          <el-input v-model="form.user" :placeholder="t('seller.platformUserId')" />
        </el-form-item>
        <el-form-item :label="t('seller.role')">
          <el-select v-model="form.role" style="width: 100%">
            <el-option :label="t('seller.staffRoleStaff')" value="staff" />
            <el-option :label="t('seller.staffRoleManager')" value="manager" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCreate">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>
