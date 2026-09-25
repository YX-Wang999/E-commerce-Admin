import request from '@/utils/request'

export function getOrderList(params) {
  return request.get('/seller/orders/', { params })
}

export function getOrderDetail(id) {
  return request.get(`/seller/orders/${id}/`)
}

export function shipOrder(id, data) {
  return request.post(`/seller/orders/${id}/ship/`, data)
}

export function cancelReviewOrder(id, data) {
  return request.post(`/seller/orders/${id}/cancel-review/`, data)
}

export function cancelOrder(id, data) {
  return request.post(`/seller/orders/${id}/cancel/`, data)
}

export function getExpressCompanies() {
  return request.get('/seller/express-companies/')
}
