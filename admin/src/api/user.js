import request from '@/utils/request'

export function getUserList(params) {
  return request.get('/users/', { params })
}

export function getUserDetail(id) {
  return request.get(`/users/${id}/`)
}

export function createUser(data) {
  return request.post('/users/', data)
}

export function updateUser(id, data) {
  return request.put(`/users/${id}/`, data)
}

export function deleteUser(id) {
  return request.delete(`/users/${id}/`)
}

export function resetPassword(userId, data) {
  return request.post(`/users/${userId}/reset_password/`, data)
}

export function sendActivation(userId) {
  return request.post(`/users/${userId}/send_activation/`)
}

export function activateAccount(data) {
  return request.post('/users/activate/', data, { skipErrorHandler: true })
}
