import request from '@/utils/request'

export function getFeedbackSummary() {
  return request.get('/seller/feedbacks/summary/', { skipErrorHandler: true })
}

export function getFeedbackList(params) {
  return request.get('/seller/feedbacks/', { params })
}

export function getFeedbackDetail(id) {
  return request.get(`/seller/feedbacks/${id}/`)
}

export function replyFeedback(id, data) {
  return request.post(`/seller/feedbacks/${id}/reply/`, data)
}
