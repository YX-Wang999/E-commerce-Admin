import request from '@/utils/request'

export function getShopRatings(params) {
  return request.get('/admin/shop-ratings/', { params })
}

export function getShopRatingAlerts(params) {
  return request.get('/admin/shop-ratings/alerts/', { params })
}

export function getRatingAdjustments(params) {
  return request.get('/admin/shop-ratings/adjustment-requests/', { params })
}

export function reviewRatingAdjustment(id, data) {
  return request.post(`/admin/shop-ratings/adjustment-requests/${id}/review/`, data)
}
