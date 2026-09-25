import request from '@/utils/request'

export function getSellerPointsOverview() {
  return request.get('/admin/seller-points/overview/')
}

export function getSellerPointsTransactions(params) {
  return request.get('/admin/seller-points/transactions/', { params })
}
