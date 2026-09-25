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

export function getChatStats() {
  return request.get('/chat/conversations/stats/')
}

export function updateChatPresence(online = true) {
  return request.post('/chat/conversations/presence/', { online })
}

export function getChatUnreadSummary() {
  return request.get('/chat/conversations/unread-summary/')
}

export function openConversationToTenant(tenantId) {
  return request.post('/chat/conversations/open/', { tenant_id: tenantId })
}
