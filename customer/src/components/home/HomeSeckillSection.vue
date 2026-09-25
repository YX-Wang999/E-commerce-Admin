<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getSeckillProducts } from '@/api/promotion'
import { usePromoCountdown } from '@/composables/usePromoCountdown'
import { formatPrice, resolveImageUrl } from '@/utils/product'

const router = useRouter()
const { t } = useI18n()

const items = ref([])
const loading = ref(true)

const endTime = computed(() => items.value[0]?.end_time || null)
const activityName = computed(() => items.value[0]?.activity_name || t('home.flashSale'))
const { countdownText } = usePromoCountdown(endTime)

async function fetchSeckill() {
  loading.value = true
  try {
    const res = await getSeckillProducts()
    items.value = (res.data || []).slice(0, 5)
  } catch {
    items.value = []
  } finally {
    loading.value = false
  }
}

function goMore() {
  router.push({ name: 'Seckill' })
}

function goItem(item) {
  if (item.activity_id) {
    router.push({ name: 'Seckill', query: { activity_id: item.activity_id } })
  } else {
    goMore()
  }
}

onMounted(fetchSeckill)
</script>

<template>
  <section v-if="loading || items.length" class="seckill-section card-block">
    <div class="section-head">
      <div class="section-title">
        <span class="title-text">{{ activityName }}</span>
        <span v-if="countdownText && countdownText !== '00:00:00'" class="countdown">{{ countdownText }}</span>
      </div>
      <button type="button" class="more-link" @click="goMore">
        {{ t('home.viewMore') }}
        <van-icon name="arrow" size="12" />
      </button>
    </div>

    <van-skeleton v-if="loading" :row="2" title />

    <div v-else class="scroll-row">
      <article
        v-for="item in items"
        :key="`${item.activity_id}-${item.product_id}`"
        class="seckill-card"
        @click="goItem(item)"
      >
        <img :src="resolveImageUrl(item.image)" class="seckill-img" alt="" />
        <div class="seckill-price">{{ formatPrice(item.seckill_price) }}</div>
        <div class="origin-price">{{ formatPrice(item.original_price) }}</div>
        <van-progress
          :percentage="item.sold_percent || 0"
          stroke-width="4"
          color="#e4393c"
          track-color="#ffe1e1"
          :show-pivot="false"
          class="progress"
        />
      </article>
    </div>
  </section>
</template>

<style scoped>
.card-block {
  margin: 12px 12px 0;
  padding: 12px;
  background: #fff;
  border-radius: 12px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-text {
  font-size: 16px;
  font-weight: 700;
  color: #e4393c;
}

.countdown {
  padding: 2px 8px;
  border-radius: 4px;
  background: #e4393c;
  color: #fff;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.more-link {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  border: none;
  background: transparent;
  font-size: 12px;
  color: #999;
  cursor: pointer;
}

.scroll-row {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 4px;
  -webkit-overflow-scrolling: touch;
}

.scroll-row::-webkit-scrollbar {
  display: none;
}

.seckill-card {
  flex: 0 0 100px;
  cursor: pointer;
}

.seckill-img {
  width: 100px;
  height: 100px;
  border-radius: 8px;
  object-fit: cover;
  background: #f5f5f5;
}

.seckill-price {
  margin-top: 6px;
  font-size: 14px;
  font-weight: 700;
  color: #e4393c;
}

.origin-price {
  font-size: 11px;
  color: #999;
  text-decoration: line-through;
}

.progress {
  margin-top: 6px;
}

@media (min-width: 992px) {
  .card-block {
    margin-left: 0;
    margin-right: 0;
  }
}
</style>
