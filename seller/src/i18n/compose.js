/** Compose seller locale messages from shared + domain modules. */

import { mergeMessages } from '../../../shared/i18n/utils.js'
import coreZh from '../../../shared/i18n/core/zh-CN.js'
import coreEn from '../../../shared/i18n/core/en-US.js'
import coreJa from '../../../shared/i18n/core/ja-JP.js'
import orderBusiness from '../../../shared/i18n/business/order.js'
import productBusiness from '../../../shared/i18n/business/product.js'
import authBusiness from '../../../shared/i18n/business/auth.js'

const CORES = {
  'zh-CN': coreZh,
  'en-US': coreEn,
  'ja-JP': coreJa,
}

export function composeSellerLocale(locale, domain) {
  return mergeMessages(
    CORES[locale],
    orderBusiness[locale],
    productBusiness[locale],
    authBusiness[locale],
    domain,
  )
}
