import request from '@/utils/request'

export function submitAppeal(data) {
  return request.post('/seller/appeals/', data, { skipErrorHandler: true })
}

export function openAppealChat(data) {
  return request.post('/seller/appeals/chat/open/', data, { skipErrorHandler: true })
}

export function getAppealChatMessages(params) {
  return request.get('/seller/appeals/chat/messages/', { params, skipErrorHandler: true })
}

export function sendAppealChatMessage(data) {
  return request.post('/seller/appeals/chat/messages/', data, { skipErrorHandler: true })
}
