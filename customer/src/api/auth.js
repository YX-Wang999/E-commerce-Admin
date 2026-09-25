import request from '@/utils/request'

/** 发送短信验证码 → POST /api/customers/auth/send-sms/（别名 /api/send-sms/） */
export function sendSms(data) {
  return request.post('/customers/auth/send-sms/', data, { skipErrorHandler: true })
}

export function login(data) {
  return request.post('/customers/auth/login/', data, { skipErrorHandler: true })
}

export function register(data) {
  return request.post('/customers/auth/register/', data, { skipErrorHandler: true })
}

export function resetPassword(data) {
  return request.post('/customers/auth/reset-password/', data, { skipErrorHandler: true })
}

export function getProfile() {
  return request.get('/customers/auth/profile/')
}

export function updateProfile(data) {
  return request.patch('/customers/auth/profile/', data)
}

export function refreshToken(data) {
  return request.post('/customers/auth/refresh/', data)
}
