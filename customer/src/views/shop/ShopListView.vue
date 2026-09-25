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

onMounted(async () => {
  loading.value = true
  try {
    const res = await getTenants({ page_size: 50 })
    tenants.value = res.data?.results || res.data || []
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="shop-list-page">
    <van-nav-bar
      :title="t('shop.listTitle')"
      left-arrow
      fixed
      placeholder
      @click-left="router.back()"
    />

    <van-loading v-if="loading" class="page-loading" vertical>{{ t('common.loading') }}</van-loading>

    <van-empty v-else-if="!tenants.length" :description="t('shop.empty')" />

    <van-cell-group v-else inset class="shop-list">
      <van-cell
        v-for="item in tenants"
        :key="item.id"
        is-link
        @click="goShop(item)"
      >
        <template #icon>
          <van-image class="cell-logo" :src="resolveImageUrl(item.logo)" fit="cover" round>
            <template #error>
              <div class="logo-fallback">{{ item.name?.charAt(0) || '店' }}</div>
            </template>
          </van-image>
        </template>
        <template #title>
          <div class="cell-title">{{ item.name }}</div>
          <div class="cell-desc">{{ item.intro }}</div>
        </template>
        <template #value>
          <span class="cell-meta">{{ t('shop.productCount', { count: item.product_count ?? 0 }) }}</span>
        </template>
      </van-cell>
    </van-cell-group>
  </div>
</template>

<style scoped>
.shop-list-page {
  min-height: 100vh;
  background: #f5f6fa;
}

.page-loading {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.shop-list {
  margin-top: 12px;
}

.cell-logo {
  width: 44px;
  height: 44px;
  margin-right: 12px;
}

.logo-fallback {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #ecf5ff;
  color: #1989fa;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.cell-title {
  font-size: 15px;
  font-weight: 600;
}

.cell-desc {
  margin-top: 4px;
  font-size: 12px;
  color: #969799;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 220px;
}

.cell-meta {
  font-size: 12px;
  color: #969799;
}
</style>
