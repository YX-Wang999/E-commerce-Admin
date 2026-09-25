import request from '@/utils/request'

export function createOrder(data) {
  return request.post('/orders/', data)
}

export function getOrder(id) {
  return request.get(`/orders/${id}/`)
}

export function getOrders(params) {
  return request.get('/orders/', { params })
}

export function mockPayOrder(id) {
  return request.post(`/orders/${id}/mock-pay/`)
}

export function cancelOrder(id, data) {
  return request.post(`/orders/${id}/cancel/`, data)
}

export function applyCancelOrder(id, data) {
  return request.post(`/orders/${id}/cancel-apply/`, data)
}

export function confirmReceipt(id, data = {}) {
  return request.post(`/orders/${id}/confirm-receipt/`, data, {
    skipErrorHandler: true,
    timeout: 30000,
  })
}

export function getOrderSummary() {
  return request.get('/orders/mine-summary/', { skipErrorHandler: true })
}
