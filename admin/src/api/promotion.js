import request from '@/utils/request'

export function getSeckillList(params) {
  return request.get('/promotions/seckills/', { params })
}

export function createSeckill(data) {
  return request.post('/promotions/seckills/', data)
}

export function updateSeckill(id, data) {
  return request.put(`/promotions/seckills/${id}/`, data)
}

export function deleteSeckill(id) {
  return request.delete(`/promotions/seckills/${id}/`)
}

export function submitSeckill(id) {
  return request.post(`/promotions/seckills/${id}/submit/`)
}

export function approveSeckill(id) {
  return request.post(`/promotions/seckills/${id}/approve/`)
}

export function rejectSeckill(id, data) {
  return request.post(`/promotions/seckills/${id}/reject/`, data)
}

export function cancelSeckill(id) {
  return request.post(`/promotions/seckills/${id}/cancel/`)
}

export function getGroupBuyList(params) {
  return request.get('/promotions/groupbuys/', { params })
}

export function createGroupBuy(data) {
  return request.post('/promotions/groupbuys/', data)
}

export function updateGroupBuy(id, data) {
  return request.put(`/promotions/groupbuys/${id}/`, data)
}

export function deleteGroupBuy(id) {
  return request.delete(`/promotions/groupbuys/${id}/`)
}

export function submitGroupBuy(id) {
  return request.post(`/promotions/groupbuys/${id}/submit/`)
}

export function approveGroupBuy(id) {
  return request.post(`/promotions/groupbuys/${id}/approve/`)
}

export function rejectGroupBuy(id, data) {
  return request.post(`/promotions/groupbuys/${id}/reject/`, data)
}

export function cancelGroupBuy(id) {
  return request.post(`/promotions/groupbuys/${id}/cancel/`)
}

export function getGroupOrders(activityId, params) {
  return request.get(`/promotions/groupbuys/${activityId}/group-orders/`, { params })
}

export function getCouponList(params) {
  return request.get('/promotions/coupons/', { params })
}

export function createCoupon(data) {
  return request.post('/promotions/coupons/', data)
}

export function updateCoupon(id, data) {
  return request.put(`/promotions/coupons/${id}/`, data)
}

export function deleteCoupon(id) {
  return request.delete(`/promotions/coupons/${id}/`)
}

export function publishCoupon(id) {
  return request.post(`/promotions/coupons/${id}/publish/`)
}

export function disableCoupon(id) {
  return request.post(`/promotions/coupons/${id}/disable/`)
}

export function getUserCouponList(params) {
  return request.get('/promotions/user-coupons/', { params })
}

export function getSuperDiscountList(params) {
  return request.get('/promotions/super-discounts/', { params })
}

export function createSuperDiscount(data) {
  return request.post('/promotions/super-discounts/', data)
}

export function updateSuperDiscount(id, data) {
  return request.put(`/promotions/super-discounts/${id}/`, data)
}

export function deleteSuperDiscount(id) {
  return request.delete(`/promotions/super-discounts/${id}/`)
}
