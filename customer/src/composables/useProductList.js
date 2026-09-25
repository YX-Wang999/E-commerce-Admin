import { ref } from 'vue'
import { getProducts } from '@/api/product'

const PAGE_SIZE = 10

export function useProductList(getExtraParams = () => ({})) {
  const products = ref([])
  const loading = ref(false)
  const loadingMore = ref(false)
  const finished = ref(false)
  const error = ref(false)
  const page = ref(1)

  async function load(reset = false) {
    if (reset) {
      page.value = 1
      finished.value = false
      products.value = []
      error.value = false
    }

    if (finished.value) return

    const isFirstPage = page.value === 1
    if (isFirstPage) {
      loading.value = true
    } else {
      loadingMore.value = true
    }

    try {
      const res = await getProducts({
        page: page.value,
        page_size: PAGE_SIZE,
        status: 'on_sale',
        ...getExtraParams(),
      })
      const { results = [], count = 0 } = res.data || {}
      products.value = isFirstPage ? results : [...products.value, ...results]
      finished.value = products.value.length >= count || results.length < PAGE_SIZE
      if (!finished.value) {
        page.value += 1
      }
    } catch {
      error.value = true
      finished.value = true
    } finally {
      loading.value = false
      loadingMore.value = false
    }
  }

  async function loadMore() {
    if (loading.value || loadingMore.value || finished.value || error.value) {
      return
    }
    await load(false)
  }

  function retry() {
    return load(true)
  }

  return {
    products,
    loading,
    loadingMore,
    finished,
    error,
    load,
    loadMore,
    retry,
  }
}
