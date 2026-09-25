import request from '@/utils/request'

export function getComplaintList(params) {
  return request.get('/complaints/', { params })
}

export function getComplaintDetail(id) {
  return request.get(`/complaints/${id}/`)
}

export function getComplaintStats() {
  return request.get('/complaints/stats/')
}

export function sendComplaintMessage(id, data) {
  return request.post(`/complaints/${id}/messages/`, data)
}

export function platformReviewComplaint(id, data) {
  return request.post(`/complaints/${id}/platform-review/`, data)
}

export function closeComplaint(id) {
  return request.post(`/complaints/${id}/close/`)
}
