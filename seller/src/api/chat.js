import request from '@/utils/request'

export function getChatConversations(params) {
  return request.get('/chat/conversations/', { params })
}

export function getConversationMessages(conversationId) {
  return request.get(`/chat/conversations/${conversationId}/messages/`)
}

export function assignConversation(conversationId) {
  return request.post(`/chat/conversations/${conversationId}/assign/`)
}

export function closeConversation(conversationId) {
  return request.post(`/chat/conversations/${conversationId}/close/`)
}

export function sendConversationMessage(conversationId, data) {
  return request.post(`/chat/conversations/${conversationId}/messages/`, data)
}

export function openPlatformChat() {
  return request.post('/chat/conversations/open/')
}

export function getChatUnreadSummary() {
  return request.get('/chat/conversations/unread-summary/')
}
