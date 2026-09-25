import request from '@/utils/request'

export function getPointsMallItems(params) {
  return request.get('/admin/points-mall/items/', { params })
}

export function createPointsMallItem(data) {
  return request.post('/admin/points-mall/items/', data)
}

export function updatePointsMallItem(id, data) {
  return request.patch(`/admin/points-mall/items/${id}/`, data)
}

export function deletePointsMallItem(id) {
  return request.delete(`/admin/points-mall/items/${id}/`)
}

export function getPointsMallOrders(params) {
  return request.get('/admin/points-mall/orders/', { params })
}

export function getPointsMallOrder(id) {
  return request.get(`/admin/points-mall/orders/${id}/`)
}

export function shipPointsMallOrder(id, data) {
  return request.post(`/admin/points-mall/orders/${id}/ship/`, data)
}

export function getPointsMallStats() {
  return request.get('/admin/points-mall/stats/')
}
