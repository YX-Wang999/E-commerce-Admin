const STORAGE_KEY = 'customer_search_history'
const MAX_HISTORY = 10

export function getSearchHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const list = raw ? JSON.parse(raw) : []
    return Array.isArray(list) ? list.filter((item) => typeof item === 'string' && item.trim()) : []
  } catch {
    return []
  }
}

export function addSearchHistory(keyword) {
  const trimmed = keyword?.trim()
  if (!trimmed) return getSearchHistory()

  const list = getSearchHistory().filter((item) => item !== trimmed)
  list.unshift(trimmed)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list.slice(0, MAX_HISTORY)))
  return getSearchHistory()
}

export function clearSearchHistory() {
  localStorage.removeItem(STORAGE_KEY)
}
