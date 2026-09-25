import request from '@/utils/request'

export function getPointsProfile() {
  return request.get('/points/profile/')
}

export function signInPoints() {
  return request.post('/points/sign-in/')
}

export function getMallPointsTransactions(params = {}) {
  return request.get('/points/mall/transactions/', { params })
}

export function getPublicPointsRules() {
  return request.get('/points/rules/public/')
}

export function getCheckoutPoints(params = {}) {
  return request.get('/points/checkout/', { params })
}
