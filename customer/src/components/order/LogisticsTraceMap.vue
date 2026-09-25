<script setup>
import { computed, nextTick, onErrorCaptured, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { BMap, BMarker, BPolyline } from '@npm-tke/vue3-baidu-map-gl'
import { tracesToMapPoints } from '@/utils/logisticsMap'

const props = defineProps({
  traces: {
    type: Array,
    default: () => [],
  },
  address: {
    type: String,
    default: '',
  },
})

const { t } = useI18n()

const renderError = ref(false)

onErrorCaptured((error) => {
  console.warn('[LogisticsTraceMap]', error)
  renderError.value = true
  return false
})

const baiduAK = import.meta.env.VITE_BAIDU_MAP_AK || ''
const mapRef = ref(null)
const mapReady = ref(false)
const mapFailed = ref(false)
let loadTimer = null

const mapPoints = computed(() => tracesToMapPoints(props.traces, props.address))
const hasValidTraces = computed(() => mapPoints.value.length > 0)
const showMap = computed(() => Boolean(baiduAK) && hasValidTraces.value && !mapFailed.value && !renderError.value)

const polylinePath = computed(() => mapPoints.value.map((point) => point.position))

const mapCenter = computed(() => {
  const first = mapPoints.value[0]?.position
  return first || { lng: 116.404, lat: 39.915 }
})

const mapZoom = computed(() => {
  if (mapPoints.value.length <= 1) return SINGLE_POINT_ZOOM
  return 7
})

function markerIcon(kind) {
  if (kind === 'start') return 'start'
  if (kind === 'end') return 'end'
  return 'simple_blue'
}

function clearLoadTimer() {
  if (loadTimer) {
    clearTimeout(loadTimer)
    loadTimer = null
  }
}

const MAX_MAP_ZOOM = 11
const SINGLE_POINT_ZOOM = 10

function fitMapViewport(map, BMapGL) {
  if (!map || !BMapGL || !mapPoints.value.length) return
  const points = mapPoints.value.map(
    (point) => new BMapGL.Point(point.position.lng, point.position.lat),
  )
  if (points.length === 1) {
    map.centerAndZoom(points[0], SINGLE_POINT_ZOOM)
    return
  }
  map.setViewport(points, { margins: [60, 60, 60, 60] })
  if (typeof map.getZoom === 'function' && map.getZoom() > MAX_MAP_ZOOM) {
    map.setZoom(MAX_MAP_ZOOM)
  }
}

function handleMapInit(payload) {
  clearLoadTimer()
  mapReady.value = true
  mapFailed.value = false
  nextTick(() => {
    fitMapViewport(payload?.map, payload?.BMapGL)
  })
}

function scheduleLoadCheck() {
  clearLoadTimer()
  if (!baiduAK || !hasValidTraces.value) return
  mapFailed.value = false
  mapReady.value = false
  loadTimer = setTimeout(() => {
    if (!mapReady.value) {
      mapFailed.value = true
    }
  }, 12000)
}

watch(
  () => [props.traces, props.address],
  () => {
    if (import.meta.env.DEV) {
      console.log('[LogisticsTraceMap] traces:', props.traces)
      console.log('[LogisticsTraceMap] mapPoints:', mapPoints.value)
    }
    scheduleLoadCheck()
    if (mapReady.value && mapRef.value) {
      nextTick(() => {
        const map = mapRef.value?.getMapInstance?.()
        fitMapViewport(map, window.BMapGL)
      })
    }
  },
  { deep: true, immediate: true },
)
</script>

<template>
  <div v-if="(showMap || (baiduAK && hasValidTraces && (mapFailed || renderError)))" class="trace-map">
    <div class="trace-map-title">{{ t('checkout.logisticsMapTitle') }}</div>

    <div v-if="showMap" class="trace-map-container">
      <BMap
        ref="mapRef"
        :ak="baiduAK"
        :center="mapCenter"
        :zoom="mapZoom"
        width="100%"
        height="300px"
        :enable-scroll-wheel-zoom="true"
        @initd="handleMapInit"
        @load="handleMapInit"
      >
        <BMarker
          v-for="(point, index) in mapPoints"
          :key="`${point.label}-${index}`"
          :position="point.position"
          :icon="markerIcon(point.kind)"
          :title="point.title"
        />
        <BPolyline
          v-if="polylinePath.length > 1"
          :path="polylinePath"
          stroke-color="#1989fa"
          :stroke-weight="3"
          :stroke-opacity="0.85"
        />
      </BMap>
    </div>

    <div v-else-if="mapFailed || renderError" class="trace-map-fallback">
      {{ t('checkout.logisticsMapLoadFailed') }}
    </div>
  </div>
</template>

<style scoped>
.trace-map {
  width: 100%;
  min-width: 0;
}

.trace-map-title {
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #323233;
}

.trace-map-container {
  width: 100%;
  height: 300px;
  overflow: hidden;
  border-radius: 8px;
  border: 1px solid #ebedf0;
}

.trace-map-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
  padding: 16px;
  font-size: 13px;
  color: #969799;
  text-align: center;
  background: #f7f8fa;
  border-radius: 8px;
  border: 1px dashed #dcdee0;
}
</style>
