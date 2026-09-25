import { mergeMessages } from './utils.js'
import coreZh from './core/zh-CN.js'
import coreEn from './core/en-US.js'
import coreJa from './core/ja-JP.js'
import orderBusiness from './business/order.js'
import productBusiness from './business/product.js'
import authBusiness from './business/auth.js'

export const core = {
  'zh-CN': coreZh,
  'en-US': coreEn,
  'ja-JP': coreJa,
}

export const business = {
  order: orderBusiness,
  product: productBusiness,
  auth: authBusiness,
}

export function getSharedForLocale(locale) {
  return mergeMessages(
    core[locale] || {},
    orderBusiness[locale] || {},
    productBusiness[locale] || {},
    authBusiness[locale] || {},
  )
}
