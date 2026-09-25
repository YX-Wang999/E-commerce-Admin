const STORAGE_KEY = 'customer_recent_products'
const MAX_ITEMS = 12

export function loadRecentProducts() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const list = raw ? JSON.parse(raw) : []
    return Array.isArray(list) ? list : []
  } catch {
    return []
  }
}

export function pushRecentProduct(product) {
  if (!product?.id) return
  const entry = {
    id: product.id,
    name: product.name || '',
    image: product.image || '',
    price: product.price ?? 0,
    viewed_at: Date.now(),
  }
  const list = loadRecentProducts().filter((item) => item.id !== entry.id)
  list.unshift(entry)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list.slice(0, MAX_ITEMS)))
}
