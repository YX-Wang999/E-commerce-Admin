<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getCategoryTree } from '@/api/product'

const router = useRouter()
const { t } = useI18n()
const categories = ref([])
const loading = ref(true)

function normalizeTopCategories(tree) {
  return [...tree]
    .filter((item) => item.is_active !== false)
    .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
    .slice(0, 9)
}

function categoryInitial(item) {
  return (item.name || '?').charAt(0)
}

function goCategory(item) {
  router.push({ name: 'Category', query: { catId: String(item.id) } })
}

function goCainiaoStation() {
  router.push({ name: 'OrderList' })
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await getCategoryTree({ active_only: true })
    categories.value = normalizeTopCategories(res.data || [])
  } catch {
    categories.value = []
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section class="category-grid card-block">
    <van-skeleton v-if="loading" :row="3" title />
    <div v-else class="grid">
      <button
        v-for="item in categories"
        :key="item.id"
        type="button"
        class="category-item"
        @click="goCategory(item)"
      >
        <span class="category-icon">{{ categoryInitial(item) }}</span>
        <span class="category-name">{{ item.name }}</span>
      </button>
      <button type="button" class="category-item" @click="goCainiaoStation">
        <span class="category-icon cainiao">
          <van-icon name="shop-o" size="22" color="#fff" />
        </span>
        <span class="category-name">{{ t('home.cainiaoStation') }}</span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.card-block {
  margin: 12px 12px 0;
  padding: 12px 8px;
  background: #fff;
  border-radius: 12px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px 4px;
}

.category-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
}

.category-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #e4393c;
}

.category-icon.cainiao {
  background: linear-gradient(135deg, #1677ff 0%, #69b1ff 100%);
}

.category-name {
  max-width: 100%;
  font-size: 12px;
  color: #666;
  line-height: 1.2;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (min-width: 992px) {
  .card-block {
    margin-left: 0;
    margin-right: 0;
  }
}
</style>
