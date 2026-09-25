import request from '@/utils/request'

export function getTenants(params) {
  return request.get('/tenants/', { params })
}

export function getTenantSummary() {
  return request.get('/tenants/summary/')
}

export function getTenant(id) {
  return request.get(`/tenants/${id}/`)
}

export function createTenant(data) {
  return request.post('/tenants/', data)
}

export function updateTenant(id, data) {
  return request.put(`/tenants/${id}/`, data)
}

export function deleteTenant(id) {
  return request.delete(`/tenants/${id}/`)
}

export function approveTenant(id) {
  return request.post(`/tenants/${id}/approve/`)
}

export function suspendTenant(id, data) {
  return request.post(`/tenants/${id}/suspend/`, data)
}

export function resumeTenant(id, data) {
  return request.post(`/tenants/${id}/resume/`, data)
}

export function closeTenant(id, data) {
  return request.post(`/tenants/${id}/close/`, data)
}

export function getTenantStats(id) {
  return request.get(`/tenants/${id}/stats/`)
}

export function checkTenantField(data) {
  return request.post('/tenants/check/', data)
}
