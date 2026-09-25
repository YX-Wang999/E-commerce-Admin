import request from '@/utils/request'

export function getComplaintSummary() {
  return request.get('/seller/complaints/summary/', { skipErrorHandler: true })
}

export function getComplaintList(params) {
  return request.get('/seller/complaints/', { params })
}

export function getComplaintDetail(id) {
  return request.get(`/seller/complaints/${id}/`)
}

export function replyComplaint(id, data) {
  return request.post(`/seller/complaints/${id}/reply/`, data)
}
