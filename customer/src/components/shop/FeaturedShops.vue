<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getTenants } from '@/api/tenant'
import { resolveImageUrl } from '@/utils/product'

const router = useRouter()
const { t } = useI18n()

const tenants = ref([])
const loading = ref(true)

function goShop(tenant) {
  router.push({ name: 'ShopHome', params: { id: tenant.id } })
}

function goAllShops() {
  router.push({ name: 'ShopList' })
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await getTenants({ page_size: 20 })
    tenants.value = res.data?.results || res.data || []
  } catch {
    tenants.value = []
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section v-if="loading || tenants.length" class="featured-shops">
    <div class="section-head">
      <h3 class="section-title">{{ t('shop.featuredTitle') }}</h3>
      <button type="button" class="section-more" @click="goAllShops">
        {{ t('shop.viewAll') }}
      </button>
    </div>

    <van-loading v-if="loading" size="20px" class="shops-loading">
      {{ t('common.loading') }}
    </van-loading>

    <div v-else class="shop-scroll">
      <button
        v-for="item in tenants"
        :key="item.id"
        type="button"
        class="shop-card"
        @click="goShop(item)"
      >
        <van-image
          class="shop-logo"
          :src="resolveImageUrl(item.logo)"
          fit="cover"
          round
        >
          <template #error>
            <div class="logo-fallback">{{ item.name?.charAt(0) || '店' }}</div>
          </template>
        </van-image>
        <span class="shop-name">{{ item.name }}</span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.featured-shops {
  margin-top: 10px;
  padding: 16px;
  background: #fff;
  border-radius: 10px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #333;
}

.section-more {
  border: none;
  background: none;
  padding: 0;
  font-size: 13px;
  color: #969799;
  cursor: pointer;
}

.shops-loading {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

.shop-scroll {
  display: flex;
  gap: 14px;
  overflow-x: auto;
  padding-bottom: 4px;
  scrollbar-width: none;
}

.shop-scroll::-webkit-scrollbar {
  display: none;
}

.shop-card {
  flex: 0 0 auto;
  width: 72px;
  border: none;
  background: none;
  padding: 0;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.shop-logo {
  width: 56px;
  height: 56px;
  border: 1px solid #f0f0f0;
}

.logo-fallback {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #f5f6fa;
  color: #1989fa;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
}

.shop-name {
  width: 72px;
  font-size: 12px;
  color: #646566;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
