import request from '@/utils/request'

export function getOrgChart() {
  return request.get('/org/chart/')
}
