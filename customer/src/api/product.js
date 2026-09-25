import request from '@/utils/request'

export function getProducts(params) {
  return request.get('/products/', { params })
}

export function getProduct(id) {
  return request.get(`/products/${id}/`)
}

export function getCategories(params) {
  return request.get('/products/categories/', { params })
}

/** 获取分类列表（后端暂无商品数量字段，接口预留） */
export function getCategoriesWithCount(params) {
  return request.get('/products/categories/', { params })
}

/** 按分类获取商品，后端筛选参数为 category */
export function getProductsByCategory(categoryId, params = {}) {
  const { signal, include_children = true, ...rest } = params
  return request.get('/products/', {
    params: {
      category: categoryId,
      include_children,
      status: 'on_sale',
      ...rest,
    },
    signal,
  })
}

export function getCategoryTree(params) {
  return request.get('/products/categories/tree/', { params })
}

export function getCategoryFlat(params) {
  return request.get('/products/categories/flat/', { params: { active_only: true, ...params } })
}

export function getBanners() {
  return request.get('/announcements/banners/', { skipErrorHandler: true }).catch(() => ({ data: [] }))
}

export function searchProducts(keyword, params = {}) {
  return request.get('/products/', {
    params: {
      keyword,
      status: 'on_sale',
      ...params,
    },
  })
}

export function getNewProducts(params = {}) {
  return request.get('/products/', {
    params: {
      status: 'on_sale',
      is_new: true,
      ...params,
    },
  })
}
