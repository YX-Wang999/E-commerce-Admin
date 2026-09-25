const GUEST_CART_KEY = 'customer_guest_cart'

function normalizeProductDetail(product) {
  return {
    id: product.id,
    name: product.name,
    price: product.price,
    stock: product.stock ?? 99,
    image: product.image || '',
    status: product.status || 'on_sale',
  }
}

export function loadGuestCartRaw() {
  try {
    const raw = localStorage.getItem(GUEST_CART_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function saveGuestCartRaw(items) {
  localStorage.setItem(GUEST_CART_KEY, JSON.stringify(items))
}

export function clearGuestCartRaw() {
  localStorage.removeItem(GUEST_CART_KEY)
}

export function buildGuestItem(product, quantity = 1) {
  const detail = normalizeProductDetail(product)
  return {
    id: `guest-${detail.id}`,
    product: detail.id,
    product_detail: detail,
    quantity,
    selected: true,
    _guest: true,
  }
}

export function addGuestCartItem(product, quantity = 1) {
  const items = loadGuestCartRaw()
  const productId = product.id
  const existing = items.find((item) => item.product === productId)
  if (existing) {
    existing.quantity += quantity
    const maxStock = existing.product_detail?.stock || 99
    if (existing.quantity > maxStock) {
      existing.quantity = maxStock
    }
  } else {
    items.push(buildGuestItem(product, quantity))
  }
  saveGuestCartRaw(items)
  return items
}

export function updateGuestCartItem(itemId, patch) {
  const items = loadGuestCartRaw()
  const index = items.findIndex((item) => item.id === itemId)
  if (index === -1) {
    return items
  }
  items[index] = { ...items[index], ...patch }
  if (items[index].quantity <= 0) {
    items.splice(index, 1)
  }
  saveGuestCartRaw(items)
  return items
}

export function removeGuestCartItem(itemId) {
  const items = loadGuestCartRaw().filter((item) => item.id !== itemId)
  saveGuestCartRaw(items)
  return items
}

export function toggleGuestCartAll(selected) {
  const items = loadGuestCartRaw().map((item) => ({ ...item, selected }))
  saveGuestCartRaw(items)
  return items
}

export function guestCartPayloadForMerge() {
  return loadGuestCartRaw().map((item) => ({
    product_id: item.product,
    quantity: item.quantity,
    selected: item.selected,
  }))
}

export function hasGuestCartItems() {
  return loadGuestCartRaw().length > 0
}
