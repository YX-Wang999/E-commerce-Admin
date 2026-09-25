import request from '@/utils/request'

export function getSeckillList(params) {
  return request.get('/seller/seckills/', { params })
}

export function createSeckill(data) {
  return request.post('/seller/seckills/', data)
}

export function updateSeckill(id, data) {
  return request.put(`/seller/seckills/${id}/`, data)
}

export function deleteSeckill(id) {
  return request.delete(`/seller/seckills/${id}/`)
}

export function submitSeckill(id) {
  return request.post(`/seller/seckills/${id}/submit/`)
}

export function cancelSeckill(id) {
  return request.post(`/seller/seckills/${id}/cancel/`)
}

export function getGroupBuyList(params) {
  return request.get('/seller/groupbuys/', { params })
}

export function createGroupBuy(data) {
  return request.post('/seller/groupbuys/', data)
}

export function updateGroupBuy(id, data) {
  return request.put(`/seller/groupbuys/${id}/`, data)
}

export function deleteGroupBuy(id) {
  return request.delete(`/seller/groupbuys/${id}/`)
}

export function submitGroupBuy(id) {
  return request.post(`/seller/groupbuys/${id}/submit/`)
}

export function cancelGroupBuy(id) {
  return request.post(`/seller/groupbuys/${id}/cancel/`)
}

export function getGroupOrders(activityId, params) {
  return request.get(`/seller/groupbuys/${activityId}/group-orders/`, { params })
}

export function getCouponList(params) {
  return request.get('/seller/coupons/', { params })
}

export function createCoupon(data) {
  return request.post('/seller/coupons/', data)
}

export function updateCoupon(id, data) {
  return request.put(`/seller/coupons/${id}/`, data)
}

export function deleteCoupon(id) {
  return request.delete(`/seller/coupons/${id}/`)
}

export function publishCoupon(id) {
  return request.post(`/seller/coupons/${id}/publish/`)
}

export function disableCoupon(id) {
  return request.post(`/seller/coupons/${id}/disable/`)
}
