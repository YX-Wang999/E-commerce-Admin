import request from '@/utils/request'

export function createReview(data) {
  return request.post('/reviews/', data)
}

export function getReviewUserCenter(params) {
  return request.get('/reviews/user/', { params })
}

export function getProductReviews(productId, params) {
  return request.get(`/reviews/product/${productId}/`, { params })
}

export function getReviewDetail(id) {
  return request.get(`/reviews/${id}/`)
}

export function likeReview(id) {
  return request.post(`/reviews/${id}/like/`)
}

export function commentReview(id, data) {
  return request.post(`/reviews/${id}/comment/`, data)
}

export function getReviewComments(id) {
  return request.get(`/reviews/${id}/comments/`)
}

export function incrementReviewView(id) {
  return request.post(`/reviews/${id}/view/`)
}

export function followUpReview(id, data) {
  return request.post(`/reviews/${id}/follow-up/`, data)
}

export function deleteReview(id) {
  return request.delete(`/reviews/${id}/`)
}

export function uploadReviewImage(file) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('scope', 'reviews')
  return request.post('/upload/image/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
