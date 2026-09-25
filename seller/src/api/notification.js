import request from '@/utils/request'

export function getNotifications(params) {
  return request.get('/seller/notifications/', { params })
}

export function getUnreadCount() {
  return request.get('/seller/notifications/unread-count/')
}

export function markAsRead(id) {
  return request.post(`/seller/notifications/${id}/read/`)
}

export function markAllRead() {
  return request.post('/seller/notifications/read-all/')
}
