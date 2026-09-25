import request from '@/utils/request'

const notifyConfig = { skipErrorHandler: true }

export function getNotifications(params) {
  return request.get('/customers/notifications/', { params, ...notifyConfig })
}

export function getUnreadCount() {
  return request.get('/customers/notifications/unread-count/', notifyConfig)
}

export function markAsRead(id) {
  return request.post(`/customers/notifications/${id}/read/`, null, notifyConfig)
}

export function markAllRead() {
  return request.post('/customers/notifications/read-all/', null, notifyConfig)
}
