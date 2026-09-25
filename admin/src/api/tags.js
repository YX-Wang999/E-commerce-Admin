import request from '@/utils/request'

export function getTags(params) {
  return request.get('/admin/tags/tags/', { params })
}

export function createTag(data) {
  return request.post('/admin/tags/tags/', data)
}

export function updateTag(id, data) {
  return request.put(`/admin/tags/tags/${id}/`, data)
}

export function getTenantTagConfigs(params) {
  return request.get('/admin/tags/tenant-tag-configs/', { params })
}

export function reviewTenantTagConfig(id, data) {
  return request.post(`/admin/tags/tenant-tag-configs/${id}/review/`, data)
}

export function getProductTagConfigs(params) {
  return request.get('/admin/tags/product-tag-configs/', { params })
}

export function updateProductTagConfig(data) {
  return request.post('/admin/tags/product-tag-configs/', data)
}

export function batchUpdateProductTags(productId, activeTagIds) {
  return request.post('/admin/tags/product-tag-configs/', {
    product_id: productId,
    active_tag_ids: activeTagIds,
  })
}
