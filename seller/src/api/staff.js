import request from '@/utils/request'

export function getStaffList() {
  return request.get('/seller/staff/')
}

export function createStaff(data) {
  return request.post('/seller/staff/create/', data)
}

export function deleteStaff(id) {
  return request.delete(`/seller/staff/${id}/`)
}
