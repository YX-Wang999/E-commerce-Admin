<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getVisibleAnnouncements } from '@/api/announcement'

const { t } = useI18n()
const router = useRouter()

const loading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })
const detailVisible = ref(false)
const currentRow = ref(null)

const PRIORITY_MAP = computed(() => ({
  urgent: { label: t('announcement.priorityUrgent'), type: 'danger' },
  important: { label: t('announcement.priorityImportant'), type: 'warning' },
  normal: { label: t('announcement.priorityNormal'), type: 'info' },
}))

const TYPE_MAP = computed(() => ({
  maintenance: t('announcement.typeMaintenance'),
  update: t('announcement.typeUpdate'),
  notice: t('announcement.typeNotice'),
  daily: t('announcement.typeDaily'),
}))

async function fetchList() {
  loading.value = true
  try {
    const res = await getVisibleAnnouncements({
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    tableData.value = res.data.results || []
    pagination.total = res.data.count || 0
  } finally {
    loading.value = false
  }
}

function openDetail(row) {
  currentRow.value = row
  detailVisible.value = true
}

function goBack() {
  router.push('/dashboard')
}

onMounted(fetchList)
</script>

<template>
  <el-card shadow="never">
    <template #header>
      <div class="card-header">
        <span>{{ t('announcement.centerTitle') }}</span>
        <el-button @click="goBack">{{ t('announcement.backDashboard') }}</el-button>
      </div>
    </template>

    <el-table v-loading="loading" :data="tableData" border stripe @row-click="openDetail">
      <el-table-column prop="title" :label="t('announcement.title')" min-width="200" show-overflow-tooltip />
      <el-table-column :label="t('announcement.type')" width="110">
        <template #default="{ row }">
          {{ row.type_label || TYPE_MAP[row.type] || row.type }}
        </template>
      </el-table-column>
      <el-table-column :label="t('announcement.priority')" width="90">
        <template #default="{ row }">
          <el-tag :type="PRIORITY_MAP[row.priority]?.type || 'info'" size="small">
            {{ row.priority_label || PRIORITY_MAP[row.priority]?.label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('announcement.pinned')" width="80" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.is_pinned" type="success" size="small">{{ t('common.yes') }}</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="published_at" :label="t('announcement.publishedAt')" width="170" />
      <el-table-column :label="t('common.actions')" width="90" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click.stop="openDetail(row)">{{ t('common.detail') }}</el-button>
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
        @size-change="fetchList"
      />
    </div>
  </el-card>

  <el-dialog v-model="detailVisible" :title="currentRow?.title || t('announcement.detailTitle')" width="640px">
    <template v-if="currentRow">
      <el-descriptions :column="2" border>
        <el-descriptions-item :label="t('announcement.type')">
          {{ currentRow.type_label || TYPE_MAP[currentRow.type] }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('announcement.priority')">
          {{ currentRow.priority_label || PRIORITY_MAP[currentRow.priority]?.label }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('announcement.publishedAt')" :span="2">
          {{ currentRow.published_at || '-' }}
        </el-descriptions-item>
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
