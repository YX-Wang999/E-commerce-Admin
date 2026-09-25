import request from '@/utils/request'

export function getSubsidyPolicies(params) {
  return request.get('/admin/subsidy/policies/', { params })
}

export function createSubsidyPolicy(data) {
  return request.post('/admin/subsidy/policies/', data)
}

export function updateSubsidyPolicy(id, data) {
  return request.put(`/admin/subsidy/policies/${id}/`, data)
}

export function deleteSubsidyPolicy(id) {
  return request.delete(`/admin/subsidy/policies/${id}/`)
}

export function getSubsidyFilings(params) {
  return request.get('/admin/subsidy/filings/', { params })
}

export function syncSubsidyFiling(id, data) {
  return request.post(`/admin/subsidy/filings/${id}/sync-filing/`, data)
}

export function getSubsidyOrders(params) {
  return request.get('/admin/subsidy/orders/', { params })
}

export function reportSubsidyOrder(id) {
  return request.post(`/admin/subsidy/orders/${id}/report/`)
}

export function getSubsidyStats() {
  return request.get('/admin/subsidy/stats/')
}
