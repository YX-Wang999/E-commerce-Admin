import request from '@/utils/request'

export function getPointsAccounts(params) {
  return request.get('/points/accounts/', { params })
}

export function getPointsTransactions(params) {
  return request.get('/points/transactions/', { params })
}

export function adjustPoints(data) {
  return request.post('/points/adjust/', data)
}

export function getPointsRules(params) {
  return request.get('/points/rules/', { params })
}

export function updatePointsRule(id, data) {
  return request.patch(`/points/rules/${id}/`, data)
}

export function createPointsRule(data) {
  return request.post('/points/rules/', data)
}

export function getPointsProfile(params) {
  return request.get('/points/profile/', { params })
}

export function signInPoints(data) {
  return request.post('/points/sign-in/', data)
}

export function getMallPointsTransactions(params) {
  return request.get('/points/mall/transactions/', { params })
}

export function getPublicPointsRules() {
  return request.get('/points/rules/public/')
}

export function submitProductReview(data) {
  return request.post('/reviews/submit/', data)
}
