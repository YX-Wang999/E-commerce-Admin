import request from '@/utils/request'

export function getComplaints(params) {
  return request.get('/complaints/', { params })
}

export function getComplaint(id) {
  return request.get(`/complaints/${id}/`)
}

export function createComplaint(data) {
  return request.post('/complaints/', data)
}

export function sendComplaintMessage(id, data) {
  return request.post(`/complaints/${id}/messages/`, data)
}

export function customerReviewComplaint(id, data) {
  return request.post(`/complaints/${id}/customer-review/`, data)
}

export function requestPlatformComplaint(id, data) {
  return request.post(`/complaints/${id}/request-platform/`, data)
}

export function uploadComplaintImage(file) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('scope', 'complaints')
  return request.post('/upload/image/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
