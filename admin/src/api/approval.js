import request from '@/utils/request'

export function getApprovalSummary() {
  return request.get('/admin/approvals/summary/')
}

export function getApprovals(params) {
  return request.get('/admin/approvals/', { params })
}

export function getApprovalDetail(id) {
  return request.get(`/admin/approvals/${id}/`)
}

export function approveApproval(id, data = {}) {
  return request.post(`/admin/approvals/${id}/approve/`, data)
}

export function rejectApproval(id, data) {
  return request.post(`/admin/approvals/${id}/reject/`, data)
}

export function batchApproveApprovals(ids, data = {}) {
  return request.post('/admin/approvals/batch-approve/', { ids, ...data })
}
