import request from '@/utils/request'

export function getShopRating() {
  return request.get('/seller/shop-rating/')
}

export function getShopRatingReviews() {
  return request.get('/seller/shop-rating/reviews/')
}

export function getRatingAdjustments() {
  return request.get('/seller/shop-rating/adjustment-requests/')
}

export function applyRatingAdjustment(data) {
  return request.post('/seller/shop-rating/adjustment-requests/', data)
}
