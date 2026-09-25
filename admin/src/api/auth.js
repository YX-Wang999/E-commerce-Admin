import request from '@/utils/request'

export function getCaptchaTrust(params) {
  return request.get('/auth/captcha/trust/', { params })
}

export function getCaptcha() {
  return request.get('/auth/captcha/')
}

export function verifyCaptcha(data) {
  return request.post('/auth/captcha/verify/', data, { skipErrorHandler: true })
}

export function login(data) {
  return request.post('/auth/login/', data, { skipErrorHandler: true })
}

export function getProfile() {
  return request.get('/auth/profile/')
}

export function refreshToken(refresh) {
  return request.post('/auth/refresh/', { refresh })
}

export function changePassword(data) {
  return request.post('/auth/change-password/', data)
}

export function forgotPassword(data) {
  return request.post('/auth/forgot-password/', data, { skipErrorHandler: true })
}
