import request from '@/utils/request'

export function getAppealList(params) {
  return request.get('/tenant-appeals/', { params })
}

export function getAppeal(id) {
  return request.get(`/tenant-appeals/${id}/`)
}

export function replyAppeal(id, data) {
  return request.post(`/tenant-appeals/${id}/reply/`, data)
}
