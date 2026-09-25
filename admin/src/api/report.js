import request from '@/utils/request'

export function getDashboardSummary() {
  return request.get('/reports/dashboard/')
}

export function getDashboardTodos() {
  return request.get('/dashboard/todos/')
}

export function getSalesReport() {
  return request.get('/reports/sales/')
}

export function getProductRank(params) {
  return request.get('/reports/product-rank/', { params })
}

export function getCustomerAnalysis() {
  return request.get('/reports/customer/')
}

export function getPromotionAnalysis() {
  return request.get('/reports/promotion/')
}

export function getFinanceSummary() {
  return request.get('/reports/finance/')
}
