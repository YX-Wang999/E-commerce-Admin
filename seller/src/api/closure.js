import request from '@/utils/request'

export function getClosureConditions() {
  return request.get('/seller/closure/conditions/')
}

export function getClosureApplication() {
  return request.get('/seller/closure/application/')
}

export function submitClosureApplication(data) {
  return request.post('/seller/closure/application/', data)
}

export function cancelClosureApplication() {
  return request.delete('/seller/closure/application/')
}
