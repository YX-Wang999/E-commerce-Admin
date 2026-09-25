import request from '@/utils/request'

export function getLogisticsTrack(orderId, refresh = false) {
  return request.get(`/logistics/${orderId}/track/`, {
    params: refresh ? { refresh: 1 } : undefined,
  })
}
