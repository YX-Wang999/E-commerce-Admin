import request from '@/utils/request'

export function getMyCoupons(params = {}) {
  return request.get('/coupons/my-coupons/', { params })
}

export function getAvailableCoupons() {
  return request.get('/coupons/available/')
}

export function getPublishCoupons() {
  return request.get('/coupons/publish/')
}

export function receiveCoupon(couponId) {
  return request.post(`/coupons/${couponId}/receive/`)
}

export function getSeckillActivities() {
  return request.get('/seckill/activities/')
}

export function getSeckillProducts(params = {}) {
  return request.get('/seckill/products/', { params })
}

export function seckillBuy(activityId, data) {
  return request.post(`/seckill/${activityId}/buy/`, data)
}

export function getGroupBuyActivities(params = {}) {
  return request.get('/groupbuy/activities/', { params })
}

export function groupBuyJoin(activityId, data) {
  return request.post(`/groupbuy/${activityId}/join/`, data)
}

export function getSuperDiscountActive() {
  return request.get('/super-discount/active/')
}
