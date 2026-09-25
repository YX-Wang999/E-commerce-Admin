<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Refresh } from '@element-plus/icons-vue'
import { getLogisticsTrack } from '@/api/logistics'

const props = defineProps({
  orderId: {
    type: [Number, String],
    default: null,
  },
  logistics: {
    type: Object,
    default: null,
  },
  autoLoad: {
    type: Boolean,
    default: true,
  },
})

const { t } = useI18n()
const loading = ref(false)
const trackData = ref(null)

const display = computed(() => trackData.value || props.logistics)

const traces = computed(() => {
  const list = display.value?.traces || []
  return [...list]
})

async function load(refresh = false) {
  if (!props.orderId) return
  loading.value = true
  try {
    const res = await getLogisticsTrack(props.orderId, refresh)
    trackData.value = res.data
  } catch {
    if (props.logistics) {
      trackData.value = props.logistics
    }
  } finally {
    loading.value = false
  }
}

watch(
  () => props.orderId,
  (id) => {
    if (id && props.autoLoad) load(false)
  },
  { immediate: true },
)

defineExpose({ load })
</script>

<template>
  <div v-if="display" v-loading="loading" class="logistics-trace">
    <div class="logistics-head">
      <div>
        <span class="company">{{ display.express_company || '-' }}</span>
        <span class="number">{{ display.tracking_number || display.trackingNumber }}</span>
        <el-tag size="small" type="info">{{ display.status_label || display.status }}</el-tag>
      </div>
      <el-button
        v-if="orderId"
        link
        type="primary"
        :icon="Refresh"
        @click="load(true)"
      >
        {{ t('logistics.refreshTrack') }}
      </el-button>
    </div>

    <el-timeline v-if="traces.length" class="trace-timeline">
      <el-timeline-item
        v-for="(item, index) in traces"
        :key="`${item.time}-${index}`"
        :timestamp="item.time"
        :type="index === 0 ? 'primary' : undefined"
        placement="top"
      >
        {{ item.content }}
      </el-timeline-item>
    </el-timeline>
    <el-empty v-else :description="t('logistics.noTrace')" :image-size="64" />
  </div>
</template>

<style scoped>
.logistics-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.company {
  font-weight: 600;
  margin-right: 8px;
}

.number {
  color: #606266;
  margin-right: 8px;
}

.trace-timeline {
  margin-top: 8px;
  padding-left: 4px;
}
</style>
