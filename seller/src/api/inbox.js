import request from '@/utils/request'

export function getInboxSummary() {
  return request.get('/seller/inbox/summary/')
}

export function getInboxList() {
  return request.get('/seller/inbox/')
}

export function markInboxRead(id) {
  return request.post(`/seller/inbox/${id}/read/`)
}

export function markAllInboxRead() {
  return request.post('/seller/inbox/read-all/')
}

export function getMyAppeals() {
  return request.get('/seller/appeals/mine/')
}

export function getAppealDetail(id) {
  return request.get(`/seller/appeals/${id}/`)
}

export function replyAppeal(id, data) {
  return request.post(`/seller/appeals/${id}/reply/`, data)
}
