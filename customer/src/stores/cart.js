import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { addToCart, getCart, mergeCart, removeItem, toggleAll, toggleSelect, updateCartItem } from '@/api/cart'
import {
  addGuestCartItem,
  clearGuestCartRaw,
  guestCartPayloadForMerge,
  hasGuestCartItems,
  loadGuestCartRaw,
  removeGuestCartItem,
  saveGuestCartRaw,
  toggleGuestCartAll,
  updateGuestCartItem,
} from '@/utils/guestCart'
import { isLoggedIn } from '@/utils/auth'

export const useCartStore = defineStore('cart', () => {
  const items = ref([])
  const loading = ref(false)

  const count = computed(() =>
    items.value.reduce((sum, item) => sum + (item.quantity || 0), 0),
  )

  const selectedItems = computed(() =>
    items.value.filter((item) => item.selected),
  )

  const selectedCount = computed(() =>
    selectedItems.value.reduce((sum, item) => sum + (item.quantity || 0), 0),
  )

  const selectedTotal = computed(() =>
    selectedItems.value.reduce(
      (sum, item) => sum + Number(item.product_detail?.price || 0) * item.quantity,
      0,
    ),
  )

  function setItems(nextItems) {
    items.value = nextItems
  }

  function loadGuestCart() {
    items.value = loadGuestCartRaw()
  }

  async function fetchCart() {
    if (!isLoggedIn()) {
      loadGuestCart()
      return
    }
    loading.value = true
    try {
      const res = await getCart()
      items.value = res.data?.items || []
    } catch {
      loadGuestCart()
    } finally {
      loading.value = false
    }
  }

  async function mergeGuestCartToServer() {
    if (!isLoggedIn() || !hasGuestCartItems()) {
      return 0
    }
    const payload = guestCartPayloadForMerge()
    if (!payload.length) {
      return 0
    }
    const res = await mergeCart({ items: payload })
    clearGuestCartRaw()
    items.value = res.data?.items || []
    return res.data?.merged_count || payload.length
  }

  async function addItem(productId, quantity = 1, productDetail = null) {
    if (!isLoggedIn()) {
      if (!productDetail) {
        throw new Error('product detail required for guest cart')
      }
      items.value = addGuestCartItem(productDetail, quantity)
      return { data: { items: items.value } }
    }
    const res = await addToCart({ product_id: productId, quantity })
    items.value = res.data?.items || []
    return res
  }

  async function updateQuantity(itemId, quantity) {
    const item = items.value.find((entry) => entry.id === itemId)
    if (item?._guest || String(itemId).startsWith('guest-')) {
      items.value = updateGuestCartItem(itemId, { quantity })
      return { data: { items: items.value } }
    }
    const res = await updateCartItem({ item_id: itemId, quantity })
    items.value = res.data?.items || []
    return res
  }

  async function toggleItemSelect(itemId, selected) {
    const item = items.value.find((entry) => entry.id === itemId)
    if (item?._guest || String(itemId).startsWith('guest-')) {
      items.value = updateGuestCartItem(itemId, { selected })
      return { data: { items: items.value } }
    }
    const res = await toggleSelect({ item_id: itemId, selected })
    items.value = res.data?.items || []
    return res
  }

  async function toggleAllSelected(selected) {
    if (!isLoggedIn()) {
      items.value = toggleGuestCartAll(selected)
      return { data: { items: items.value } }
    }
    const res = await toggleAll({ selected })
    items.value = res.data?.items || []
    return res
  }

  async function removeCartItem(itemId) {
    const item = items.value.find((entry) => entry.id === itemId)
    if (item?._guest || String(itemId).startsWith('guest-')) {
      items.value = removeGuestCartItem(itemId)
      return { data: { items: items.value } }
    }
    const res = await removeItem({ item_id: itemId })
    items.value = res.data?.items || []
    return res
  }

  function reset() {
    if (isLoggedIn()) {
      items.value = []
      return
    }
    loadGuestCart()
  }

  function persistGuestSelection() {
    if (!isLoggedIn()) {
      saveGuestCartRaw(items.value)
    }
  }

  return {
    items,
    count,
    selectedItems,
    selectedCount,
    selectedTotal,
    loading,
    fetchCart,
    loadGuestCart,
    mergeGuestCartToServer,
    addItem,
    updateQuantity,
    toggleItemSelect,
    toggleAllSelected,
    removeCartItem,
    setItems,
    reset,
    persistGuestSelection,
  }
})
