import request from '@/utils/request'

export function getTenants(params) {
  return request.get('/tenants/', { params })
}

export function getTenant(id) {
  return request.get(`/tenants/${id}/`)
}

export function getTenantByCode(code) {
  return request.get('/tenants/', { params: { code } })
}
