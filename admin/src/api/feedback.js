import request from '@/utils/request'

export function getFeedbackList(params) {
  return request.get('/feedback/', { params })
}

export function getFeedbackDetail(id) {
  return request.get(`/feedback/${id}/`)
}

export function replyFeedback(id, data) {
  return request.post(`/feedback/${id}/reply/`, data)
}

export function deleteFeedback(id) {
  return request.delete(`/feedback/${id}/`)
}
