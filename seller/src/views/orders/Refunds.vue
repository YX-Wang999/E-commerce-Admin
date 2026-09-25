<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import ComplaintList from '@/views/complaints/List.vue'
import FeedbackList from '@/views/orders/FeedbackList.vue'
import { getComplaintSummary } from '@/api/complaints'
import { getFeedbackSummary } from '@/api/feedback'
import { useComplaintBadgeStore } from '@/stores/complaintBadge'

const { t } = useI18n()
const complaintBadgeStore = useComplaintBadgeStore()

const activeTab = ref('feedback')
const feedbackPending = ref(0)
const complaintPending = ref(0)
const feedbackRef = ref(null)

async function refreshBadges() {
  try {
    const [fb, cp] = await Promise.all([getFeedbackSummary(), getComplaintSummary()])
    feedbackPending.value = fb.data?.pending_count || 0
    complaintPending.value = cp.data?.pending_count || 0
  } catch {
    feedbackPending.value = 0
    complaintPending.value = 0
  }
  await complaintBadgeStore.refresh()
}

function onTabChange(name) {
  if (name === 'feedback') {
    feedbackRef.value?.fetchList?.()
  }
}

onMounted(refreshBadges)
</script>

<template>
  <div class="refunds-page">
    <div class="page-header">
      <h2>{{ t('seller.menuRefunds') }}</h2>
    </div>

    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <el-tab-pane name="feedback">
        <template #label>
          <span>{{ t('seller.tabCustomerFeedback') }}</span>
          <el-badge v-if="feedbackPending" :value="feedbackPending" class="tab-badge" />
        </template>
        <FeedbackList ref="feedbackRef" />
      </el-tab-pane>
      <el-tab-pane name="complaints">
        <template #label>
          <span>{{ t('seller.tabComplaints') }}</span>
          <el-badge v-if="complaintPending" :value="complaintPending" class="tab-badge" />
        </template>
        <ComplaintList @updated="refreshBadges" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.refunds-page { padding: 4px 0; }
.page-header { margin-bottom: 8px; }
.page-header h2 { margin: 0; font-size: 18px; }
.tab-badge { margin-left: 6px; }
</style>
