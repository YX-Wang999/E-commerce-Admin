import request from '@/utils/request'

export function getExpressCompanies() {
  return request.get('/logistics/express-companies/')
}

export function getLogisticsTrack(orderId, refresh = false) {
  return request.get(`/logistics/${orderId}/track/`, {
    params: refresh ? { refresh: 1 } : undefined,
  })
}
