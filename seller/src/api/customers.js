import request from '@/utils/request'

export function getCustomerList(params) {
  return request.get('/seller/customers/', { params })
}

export function getCustomerDetail(id) {
  return request.get(`/seller/customers/${id}/`)
}
