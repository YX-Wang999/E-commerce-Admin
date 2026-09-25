import request from '@/utils/request'

export function getSettingList(params) {
  return request.get('/system/settings/', { params })
}

export function createSetting(data) {
  return request.post('/system/settings/', data)
}

export function updateSetting(id, data) {
  return request.put(`/system/settings/${id}/`, data)
}

export function deleteSetting(id) {
  return request.delete(`/system/settings/${id}/`)
}

export function getPublicSettings() {
  return request.get('/system/settings/public/', { skipErrorHandler: true })
}

export function getRoleDisplayNames() {
  return request.get('/system/settings/role-display-names/')
}

export function updateRoleDisplayNames(data) {
  return request.put('/system/settings/role-display-names/', data)
}
