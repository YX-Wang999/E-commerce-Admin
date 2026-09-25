import request from '@/utils/request'

export function getProductList(params) {
  return request.get('/seller/products/', { params })
}

export function getProductDetail(id) {
  return request.get(`/seller/products/${id}/`)
}

export function createProduct(data) {
  return request.post('/seller/products/', data)
}

export function updateProduct(id, data) {
  return request.put(`/seller/products/${id}/`, data)
}

export function toggleProduct(id, status) {
  return request.patch(`/seller/products/${id}/toggle/`, status ? { status } : {})
}

export function getCategoryList() {
  return request.get('/seller/categories/')
}

export function getBrandList() {
  return request.get('/seller/brands/')
}
