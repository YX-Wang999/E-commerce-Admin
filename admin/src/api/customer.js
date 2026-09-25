import request from '@/utils/request'

export function getCustomerList(params) {
  return request.get('/customers/', { params })
}

export function getCustomerDetail(id) {
  return request.get(`/customers/${id}/`)
}

export function createCustomer(data) {
  return request.post('/customers/', data)
}

export function updateCustomer(id, data) {
  return request.patch(`/customers/${id}/`, data)
}

export function deleteCustomer(id) {
  return request.delete(`/customers/${id}/`)
}
