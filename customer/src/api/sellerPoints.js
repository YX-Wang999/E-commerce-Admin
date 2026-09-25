import request from '@/utils/request'

export function getCheckoutSellerPoints(params) {
  return request.get('/customer/seller-points/checkout/', { params })
}
