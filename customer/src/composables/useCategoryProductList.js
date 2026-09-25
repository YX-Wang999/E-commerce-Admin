import { onUnmounted, ref } from 'vue'
import { getProductsByCategory } from '@/api/product'

const PAGE_SIZE = 10

function isAbortError(err) {
  return err?.code === 'ERR_CANCELED' || err?.name === 'CanceledError'
}

export function useCategoryProductList(getExtraParams = () => ({})) {
  const products = ref([])
  const loading = ref(false)
  const loadingMore = ref(false)
  const finished = ref(false)
  const error = ref(false)
  const page = ref(1)

  let abortController = null
  let currentCategoryId = null

  function abortPending() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
  }

  async function load(categoryId, reset = false) {
    if (!categoryId) return

    if (reset) {
      abortPending()
      page.value = 1
      finished.value = false
      products.value = []
      error.value = false
      loading.value = false
      loadingMore.value = false
      currentCategoryId = categoryId
    } else {
      if (categoryId !== currentCategoryId) return
      if (finished.value || loading.value || loadingMore.value) return
    }

    const isFirstPage = page.value === 1
    if (isFirstPage) {
      loading.value = true
    } else {
      loadingMore.value = true
    }

    abortController = new AbortController()
    const { signal } = abortController

    try {
      const res = await getProductsByCategory(categoryId, {
        page: page.value,
        page_size: PAGE_SIZE,
        status: 'on_sale',
        ...getExtraParams(),
        signal,
      })

      if (signal.aborted || categoryId !== currentCategoryId) {
        return
      }

      const { results = [], count = 0 } = res.data || {}
      products.value = isFirstPage ? results : [...products.value, ...results]
      finished.value = products.value.length >= count || results.length < PAGE_SIZE
      if (!finished.value) {
        page.value += 1
      }
    } catch (err) {
      if (isAbortError(err) || categoryId !== currentCategoryId) {
        return
      }
      error.value = true
      finished.value = true
    } finally {
      if (categoryId === currentCategoryId) {
        loading.value = false
        loadingMore.value = false
      }
    }
  }

  async function loadMore(categoryId) {
    if (loading.value || loadingMore.value || finished.value || error.value) {
      return
    }
    await load(categoryId, false)
  }

  function retry(categoryId) {
    return load(categoryId, true)
  }

  onUnmounted(() => {
    abortPending()
  })

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
