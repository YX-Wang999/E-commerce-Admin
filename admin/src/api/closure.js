import request from '@/utils/request'

export function getClosureApplications(params) {
  return request.get('/admin/closures/', { params })
}

export function getClosureDetail(id) {
  return request.get(`/admin/closures/${id}/`)
}

export function approveClosure(id, data) {
  return request.post(`/admin/closures/${id}/approve/`, data)
}

export function rejectClosure(id, data) {
  return request.post(`/admin/closures/${id}/reject/`, data)
}

export function completeClosure(id) {
  return request.post(`/admin/closures/${id}/complete/`)
}

export function exportClosures() {
  return request.get('/admin/closures/export/', { responseType: 'blob', skipErrorHandler: true })
}
