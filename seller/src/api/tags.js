import request from '@/utils/request'

export function getSellerTags() {
  return request.get('/seller/tags/')
}

export function updateSellerTagConfig(data) {
  return request.post('/seller/tag-configs/', data)
}

export function getProductTagConfigs(params) {
  return request.get('/seller/product-tag-configs/', { params })
}

export function updateProductTagConfig(data) {
  return request.post('/seller/product-tag-configs/', data)
}

export function batchUpdateProductTags(productId, activeTagIds) {
  return request.post('/seller/product-tag-configs/', {
    product_id: productId,
    active_tag_ids: activeTagIds,
  })
}
