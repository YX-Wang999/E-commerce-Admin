import request from '@/utils/request'

export function getAuditLogList(params) {
  return request.get('/audit/logs/', { params })
}
