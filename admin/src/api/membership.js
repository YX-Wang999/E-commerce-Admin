import request from '@/utils/request'

export function getMemberLevels(params) {
  return request.get('/admin/membership/levels/', { params })
}

export function createMemberLevel(data) {
  return request.post('/admin/membership/levels/', data)
}

export function updateMemberLevel(id, data) {
  return request.put(`/admin/membership/levels/${id}/`, data)
}

export function deleteMemberLevel(id) {
  return request.delete(`/admin/membership/levels/${id}/`)
}

export function getCustomerMembership(customerId) {
  return request.get(`/admin/membership/customers/${customerId}/`)
}
