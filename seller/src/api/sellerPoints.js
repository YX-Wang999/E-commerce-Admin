import request from '@/utils/request'

export function getSellerPointsRule() {
  return request.get('/seller/points/rule/')
}

export function updateSellerPointsRule(data) {
  return request.put('/seller/points/rule/', data)
}

export function getSellerPointsAccounts(params) {
  return request.get('/seller/points/accounts/', { params })
}

export function getSellerPointsTransactions(params) {
  return request.get('/seller/points/transactions/', { params })
}

export function adjustSellerPoints(data) {
  return request.post('/seller/points/adjust/', data)
}
