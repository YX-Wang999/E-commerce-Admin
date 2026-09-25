import request from '@/utils/request'

export function getSubsidyProducts(params = {}) {
  const { signal, ...rest } = params
  return request.get('/customer/subsidy/products/', { params: rest, signal })
}

export function getSubsidyEligibility(params) {
  return request.get('/customer/subsidy/eligibility/', { params })
}

export function calculateSubsidy(params) {
  return request.get('/customer/subsidy/calculate/', { params })
}
