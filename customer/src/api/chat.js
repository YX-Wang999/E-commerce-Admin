import request from '@/utils/request'

export function getMyConversation(params) {
  return request.get('/chat/conversations/mine/', { params })
}

export function listConversations(params) {
  return request.get('/chat/conversations/', { params })
}

export function openConversation(data) {
  return request.post('/chat/conversations/mine/', data)
}

export function startNewConversation(data) {
  return request.post('/chat/conversations/mine/', data)
}

export function transferToPlatform(conversationId) {
  return request.post(`/chat/conversations/${conversationId}/transfer-platform/`)
}

export function createComplaint(data) {
  return request.post('/chat/complaints/', data)
}

export function getConversationMessages(conversationId) {
  return request.get(`/chat/conversations/${conversationId}/messages/`)
}

export function sendConversationMessage(conversationId, data) {
  return request.post(`/chat/conversations/${conversationId}/messages/`, data)
}

export function closeConversation(conversationId) {
  return request.post(`/chat/conversations/${conversationId}/close/`)
}
