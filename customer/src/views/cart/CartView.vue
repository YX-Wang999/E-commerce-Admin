<script setup>
import { computed, onMounted } from 'vue'
import { useMediaQuery } from '@vueuse/core'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showToast } from 'vant'
import { confirmDialog } from '@/utils/confirmDialog'
import { useCartStore } from '@/stores/cart'
import { requireLogin } from '@/stores/loginGate'
import { formatPrice, resolveImageUrl } from '@/utils/product'
import { getProductShopName } from '@/utils/shop'
import { navigateBack } from '@/utils/navigation'

const router = useRouter()
const { t } = useI18n()
const cartStore = useCartStore()
const isMobile = useMediaQuery('(max-width: 768px)')

const cartItems = computed(() => cartStore.items)

const allSelected = computed({
  get: () => cartItems.value.length > 0 && cartItems.value.every((item) => item.selected),
  set: (val) => handleToggleAll(val),
})

const selectedCount = computed(() => cartStore.selectedCount)

const totalPrice = computed(() => cartStore.selectedTotal.toFixed(2))

async function handleQuantityChange(itemId, value) {
  try {
    await cartStore.updateQuantity(itemId, value)
  } catch {
    await cartStore.fetchCart()
  }
}

async function handleToggle(itemId, selected) {
  try {
    await cartStore.toggleItemSelect(itemId, selected)
  } catch {
    await cartStore.fetchCart()
  }
}

async function handleToggleAll(selected) {
  try {
    await cartStore.toggleAllSelected(selected)
  } catch {
    await cartStore.fetchCart()
  }
}

async function handleRemove(itemId) {
  try {
    await confirmDialog({
      title: t('cart.removeConfirmTitle'),
      message: t('cart.removeConfirmMessage'),
    })
    await cartStore.removeCartItem(itemId)
    showToast(t('cart.removed'))
  } catch (error) {
    if (error !== 'cancel') {
      await cartStore.fetchCart()
    }
  }
}

async function handleCheckout() {
  if (selectedCount.value === 0) {
    showToast(t('cart.selectAtLeastOne'))
    return
  }
  try {
    await requireLogin({ redirect: '/checkout' })
    router.push({ name: 'Checkout' })
  } catch {
    // cancelled login
  }
}

function goHome() {
  router.push({ name: 'Home' })
}

function handleBack() {
  navigateBack(router)
}

function goToProduct(item) {
  const productId = item.product || item.product_detail?.id
  if (productId) {
    router.push({ name: 'ProductDetail', params: { id: productId } })
  }
}

onMounted(() => {
  cartStore.fetchCart()
})
</script>

<template>
  <div class="cart-page">
    <van-nav-bar
      v-if="isMobile"
      :title="t('header.cart')"
      left-arrow
      fixed
      placeholder
      safe-area-inset-top
      @click-left="handleBack"
    />

    <van-loading v-if="cartStore.loading" class="page-loading" vertical>
      {{ t('common.loading') }}
    </van-loading>

    <template v-else>
      <div v-if="cartItems.length > 0" class="cart-list">
        <van-swipe-cell
          v-for="item in cartItems"
          :key="item.id"
          class="cart-swipe-cell"
        >
          <div class="cart-item" @click="goToProduct(item)">
            <van-checkbox
              :model-value="item.selected"
              @update:model-value="handleToggle(item.id, $event)"
              @click.stop
            />
            <img
              :src="resolveImageUrl(item.product_detail?.image)"
              class="item-image"
              alt=""
            />
            <div class="item-info">
              <div class="item-name-row">
                <div class="item-name">{{ item.product_detail?.name }}</div>
                <button
                  type="button"
                  class="item-delete-btn"
                  :aria-label="t('cart.remove')"
                  @click.stop="handleRemove(item.id)"
                >
                  <van-icon name="delete-o" size="18" />
                </button>
              </div>
              <div v-if="getProductShopName(item.product_detail)" class="item-shop">
                🏪 {{ getProductShopName(item.product_detail) }}
              </div>
              <div class="item-bottom">
                <div class="item-price">{{ formatPrice(item.product_detail?.price) }}</div>
                <div class="item-stepper" @click.stop>
                  <van-stepper
                    :model-value="item.quantity"
                    min="1"
                    :max="item.product_detail?.stock || 99"
                    @update:model-value="handleQuantityChange(item.id, $event)"
                  />
                </div>
              </div>
            </div>
          </div>
          <template #right>
            <van-button
              square
              type="danger"
              class="delete-button"
              @click="handleRemove(item.id)"
            >
              {{ t('cart.remove') }}
            </van-button>
          </template>
        </van-swipe-cell>
      </div>

      <div v-else class="empty-cart">
        <van-icon name="shopping-cart-o" size="64" color="#ccc" />
        <p>{{ t('cart.empty') }}</p>
        <van-button type="primary" round @click="goHome">
          {{ t('cart.goShopping') }}
        </van-button>
      </div>

      <div v-if="cartItems.length > 0" class="cart-footer">
        <van-checkbox
          :model-value="allSelected"
          @update:model-value="handleToggleAll"
        >
          {{ t('cart.selectAll') }}
        </van-checkbox>
        <div class="cart-total">
          <span>{{ t('cart.total') }}</span>
          <span class="total-price">¥{{ totalPrice }}</span>
        </div>
        <van-button type="danger" round @click="handleCheckout">
          {{ t('cart.checkout', { count: selectedCount }) }}
        </van-button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.cart-page {
  min-height: calc(100vh - 200px);
  background: var(--color-bg, #f5f5f5);
  padding-bottom: calc(72px + env(safe-area-inset-bottom, 0px));
}

.page-loading {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

.cart-list {
  padding: 0 12px;
}

.cart-swipe-cell {
  margin-bottom: 8px;
  border-radius: 8px;
  overflow: hidden;
}

.cart-item {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  background: #fff;
  gap: 10px;
}

.item-image {
  width: 80px;
  height: 80px;
  border-radius: 4px;
  object-fit: cover;
  flex-shrink: 0;
  background: #f0f2f5;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-name-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.item-name {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  color: #333;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-shop {
  margin-top: 4px;
  font-size: 12px;
  color: #969799;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-delete-btn {
  flex-shrink: 0;
  border: none;
  background: none;
  padding: 2px;
  color: #969799;
  cursor: pointer;
}

.item-delete-btn:hover {
  color: #ee0a24;
}

.item-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
  gap: 8px;
}

.item-price {
  font-size: 16px;
  color: #ee0a24;
  font-weight: 600;
  flex-shrink: 0;
}

.item-stepper {
  flex-shrink: 0;
}

.delete-button {
  height: 100%;
  min-width: 72px;
}

.empty-cart {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: 100px;
  color: #999;
}

.empty-cart p {
  margin: 16px 0 24px;
  font-size: 16px;
}

.cart-footer {
  position: fixed;
  bottom: calc(50px + env(safe-area-inset-bottom, 0px));
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: var(--color-surface, #fff);
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.06);
  gap: 12px;
  z-index: 10;
}

@media (min-width: 769px) {
  .cart-footer {
    bottom: 0;
  }

  .cart-page {
    padding-bottom: 72px;
  }
}

.cart-total {
  flex: 1;
  font-size: 14px;
  color: #323233;
}

.total-price {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-primary, #ff4d4f);
}

.cart-footer .van-button {
  flex-shrink: 0;
  padding: 0 20px;
}
</style>

