<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getComplaints } from '@/api/complaint'

const router = useRouter()
const { t } = useI18n()

const loading = ref(true)
const activeTab = ref('all')
const list = ref([])

const tabs = computed(() => [
  { name: 'all', title: t('complaint.tabAll') },
  { name: 'pending', title: t('complaint.tabPending') },
  { name: 'processing', title: t('complaint.tabProcessing') },
  { name: 'done', title: t('complaint.tabDone') },
])

const statusMap = {
  pending: 'complaint.statusPending',
  merchant_processing: 'complaint.statusMerchantProcessing',
  customer_review: 'complaint.statusCustomerReview',
  platform_reviewing: 'complaint.statusPlatformReviewing',
  resolved: 'complaint.statusResolved',
  rejected: 'complaint.statusRejected',
  closed: 'complaint.statusClosed',
}

function matchTab(item) {
  if (activeTab.value === 'all') return true
  if (activeTab.value === 'pending') return item.status === 'pending'
  if (activeTab.value === 'processing') {
    return ['merchant_processing', 'customer_review', 'platform_reviewing'].includes(item.status)
  }
  return ['resolved', 'rejected', 'closed'].includes(item.status)
}

const filteredList = computed(() => list.value.filter(matchTab))

async function fetchList() {
  loading.value = true
  try {
    const res = await getComplaints({ page_size: 100 })
    list.value = res.data?.results || res.data || []
  } finally {
    loading.value = false
  }
}

function goDetail(item) {
  router.push({ name: 'ComplaintDetail', params: { id: item.id } })
}

onMounted(fetchList)
</script>

<template>
  <div class="complaint-page">
    <van-nav-bar :title="t('complaint.myTitle')" left-arrow @click-left="router.back()" />

    <van-tabs v-model:active="activeTab" sticky>
      <van-tab v-for="tab in tabs" :key="tab.name" :name="tab.name" :title="tab.title" />
    </van-tabs>

    <van-loading v-if="loading" class="page-loading" />
    <van-empty v-else-if="!filteredList.length" :description="t('complaint.empty')" />

    <div v-else class="complaint-list">
      <div v-for="item in filteredList" :key="item.id" class="complaint-card" @click="goDetail(item)">
        <div class="card-head">
          <span class="status">{{ t(statusMap[item.status] || 'complaint.statusPending') }}</span>
          <span class="time">{{ item.created_at?.replace('T', ' ').slice(0, 16) }}</span>
        </div>
        <div class="title">{{ item.title }}</div>
        <div class="meta">
          {{ t('complaint.orderNo', { no: item.order_no || '-' }) }}
          · {{ item.tenant_name }}
        </div>
        <div class="preview">{{ item.content }}</div>
        <van-button size="small" type="primary" plain>{{ t('complaint.viewDetail') }}</van-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.complaint-page {
  min-height: 100vh;
  background: #f5f6fa;
}
.page-loading {
  display: flex;
  justify-content: center;
  padding: 48px 0;
}
.complaint-list {
  padding: 12px 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.complaint-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px 16px;
}
.card-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}
.status {
  color: #ee0a24;
  font-size: 13px;
  font-weight: 600;
}
.time {
  color: #969799;
  font-size: 12px;
}
.title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 6px;
}
.meta {
  color: #969799;
  font-size: 12px;
  margin-bottom: 8px;
}
.preview {
  color: #646566;
  font-size: 13px;
  margin-bottom: 10px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
