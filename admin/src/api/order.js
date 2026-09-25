import request from '@/utils/request'

export function getOrderList(params) {
  return request.get('/orders/', { params })
}

export function getOrderDetail(id) {
  return request.get(`/orders/${id}/`)
}

export function updateOrder(id, data) {
  return request.put(`/orders/${id}/`, data)
}

export function shipOrder(id, data) {
  return request.post(`/orders/${id}/ship/`, data)
}

export function getRefundList(params) {
  return request.get('/orders/refunds/', { params })
}

export function approveRefund(id) {
  return request.post(`/orders/refunds/${id}/approve/`)
}

export function rejectRefund(id) {
  return request.post(`/orders/refunds/${id}/reject/`)
}

export function exportOrders(params) {
  return request.get('/orders/export/', {
    params,
    responseType: 'blob',
  })
}

export function getOrderPendingSummary() {
  return request.get('/orders/pending-summary/', { skipErrorHandler: true })
}

export function forceCancelOrder(id, data) {
  return request.post(`/admin/orders/${id}/cancel/`, data)
}

export function reviewCancelOrder(id, data) {
  return request.post(`/admin/orders/${id}/cancel-review/`, data)
}

export function getCancelStats() {
  return request.get('/admin/orders/cancel-stats/')
}
