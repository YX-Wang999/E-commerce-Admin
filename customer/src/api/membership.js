import request from '@/utils/request'

export function getMembershipProfile() {
  return request.get('/membership/my-profile/')
}

export function getMembershipLevels() {
  return request.get('/membership/levels/')
}

export function getGrowthLogs(params = {}) {
  return request.get('/membership/growth-logs/', { params })
}

export function membershipCheckin() {
  return request.post('/membership/checkin/')
}

export function membershipLevelUp() {
  return request.post('/membership/level-up/')
}
