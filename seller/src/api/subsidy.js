import request from '@/utils/request'

export function getSubsidyApplications(params) {
  return request.get('/seller/subsidy/products/', { params })
}

export function applySubsidy(data) {
  return request.post('/seller/subsidy/products/', data)
}

export function getAvailableSubsidyProducts(params) {
  return request.get('/seller/subsidy/available-products/', { params })
}

export function exportFilingMaterials(id) {
  return request.post(`/seller/subsidy/filings/${id}/export/`, null, { responseType: 'blob' }).then((res) => {
    const blob = new Blob([res.data], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `subsidy-filing-${id}.json`
    link.click()
    window.URL.revokeObjectURL(url)
  })
}

export function getSubsidyOrders(params) {
  return request.get('/seller/subsidy/orders/', { params })
}

export function updateSubsidyOrderCodes(id, data) {
  return request.put(`/seller/subsidy/orders/${id}/codes/`, data)
}
