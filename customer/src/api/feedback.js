import request from '@/utils/request'

export function getMyFeedbacks(params) {
  return request.get('/feedback/mine/', { params })
}

export function submitFeedback(data) {
  return request.post('/feedback/mine/', data)
}
