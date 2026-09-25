import request from '@/utils/request'

export function login(data) {
  return request.post('/seller/auth/login/', data, { skipErrorHandler: true })
}

export function getProfile() {
  return request.get('/seller/auth/profile/')
}

export function updateTenantProfile(data) {
  return request.put('/seller/profile/', data)
}

export function closeShop(data) {
  return request.post('/seller/profile/close/', data)
}

export function applyTenant(data) {
  return request.post('/seller/apply/', data, { skipErrorHandler: true })
}

export function checkApplyField(data) {
  return request.post('/seller/apply/check/', data, { skipErrorHandler: true })
}
