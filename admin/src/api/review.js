import request from '@/utils/request'

export function getAdminReviews(params) {
  return request.get('/admin/reviews/', { params })
}

export function deleteAdminReview(id) {
  return request.delete(`/admin/reviews/${id}/`)
}
