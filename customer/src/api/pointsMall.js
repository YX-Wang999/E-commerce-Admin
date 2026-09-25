import request from '@/utils/request'

export function getPointsMallItems(params) {
  return request.get('/points-mall/items/', { params })
}

export function getPointsMallItem(id) {
  return request.get(`/points-mall/items/${id}/`)
}

export function exchangePointsMallItem(id, data) {
  return request.post(`/points-mall/items/${id}/exchange/`, data)
}

export function getPointsMallOrders(params) {
  return request.get('/points-mall/orders/', { params })
}

export function getPointsMallOrder(id) {
  return request.get(`/points-mall/orders/${id}/`)
}
