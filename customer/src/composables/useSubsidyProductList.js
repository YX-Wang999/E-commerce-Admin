import { onUnmounted, ref } from 'vue'
import { getSubsidyProducts } from '@/api/subsidy'

const PAGE_SIZE = 10

function isAbortError(err) {
  return err?.code === 'ERR_CANCELED' || err?.name === 'CanceledError'
}

function mapSubsidyRow(row) {
  return {
    id: row.product_id,
    name: row.name,
    image: row.image,
    price: row.final_price,
    original_price: row.price,
    subsidy_amount: row.subsidy_amount,
    is_subsidy: true,
    tenant_name: row.tenant_name,
  }
}

export function useSubsidyProductList() {
  const products = ref([])
  const loading = ref(false)
  const loadingMore = ref(false)
  const finished = ref(false)
  const error = ref(false)
  const page = ref(1)

  let abortController = null

  function abortPending() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
  }

  async function load(reset = false) {
    if (reset) {
      abortPending()
      page.value = 1
      finished.value = false
      products.value = []
      error.value = false
      loading.value = false
      loadingMore.value = false
    } else if (finished.value || loading.value || loadingMore.value) {
      return
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
      const res = await getSubsidyProducts({
        page: page.value,
        page_size: PAGE_SIZE,
        signal,
      })

      if (signal.aborted) return

      const { results = [], count = 0 } = res.data || {}
      const mapped = results.map(mapSubsidyRow)
      products.value = isFirstPage ? mapped : [...products.value, ...mapped]
      finished.value = products.value.length >= count || results.length < PAGE_SIZE
      if (!finished.value) {
        page.value += 1
      }
    } catch (err) {
      if (isAbortError(err)) return
      error.value = true
      finished.value = true
    } finally {
      loading.value = false
      loadingMore.value = false
    }
  }

  async function loadMore() {
    if (loading.value || loadingMore.value || finished.value || error.value) return
    await load(false)
  }

  function retry() {
    return load(true)
  }

  onUnmounted(abortPending)

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
