<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getSeckillActivities, getSeckillProducts } from '@/api/promotion'
import { usePromoCountdown } from '@/composables/usePromoCountdown'
import { formatPrice, resolveImageUrl } from '@/utils/product'

const router = useRouter()
const { t } = useI18n()

const loading = ref(true)
const activities = ref([])
const products = ref([])
const selectedActivityId = ref(null)

const selectedActivity = computed(() =>
  activities.value.find((item) => item.id === selectedActivityId.value),
)

const activeEndTime = computed(() => products.value[0]?.end_time || selectedActivity.value?.end_time || null)
const { countdownText } = usePromoCountdown(activeEndTime)

async function fetchActivities() {
  const res = await getSeckillActivities()
  activities.value = res.data || []
  const ongoing = activities.value.find((item) => item.phase === 'ongoing') || activities.value[0]
  if (ongoing) {
    selectedActivityId.value = ongoing.id
    await fetchProducts(ongoing.id)
  }
}

async function fetchProducts(activityId) {
  if (!activityId) {
    products.value = []
    return
  }
  const res = await getSeckillProducts({ activity_id: activityId })
  products.value = res.data || []
}

async function selectActivity(activity) {
  selectedActivityId.value = activity.id
  loading.value = true
  try {
    await fetchProducts(activity.id)
  } finally {
    loading.value = false
  }
}

function goProduct(item) {
  if (item.product_id) {
    router.push({ name: 'ProductDetail', params: { id: item.product_id } })
  }
}

function goFullPage() {
  router.push(
    selectedActivityId.value
      ? { name: 'Seckill', query: { activity_id: selectedActivityId.value } }
      : { name: 'Seckill' },
  )
}

onMounted(async () => {
  loading.value = true
  try {
    await fetchActivities()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="seckill-panel">
    <div class="seckill-header">
      <div>
        <div class="seckill-header__name">{{ t('home.flashSale') }}</div>
        <div v-if="countdownText && countdownText !== '00:00:00'" class="seckill-header__countdown">
          {{ t('seckill.countdown', { time: countdownText }) }}
        </div>
      </div>
      <button type="button" class="seckill-header__more" @click="goFullPage">
        {{ t('home.viewMore') }}
        <van-icon name="arrow" size="12" />
      </button>
    </div>

    <van-skeleton v-if="loading && !activities.length" :row="4" title />

    <template v-else>
      <div v-if="activities.length" class="activity-tabs">
        <button
          v-for="activity in activities"
          :key="activity.id"
          type="button"
          class="activity-tab"
          :class="{ active: selectedActivityId === activity.id }"
          @click="selectActivity(activity)"
        >
          {{ activity.name }}
        </button>
      </div>

      <div v-if="products.length" class="product-grid">
        <article
          v-for="item in products"
          :key="item.id"
          class="product-item"
          @click="goProduct(item)"
        >
          <img :src="resolveImageUrl(item.image)" class="product-image" alt="" />
          <div class="product-name">{{ item.product_name || item.name }}</div>
          <div class="product-price">{{ formatPrice(item.seckill_price ?? item.price) }}</div>
        </article>
      </div>

      <div v-else-if="!loading" class="empty-state">
        <van-icon name="clock-o" size="40" color="#dcdee0" />
        <p>{{ t('seckill.empty') }}</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.seckill-panel {
  padding: 8px 12px 16px;
}

.seckill-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  padding: 10px 12px;
  background: #fff;
  border-radius: 8px;
}

.seckill-header__name {
  font-size: 16px;
  font-weight: 700;
  color: #e4393c;
}

.seckill-header__countdown {
  margin-top: 4px;
  font-size: 12px;
  color: #e4393c;
  font-variant-numeric: tabular-nums;
}

.seckill-header__more {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  border: none;
  background: transparent;
  color: #969799;
  font-size: 12px;
  cursor: pointer;
}

.activity-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  margin-bottom: 10px;
  padding: 0 2px;
  scrollbar-width: none;
}

.activity-tabs::-webkit-scrollbar {
  display: none;
}

.activity-tab {
  flex-shrink: 0;
  padding: 6px 12px;
  border: 1px solid #eee;
  border-radius: 999px;
  background: #fff;
  font-size: 13px;
  color: #666;
  cursor: pointer;
}

.activity-tab.active {
  border-color: #e4393c;
  color: #e4393c;
  font-weight: 600;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.product-item {
  padding: 10px;
  background: #fff;
  border-radius: 10px;
  cursor: pointer;
}

.product-image {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  border-radius: 8px;
  background: #f5f5f5;
}

.product-name {
  margin-top: 8px;
  font-size: 13px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-price {
  margin-top: 4px;
  font-size: 15px;
  font-weight: 700;
  color: #e4393c;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  min-height: 200px;
  justify-content: center;
  background: #fff;
  border-radius: 12px;
  color: #969799;
  font-size: 14px;
}
</style>
