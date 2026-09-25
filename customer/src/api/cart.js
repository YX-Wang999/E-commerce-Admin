import request from '@/utils/request'

export function getCart() {
  return request.get('/cart/my_cart/')
}

export function addToCart(data) {
  return request.post('/cart/add/', data)
}

export function updateCartItem(data) {
  return request.post('/cart/update/', data)
}

export function toggleSelect(data) {
  return request.post('/cart/toggle/', data)
}

export function toggleAll(data) {
  return request.post('/cart/toggle-all/', data)
}

export function removeItem(data) {
  return request.delete('/cart/remove/', { data })
}

export function clearCart() {
  return request.delete('/cart/clear/')
}

export function mergeCart(data) {
  return request.post('/cart/merge/', data)
}
