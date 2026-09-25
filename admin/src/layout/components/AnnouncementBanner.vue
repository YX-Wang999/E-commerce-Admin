<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getAnnouncementBanners } from '@/api/announcement'

const { t } = useI18n()
const router = useRouter()

const banners = ref([])
const dismissedIds = ref(new Set(JSON.parse(sessionStorage.getItem('dismissed_announcements') || '[]')))

const visibleBanners = computed(() =>
  banners.value.filter((item) => !dismissedIds.value.has(item.id)),
)

function alertType(priority) {
  if (priority === 'urgent') return 'error'
  if (priority === 'important') return 'warning'
  return 'info'
}

function dismiss(id) {
  dismissedIds.value.add(id)
  sessionStorage.setItem(
    'dismissed_announcements',
    JSON.stringify([...dismissedIds.value]),
  )
}

function goCenter() {
  router.push('/announcements')
}

async function fetchBanners() {
  try {
    const res = await getAnnouncementBanners()
    banners.value = res.data || []
  } catch {
    banners.value = []
  }
}

onMounted(fetchBanners)

defineExpose({ refresh: fetchBanners })
</script>

<template>
  <div v-if="visibleBanners.length" class="announcement-banner-wrap">
    <el-alert
      v-for="item in visibleBanners"
      :key="item.id"
      :type="alertType(item.priority)"
      show-icon
      closable
      class="announcement-banner"
      :class="{ 'is-pinned': item.is_pinned }"
      @close="dismiss(item.id)"
    >
      <template #title>
        <span class="banner-title">
          <el-tag v-if="item.is_pinned" type="success" size="small" effect="dark">{{ t('announcement.pinned') }}</el-tag>
          {{ item.title }}
        </span>
      </template>
      <div class="banner-body">
        <div class="banner-content" v-html="item.content" />
        <el-button link type="primary" size="small" @click="goCenter">
          {{ t('announcement.viewAll') }}
        </el-button>
      </div>
    </el-alert>
  </div>
</template>

<style scoped>
.announcement-banner-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 16px 0;
}

.announcement-banner {
  margin: 0;
}

.announcement-banner.is-pinned {
  border-width: 1px;
  border-style: solid;
}

.banner-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.banner-body {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.banner-content {
  flex: 1;
  font-size: 13px;
  line-height: 1.5;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.banner-content :deep(p) {
  margin: 0;
}

@media (max-width: 575px) {
  .announcement-banner-wrap {
    padding: 8px 8px 0;
  }

  .banner-body {
    flex-direction: column;
  }
}
</style>
