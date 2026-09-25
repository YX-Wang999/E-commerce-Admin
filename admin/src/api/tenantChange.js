import request from '@/utils/request'

export function getPendingChanges(params) {
  return request.get('/tenants/pending-changes/', { params })
}

export function getTenantChangeLogs(tenantId, params) {
  return request.get(`/tenants/${tenantId}/change-logs/`, { params })
}

export function reviewTenantChange(tenantId, logId, data) {
  return request.post(`/tenants/${tenantId}/change-logs/${logId}/review/`, data)
}
