import request from '@/utils/request'

export function getProductList(params) {
  return request.get('/products/', { params })
}

export function getProductDetail(id) {
  return request.get(`/products/${id}/`)
}

export function createProduct(data) {
  return request.post('/products/', data)
}

export function updateProduct(id, data) {
  return request.put(`/products/${id}/`, data)
}

export function deleteProduct(id) {
  return request.delete(`/products/${id}/`)
}

export function onSaleProduct(id) {
  return request.post(`/products/${id}/on_sale/`)
}

export function offSaleProduct(id) {
  return request.post(`/products/${id}/off_sale/`)
}

export function getCategoryList(params) {
  return request.get('/products/categories/', { params })
}

export function getCategoryTree() {
  return request.get('/products/categories/tree/')
}

export function getCategoryFlat(params) {
  return request.get('/products/categories/flat/', { params })
}

export function createCategory(data) {
  return request.post('/products/categories/', data)
}

export function updateCategory(id, data) {
  return request.put(`/products/categories/${id}/`, data)
}

export function deleteCategory(id, params) {
  return request.delete(`/products/categories/${id}/`, { params })
}

export function batchSortCategories(items) {
  return request.post('/products/categories/batch-sort/', { items })
}

export function getBrandList(params) {
  return request.get('/products/brands/', { params })
}

export function getInventoryLogs(params) {
  return request.get('/products/inventory-logs/', { params })
}

export function createBrand(data) {
  return request.post('/products/brands/', data)
}

export function updateBrand(id, data) {
  return request.put(`/products/brands/${id}/`, data)
}

export function deleteBrand(id) {
  return request.delete(`/products/brands/${id}/`)
}
